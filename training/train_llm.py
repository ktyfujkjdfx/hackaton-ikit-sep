"""Дообучение генеративного пояснителя (шаг 3 роли B): QLoRA на своей видеокарте.

Запуск (окружение .venv-llm, нужна CUDA-видеокарта от 8 ГБ):
    python train_llm.py --epochs 2 --max-hours 4

Что делает:
  * берёт базовую русскоязычную модель (по умолчанию Vikhr-Qwen-2.5-1.5B-Instruct);
  * грузит её в 4 битах (nf4) — на 8 ГБ это ~1,3 ГБ весов, остальное уходит на активации;
  * учит только адаптер LoRA: база не меняется, поэтому русский язык модель не забывает;
  * учится ТОЛЬКО на ответе ассистента — промпт с фактами в лосс не входит;
  * держит бюджет времени: по --max-hours обучение аккуратно останавливается и сохраняется.

Результат: training/runs/dotyanu_llm/ — адаптер LoRA плюс токенизатор.
Дальше: merge_llm.py (слить в обычные веса для прода) и eval_llm.py (метрики).
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import torch
from datasets import Dataset
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, TrainerCallback
from trl import SFTConfig, SFTTrainer

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
DEFAULT_BASE = "Vikhrmodels/Vikhr-Qwen-2.5-1.5B-Instruct"
DEFAULT_OUT = ROOT / "runs" / "dotyanu_llm"


def load_split(name: str) -> Dataset:
    """jsonl из gen_chat_dataset.py → формат prompt/completion (лосс только на ответе)."""
    rows = []
    for line in (DATA_DIR / name).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        item = json.loads(line)
        messages = item["messages"]
        rows.append({"prompt": messages[:-1], "completion": messages[-1:]})
    return Dataset.from_list(rows)


class TimeBudget(TrainerCallback):
    """Стоп по бюджету времени: лучше готовый адаптер, чем прерванное обучение."""

    def __init__(self, max_hours: float) -> None:
        self.limit = max_hours * 3600
        self.started = time.time()

    def on_step_end(self, args, state, control, **kwargs):  # noqa: ANN001, D102
        if time.time() - self.started > self.limit:
            print(f"\nбюджет времени {self.limit / 3600:.1f} ч исчерпан — останавливаюсь и сохраняюсь")
            control.should_training_stop = True
        return control


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default=DEFAULT_BASE, help="базовая модель с Hugging Face")
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    parser.add_argument("--epochs", type=float, default=2.0)
    parser.add_argument("--max-hours", type=float, default=4.0, help="бюджет времени обучения")
    parser.add_argument("--batch", type=int, default=2, help="примеров за шаг на видеокарте")
    parser.add_argument("--accum", type=int, default=8, help="шагов накопления градиента")
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--max-length", type=int, default=768)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    if not torch.cuda.is_available():
        raise SystemExit("нужна видеокарта с CUDA: на процессоре это обучение не закончится за ночь")
    print("видеокарта:", torch.cuda.get_device_name(0),
          f"{torch.cuda.get_device_properties(0).total_memory / 2**30:.1f} ГБ")

    train_ds, eval_ds = load_split("chat_sft_train.jsonl"), load_split("chat_sft_test.jsonl")
    print(f"train {len(train_ds)} · test {len(eval_ds)}")

    tokenizer = AutoTokenizer.from_pretrained(args.base)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # 4 бита nf4 + fp16: Turing (RTX 20xx) не умеет bf16 по-настоящему, поэтому именно fp16.
    quantization = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=torch.float16,
    )
    model = AutoModelForCausalLM.from_pretrained(
        args.base, quantization_config=quantization, dtype=torch.float16, device_map={"": 0},
    )
    model.config.use_cache = False

    peft_config = LoraConfig(
        r=32, lora_alpha=64, lora_dropout=0.05, bias="none", task_type="CAUSAL_LM",
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                        "gate_proj", "up_proj", "down_proj"],
    )
    model = prepare_model_for_kbit_training(model, use_gradient_checkpointing=True)
    model = get_peft_model(model, peft_config)
    model.print_trainable_parameters()

    config = SFTConfig(
        output_dir=args.out,
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch,
        per_device_eval_batch_size=args.batch,
        gradient_accumulation_steps=args.accum,
        gradient_checkpointing=True,
        gradient_checkpointing_kwargs={"use_reentrant": False},
        learning_rate=args.lr,
        lr_scheduler_type="cosine",
        warmup_ratio=0.03,
        logging_steps=10,
        eval_strategy="steps",
        eval_steps=100,
        save_strategy="steps",
        save_steps=100,
        save_total_limit=2,
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        max_length=args.max_length,
        packing=False,
        fp16=True,
        optim="paged_adamw_8bit",
        report_to=[],
        seed=args.seed,
        dataloader_num_workers=0,
        disable_tqdm=True,
    )

    trainer = SFTTrainer(
        model=model,
        args=config,
        train_dataset=train_ds,
        eval_dataset=eval_ds,
        processing_class=tokenizer,
        callbacks=[TimeBudget(args.max_hours)],
    )
    # После сборки тренера: TRL кладёт адаптер в bfloat16, а fp16-скейлер на Turing
    # с bfloat16-градиентами не работает. Обучаемые веса держим в fp32.
    for parameter in trainer.model.parameters():
        if parameter.requires_grad and parameter.dtype != torch.float32:
            parameter.data = parameter.data.to(torch.float32)

    trainer.train()

    out = Path(args.out)
    trainer.save_model(str(out))
    tokenizer.save_pretrained(out)
    metrics = trainer.evaluate()
    (out / "train_meta.json").write_text(json.dumps({
        "base_model": args.base,
        "epochs": args.epochs,
        "train_size": len(train_ds),
        "eval_size": len(eval_ds),
        "eval_loss": metrics.get("eval_loss"),
        "lora": {"r": peft_config.r, "alpha": peft_config.lora_alpha},
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print("готово:", out, "eval_loss", metrics.get("eval_loss"))


if __name__ == "__main__":
    main()
