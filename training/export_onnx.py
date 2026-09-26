"""Экспорт нейросети в ONNX + int8 (B.4): torch.onnx.export → quantize_dynamic.

Запуск:  python export_onnx.py
Пишет:   ../backend/app/ai/models/rubert_intent/{model.onnx, tokenizer.json, labels.json}

Сверяет предсказания torch и onnx на 20 фразах из test (B.10: токенизатор должен давать те же id).
Цель по размеру — не больше 40 МБ.
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

import numpy as np
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "backend"))
from app.ai.nlu.labels import LABELS  # noqa: E402
from app.ai.parse import normalize  # noqa: E402

CHECKPOINT = ROOT / "runs" / "rubert_intent"
OUT_DIR = ROOT.parent / "backend" / "app" / "ai" / "models" / "rubert_intent"
DATA_DIR = ROOT / "data"
MAX_LENGTH = 64
SIZE_LIMIT_MB = 40


def export(model, tokenizer, path: Path) -> None:
    sample = tokenizer("могу купить наушники за 3000", return_tensors="pt",
                       truncation=True, max_length=MAX_LENGTH)
    inputs = ("input_ids", "attention_mask", "token_type_ids")
    args = tuple(sample[name] for name in inputs if name in sample)
    names = [name for name in inputs if name in sample]
    options = dict(
        input_names=names, output_names=["logits"],
        dynamic_axes={name: {0: "batch", 1: "sequence"} for name in names}
                     | {"logits": {0: "batch"}},
        opset_version=14, do_constant_folding=True,
    )
    try:
        # Старый экспортёр даёт граф, который квантизация переваривает без правок
        torch.onnx.export(model, args, str(path), dynamo=False, **options)
    except TypeError:
        torch.onnx.export(model, args, str(path), **options)


def inline_weights(path: Path) -> Path:
    """Собрать веса обратно в один файл.

    Новый экспортёр torch выносит большие веса в соседний .data; после квантизации ссылка
    на него ломается, поэтому перед квантизацией всё складываем внутрь самого .onnx.
    """
    import onnx

    model = onnx.load(str(path), load_external_data=True)
    target = path.with_name("model_inline.onnx")
    onnx.save(model, str(target), save_as_external_data=False)
    return target


def quantize(source: Path, target: Path) -> None:
    """int8 по весам. Если граф не проходит вывод форм, сначала прогоняем предобработку."""
    from onnxruntime.quantization import QuantType, quantize_dynamic

    try:
        quantize_dynamic(str(source), str(target), weight_type=QuantType.QInt8)
        return
    except Exception as error:  # noqa: BLE001
        print(f"квантизация без предобработки не прошла ({error}); пробую quant_pre_process")

    from onnxruntime.quantization.shape_inference import quant_pre_process

    prepared = source.with_name("model_prepared.onnx")
    quant_pre_process(str(source), str(prepared), skip_symbolic_shape=True)
    quantize_dynamic(str(prepared), str(target), weight_type=QuantType.QInt8)


def compare(model, tokenizer, onnx_path: Path, sample_size: int = 20) -> int:
    """Сколько из sample_size фраз torch и onnx поняли одинаково."""
    import onnxruntime

    rows = [json.loads(line) for line in open(DATA_DIR / "intents_test.jsonl", encoding="utf-8")]
    texts = [normalize(r["text"]) for r in rows[:sample_size]]
    session = onnxruntime.InferenceSession(str(onnx_path), providers=["CPUExecutionProvider"])
    input_names = {i.name for i in session.get_inputs()}

    same = 0
    model.eval()
    for text in texts:
        encoded = tokenizer(text, return_tensors="pt", truncation=True, max_length=MAX_LENGTH)
        with torch.no_grad():
            torch_label = int(model(**encoded).logits.argmax(dim=-1))
        feed = {name: encoded[name].numpy().astype(np.int64)
                for name in input_names if name in encoded}
        onnx_label = int(np.argmax(session.run(None, feed)[0][0]))
        same += int(torch_label == onnx_label)
    return same


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    if not (CHECKPOINT / "config.json").exists():
        raise SystemExit(f"нет чекпоинта {CHECKPOINT} — сначала запусти train_rubert.py")

    tokenizer = AutoTokenizer.from_pretrained(CHECKPOINT)
    model = AutoModelForSequenceClassification.from_pretrained(CHECKPOINT)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    for stale in OUT_DIR.glob("model*.onnx*"):  # чтобы не осталось ссылок на прошлый экспорт
        stale.unlink()

    with tempfile.TemporaryDirectory() as temp:
        raw = Path(temp) / "model_fp32.onnx"
        export(model, tokenizer, raw)
        raw = inline_weights(raw)
        raw_mb = raw.stat().st_size / 1024 / 1024
        target = OUT_DIR / "model.onnx"
        try:
            quantize(raw, target)
        except Exception as error:  # noqa: BLE001 — без квантизации тоже поедет, просто крупнее
            print(f"квантизация не удалась ({error}) — кладу fp32")
            shutil.copy(raw, target)
        print(f"onnx fp32: {raw_mb:.1f} МБ → int8: {target.stat().st_size / 1024 / 1024:.1f} МБ")

    tokenizer.backend_tokenizer.save(str(OUT_DIR / "tokenizer.json"))
    (OUT_DIR / "labels.json").write_text(
        json.dumps(list(LABELS), ensure_ascii=False, indent=2), encoding="utf-8")

    same = compare(model, tokenizer, OUT_DIR / "model.onnx")
    size_mb = sum(p.stat().st_size for p in OUT_DIR.iterdir()) / 1024 / 1024
    print(f"torch и onnx совпали на {same} из 20 фраз")
    print(f"итоговый размер {OUT_DIR.name}: {size_mb:.1f} МБ "
          f"({'в пределах' if size_mb <= SIZE_LIMIT_MB else 'БОЛЬШЕ'} цели {SIZE_LIMIT_MB} МБ)")
    if same < 20:
        print("ВНИМАНИЕ: предсказания расходятся — проверь токенизатор (B.10)")


if __name__ == "__main__":
    main()
