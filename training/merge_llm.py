"""Слить адаптер LoRA с базовой моделью — одна папка, которую грузит сервис.

Запуск:  python merge_llm.py                       # runs/dotyanu_llm → runs/dotyanu_llm_merged
         python merge_llm.py --dtype float16       # 1,5B ≈ 3,1 ГБ на диске

Зачем: в проде не нужен peft и не нужно тянуть базовую модель с Hugging Face — достаточно
указать LLM_MODEL_PATH на готовую папку. Веса в git НЕ кладём (они гигабайтные).
"""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

ROOT = Path(__file__).resolve().parent
DEFAULT_ADAPTER = ROOT / "runs" / "dotyanu_llm"
DEFAULT_OUT = ROOT / "runs" / "dotyanu_llm_merged"
DEFAULT_BASE = "Vikhrmodels/Vikhr-Qwen-2.5-1.5B-Instruct"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--adapter", default=str(DEFAULT_ADAPTER))
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    parser.add_argument("--base", default="", help="по умолчанию берётся из adapter_config.json")
    parser.add_argument("--dtype", default="float16", choices=["float16", "float32"])
    args = parser.parse_args()

    adapter = Path(args.adapter)
    if not (adapter / "adapter_config.json").exists():
        raise SystemExit(f"нет адаптера в {adapter} — сначала train_llm.py")

    import json

    base = args.base or json.loads(
        (adapter / "adapter_config.json").read_text(encoding="utf-8")
    ).get("base_model_name_or_path") or DEFAULT_BASE
    dtype = torch.float16 if args.dtype == "float16" else torch.float32

    print(f"база: {base}\nадаптер: {adapter}")
    model = AutoModelForCausalLM.from_pretrained(base, dtype=dtype, device_map="cpu")
    model = PeftModel.from_pretrained(model, str(adapter))
    model = model.merge_and_unload()

    out = Path(args.out)
    if out.exists():
        shutil.rmtree(out)
    model.save_pretrained(out, safe_serialization=True)
    AutoTokenizer.from_pretrained(str(adapter)).save_pretrained(out)

    size = sum(f.stat().st_size for f in out.rglob("*") if f.is_file()) / 2**30
    print(f"готово: {out} ({size:.1f} ГБ)\nв .env: LLM_MODEL_PATH={out}")


if __name__ == "__main__":
    main()
