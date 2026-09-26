"""Сколько модель занимает и как быстро отвечает — в трёх режимах (B.9).

Запуск:  python bench_llm.py

Меряем то, что важно для продукта: пиковую видеопамять и время ответа на реальном промпте
из тестового набора. Режимы:
    merged fp16   — слитая модель, как её грузит сервис по LLM_MODEL_PATH
    adapter fp16  — база плюс адаптер LoRA (LLM_ADAPTER_PATH), репозиторий остаётся лёгким
    merged 4bit   — то же в 4 битах (LLM_LOAD_4BIT=1), режим для слабой видеокарты
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "backend"))

MERGED = ROOT / "runs" / "dotyanu_llm_merged"
ADAPTER = ROOT / "runs" / "dotyanu_llm"
BASE = "Vikhrmodels/Vikhr-Qwen-2.5-1.5B-Instruct"
N_PROMPTS = 6
MAX_NEW_TOKENS = 110


def prompts() -> list[list[dict]]:
    rows = [json.loads(line) for line in
            (ROOT / "data" / "chat_sft_test.jsonl").read_text(encoding="utf-8").splitlines()
            if line.strip()]
    return [row["messages"][:2] for row in rows[:N_PROMPTS]]


def four_bit() -> BitsAndBytesConfig:
    return BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                              bnb_4bit_use_double_quant=True,
                              bnb_4bit_compute_dtype=torch.float16)


def load(mode: str):
    if mode == "merged fp16":
        tokenizer = AutoTokenizer.from_pretrained(str(MERGED))
        model = AutoModelForCausalLM.from_pretrained(str(MERGED), dtype=torch.float16).to("cuda")
    elif mode == "adapter fp16":
        from peft import PeftModel

        tokenizer = AutoTokenizer.from_pretrained(str(ADAPTER))
        model = AutoModelForCausalLM.from_pretrained(BASE, dtype=torch.float16).to("cuda")
        model = PeftModel.from_pretrained(model, str(ADAPTER))
    else:
        tokenizer = AutoTokenizer.from_pretrained(str(MERGED))
        model = AutoModelForCausalLM.from_pretrained(
            str(MERGED), dtype=torch.float16, device_map={"": 0},
            quantization_config=four_bit())
    model.eval()
    return model, tokenizer


def measure(mode: str) -> dict:
    torch.cuda.empty_cache()
    torch.cuda.reset_peak_memory_stats()
    model, tokenizer = load(mode)
    chats = prompts()

    # первый прогон прогревает ядра — его в среднее не берём
    warm = tokenizer(tokenizer.apply_chat_template(chats[0], tokenize=False,
                                                   add_generation_prompt=True),
                     return_tensors="pt").to(model.device)
    with torch.inference_mode():
        model.generate(**warm, max_new_tokens=16, do_sample=False,
                       pad_token_id=tokenizer.pad_token_id or tokenizer.eos_token_id)

    seconds, tokens = 0.0, 0
    for chat in chats:
        text = tokenizer.apply_chat_template(chat, tokenize=False, add_generation_prompt=True)
        inputs = tokenizer(text, return_tensors="pt").to(model.device)
        started = time.time()
        with torch.inference_mode():
            output = model.generate(**inputs, max_new_tokens=MAX_NEW_TOKENS, do_sample=False,
                                    repetition_penalty=1.05,
                                    pad_token_id=tokenizer.pad_token_id or tokenizer.eos_token_id)
        seconds += time.time() - started
        tokens += output.shape[1] - inputs["input_ids"].shape[1]

    result = {
        "режим": mode,
        "видеопамять_пик_ГБ": round(torch.cuda.max_memory_allocated() / 2**30, 2),
        "секунд_на_ответ": round(seconds / len(chats), 2),
        "токенов_в_секунду": round(tokens / seconds, 1),
    }
    del model
    torch.cuda.empty_cache()
    return result


def main() -> None:
    if not torch.cuda.is_available():
        raise SystemExit("нужна видеокарта")
    print(torch.cuda.get_device_name(0))
    results = []
    for mode in ("merged fp16", "adapter fp16", "merged 4bit"):
        try:
            results.append(measure(mode))
            print(json.dumps(results[-1], ensure_ascii=False))
        except Exception as error:  # noqa: BLE001 — режим может не завестись, это тоже результат
            print(f"{mode}: не заработал — {error}")
    path = ROOT / "reports" / "llm_bench.json"
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print("сохранено:", path)


if __name__ == "__main__":
    main()
