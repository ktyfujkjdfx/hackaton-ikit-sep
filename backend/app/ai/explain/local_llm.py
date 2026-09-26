"""Своя генеративная модель как пояснитель (B.6, шаг 3): локально, без интернета и ключей.

Включается `EXPLAIN_MODE=local`. Модель только ПЕРЕСКАЗЫВАЕТ готовые факты движка A:
числа она берёт из промпта, а всё, что она всё-таки придумает, отрежет guard.py.

Модель в репозиторий не кладём (несколько гигабайт) — путь задаётся переменными окружения:
    LLM_MODEL_PATH    — папка со слитой моделью (training/merge_llm.py), либо
    LLM_BASE_MODEL    — базовая модель с Hugging Face и
    LLM_ADAPTER_PATH  — папка адаптера LoRA (training/runs/dotyanu_llm)

Нет модели, нет torch, кончилось время — возвращаем None, и orchestrator берёт шаблон.
Демо на Render так и работает: там EXPLAIN_MODE=templates, тяжёлых зависимостей нет.
"""
from __future__ import annotations

import logging
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache

from app.ai.explain import prompt as prompt_format

log = logging.getLogger(__name__)

DEFAULT_MAX_NEW_TOKENS = 110
_LOAD_LOCK = threading.Lock()
_EXECUTOR = ThreadPoolExecutor(max_workers=1, thread_name_prefix="local-llm")


def model_path() -> str:
    return os.getenv("LLM_MODEL_PATH", "").strip()


def adapter_path() -> str:
    return os.getenv("LLM_ADAPTER_PATH", "").strip()


def base_model() -> str:
    return os.getenv("LLM_BASE_MODEL", "Vikhrmodels/Vikhr-Qwen-2.5-1.5B-Instruct").strip()


def max_new_tokens() -> int:
    try:
        return int(os.getenv("LLM_MAX_NEW_TOKENS", DEFAULT_MAX_NEW_TOKENS))
    except ValueError:
        return DEFAULT_MAX_NEW_TOKENS


def configured() -> bool:
    """Есть ли что грузить. Проверка дешёвая: её зовёт /api/health."""
    return bool(model_path() or adapter_path())


@lru_cache(maxsize=1)
def _load():
    """Модель и токенизатор. Грузим один раз на процесс; ошибка → (None, None)."""
    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
    except Exception as error:  # noqa: BLE001 — на сервере torch не установлен, это норма
        log.warning("локальная модель недоступна: нет torch/transformers (%s)", error)
        return None, None

    path = model_path()
    device = os.getenv("LLM_DEVICE", "cuda" if torch.cuda.is_available() else "cpu")
    dtype = torch.float16 if device.startswith("cuda") else torch.float32

    # LLM_LOAD_4BIT=1 — для слабых видеокарт: 1,5B в 4 битах занимает около 1,5 ГБ вместо 3,1 ГБ.
    extra: dict = {"dtype": dtype}
    if os.getenv("LLM_LOAD_4BIT", "").strip() in ("1", "true", "yes") and device.startswith("cuda"):
        try:
            from transformers import BitsAndBytesConfig

            extra = {"dtype": dtype, "device_map": {"": 0}, "quantization_config":
                     BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                                        bnb_4bit_compute_dtype=torch.float16)}
        except Exception:  # noqa: BLE001 — нет bitsandbytes, грузим как есть
            log.warning("bitsandbytes нет — гружу модель без 4 бит")

    def _place(loaded):
        """С quantization_config модель уже на видеокарте — второй раз двигать нельзя."""
        return loaded if "quantization_config" in extra else loaded.to(device)

    try:
        if path:
            tokenizer = AutoTokenizer.from_pretrained(path)
            model = _place(AutoModelForCausalLM.from_pretrained(path, **extra))
        else:
            from peft import PeftModel

            tokenizer = AutoTokenizer.from_pretrained(adapter_path())
            model = _place(AutoModelForCausalLM.from_pretrained(base_model(), **extra))
            model = PeftModel.from_pretrained(model, adapter_path())
    except Exception:  # noqa: BLE001 — не загрузилась, значит отвечаем шаблоном
        log.exception("не удалось загрузить локальную модель — остаюсь на шаблонах")
        return None, None

    model.eval()
    log.info("локальная модель загружена на %s", device)
    return model, tokenizer


def available() -> bool:
    if not configured():
        return False
    with _LOAD_LOCK:
        model, _ = _load()
    return model is not None


def _generate(text: str) -> str:
    import torch

    model, tokenizer = _load()
    inputs = tokenizer(text, return_tensors="pt").to(model.device)
    with torch.inference_mode():
        output = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens(),
            do_sample=False,
            repetition_penalty=1.05,
            pad_token_id=tokenizer.pad_token_id or tokenizer.eos_token_id,
        )
    new_tokens = output[0][inputs["input_ids"].shape[1]:]
    return tokenizer.decode(new_tokens, skip_special_tokens=True).strip()


def generate(message: str, intent: str, headline: str, facts: list[dict],
             timeout: float) -> str | None:
    """Ответ модели или None. None — это норма: значит, покажем шаблон."""
    if not configured():
        return None
    with _LOAD_LOCK:
        model, tokenizer = _load()
    if model is None or tokenizer is None:
        return None

    chat = prompt_format.messages(message, intent, headline, facts)
    try:
        text = tokenizer.apply_chat_template(chat, tokenize=False, add_generation_prompt=True)
    except Exception:  # noqa: BLE001 — токенизатор без шаблона чата
        log.exception("у токенизатора нет шаблона чата — остаюсь на шаблонах")
        return None

    try:
        answer = _EXECUTOR.submit(_generate, text).result(timeout=timeout)
    except TimeoutError:
        log.warning("локальная модель не уложилась в %.1f с — беру шаблон", timeout)
        return None
    except Exception:  # noqa: BLE001 — любая ошибка генерации не должна ломать ответ
        log.exception("локальная модель упала — беру шаблон")
        return None
    return answer.strip() or None
