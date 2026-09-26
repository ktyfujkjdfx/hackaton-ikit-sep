# training — датасет, обучение и экспорт модели роли B

Не деплоится. На сервере из этой папки не нужно ничего: туда идут только артефакты
в `backend/app/ai/models/`.

## Как обучить модель (3 команды)

```powershell
cd training; python -m venv .venv-train; .venv-train\Scripts\Activate.ps1; pip install -r requirements-train.txt
python gen_dataset.py
python train_sklearn.py; python eval.py --holdout
```

Первая команда ставит окружение, вторая собирает датасет, третья обучает модель шага 1
и печатает метрики. Модель сразу ложится в `backend/app/ai/models/intent_sklearn.joblib` —
именно её грузит прод при `NLU_MODE=sklearn`.

## Нейросеть (шаг 2, ONNX для прода)

```powershell
python train_rubert.py --epochs 5     # дообучение cointegrated/rubert-tiny2, CPU, минуты
python export_onnx.py                 # torch.onnx.export + int8 → models/rubert_intent/
python eval.py --holdout --onnx       # сравнить sklearn и onnx на одних данных
```

## Генеративный пояснитель (шаг 3, своя видеокарта)

Третья модель роли B. Она не классифицирует, а **пересказывает готовые факты движка** живым
русским языком: отвечает на вопрос студента своими словами, но каждое число обязана взять из
фактов. Считать ей по-прежнему нельзя, и guard проверяет это на каждом ответе.

Нужна видеокарта NVIDIA от 6 ГБ и отдельное окружение (в `.venv-train` его не ставим —
там CPU-torch для ONNX):

```powershell
cd training
python -m venv .venv-llm; .venv-llm\Scripts\Activate.ps1
pip install torch==2.9.1 --index-url https://download.pytorch.org/whl/cu126
pip install -r requirements-llm.txt

python gen_chat_dataset.py                       # датасет из движка A, ~7 200 примеров
python train_llm.py --epochs 2 --max-hours 4     # QLoRA, на RTX 2060 SUPER около 2 часов
python merge_llm.py                              # адаптер + база → одна папка для сервиса
python eval_llm.py --limit 200 --compare-base    # метрики рядом с необученной базой
python chat_llm.py                               # поговорить с помощником в консоли
```

Веса в git **не кладём** (3 ГБ). Сервис берёт модель по пути из `.env`:

```
EXPLAIN_MODE=local
LLM_MODEL_PATH=C:\путь\hackaton-ikit-sep\training\runs\dotyanu_llm_merged
LLM_LOAD_4BIT=1     # для слабой видеокарты: около 1,5 ГБ видеопамяти вместо 3,1
```

Нет весов, нет torch, не уложилась в таймаут — чат сам переходит на шаблоны. Поэтому демо на
Render работает без всего этого: там `EXPLAIN_MODE=templates`.

## Файлы

| Файл | Что делает |
|---|---|
| `manual_phrases.py` | ручные фразы «как пишут в чате», по 18 на класс |
| `gen_dataset.py` | шаблоны со слотами + ручные фразы → `data/intents_train.jsonl` и `intents_test.jsonl` |
| `train_sklearn.py` | TF-IDF char_wb + логистическая регрессия → `intent_sklearn.joblib` |
| `train_rubert.py` | дообучение rubert-tiny2 → `runs/rubert_intent/` |
| `export_onnx.py` | ONNX + int8 → `models/rubert_intent/` |
| `eval.py` | accuracy, macro-F1, отчёт по классам, матрица ошибок в `reports/` |
| `dump_chat_fixtures.py` | фикстуры ответов чата для роли C |
| `update_holdout_report.py` | пересчитать holdout и обновить таблицу в `docs/ai/model_card.md` |
| `answer_variants.py` | банк формулировок ответа: цели обучения генеративной модели |
| `gen_chat_dataset.py` | вопрос + факты движка → `data/chat_sft_*.jsonl`, каждый ответ проходит guard |
| `train_llm.py` | QLoRA-дообучение Vikhr-Qwen-2.5-1.5B-Instruct → `runs/dotyanu_llm/` |
| `merge_llm.py` | слить адаптер с базой → `runs/dotyanu_llm_merged/`, её грузит сервис |
| `eval_llm.py` | grounded / numbers / russian / safe на test и holdout |
| `chat_llm.py` | консольный чат через настоящий `/api/chat` |

Holdout приходит частями (A — 20 фраз, D — 40). Когда файл пополнился:

```powershell
python update_holdout_report.py --check   # кто уже прислал
python update_holdout_report.py           # пересчитать обе модели и обновить model card
```

## Правила датасета

- Объём: 150 фраз на класс в train, 30 в test, 12 классов.
- `random_state = 42`, дедупликация по нормализованному тексту.
- Формулировки (ядра шаблонов) делятся до генерации: примерно 20% уходит только в test,
  поэтому в test нет ни одной формулировки из train.
- `data/intents_holdout_team.jsonl` пишут A и D. Он **никогда** не попадает в train —
  `gen_dataset.py` его не читает. Это главная метрика для жюри.
