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
