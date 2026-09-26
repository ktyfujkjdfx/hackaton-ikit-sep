# Роль B — AI: своя модель, которая понимает вопросы студента

> Команда «Дотяну» · 4 человека · 26–27 сентября 2026 · стоп‑код 11:00 (Красноярск).
> Роли: A — движок и API · B — AI (своя модель) · C — фронтенд и тимлид · D — данные, деплой, исследование. Общая часть в конце каждого файла одинакова.

> Твой личный план. Сначала прочитай свою часть, потом общую часть ниже.
> **Твой главный закон: AI понимает и объясняет, но никогда не считает.** Все числа приходят из движка A.

## B.0 Твоя зона за 30 секунд

- Папки: `backend/app/ai/`, `backend/app/api/chat.py`, `backend/tests/test_ai.py`, `backend/.env.example`, `training/`, `docs/ai/model_card.md`.
- Что ты делаешь:
  1. **Обучаешь свою модель** — классификатор намерений на 12 классов (раздел 9). Сначала быстрая модель scikit‑learn: к 19:00 она уже рабочая и идёт в прод. Потом нейросеть `rubert-tiny2`, дообученная на наших данных, с экспортом в ONNX (к 23:00).
  2. Пишешь `POST /api/chat`: модель определяет намерение → парсер достаёт сумму и дату → вызываешь функции движка A → отдаёшь готовые факты и короткое пояснение.
  3. Делаешь запасные слои: правила (если модель не уверена) и, по желанию, готовый API для текста пояснения (с guard).
- **Две свои модели, и обе не считают деньги.** Классификатор понимает, о чём спрашивает студент. Генеративный пояснитель (шаг 3) отвечает живым языком по уже готовому расчёту: числа он обязан переписать из facts, а guard проверяет каждое. Обучение генеративной модели изначально не планировалось — решение принято по ходу, когда стало ясно, что QLoRA на 1,5B укладывается в два часа на одной игровой видеокарте. Для жюри это свои нейросети, свои данные и своя метрика — включая честность чисел, которую можно проверить кодом.
- Эталон правил и текстов ответов: функции `ask()`, `purchaseAnswer`, `planAnswer`, `explainAnswer`, `termAnswer`, `investAnswer`, `addAnswer`, `refuse` в `<script>` файла `docs/prototype.html`.

## B.1 Зависимости

| От кого | Что | Когда |
|---|---|---|
| A | `models.py` (включая `ChatRequest`, `ChatResponse`) | 17:50 |
| A | функции движка по сигнатурам раздела 7.1 + `engine/format.py` | 18:00 (до этого мокай в тестах) |
| D | `backend/app/data/knowledge.json` | 18:30 |
| A, D | отложенные тестовые фразы `intents_holdout_team.jsonl`: A — 20, D — 40 | 19:00–19:30 |

| Кому | Что | Когда |
|---|---|---|
| C | фикстуры ответов чата `frontend/src/api/fixtures/chat_*.json` (10 фраз из B.8) | **20:00** |
| C | `/api/chat` на sklearn‑модели, все интенты | **21:30** |
| все | решение «onnx или sklearn в проде» | **23:00** |
| D | метрики модели, картинка (матрица ошибок), 4 строки текста для слайда | **01:00** |

## B.2 Архитектура

```
api/chat.py              POST /api/chat → orchestrator.handle(req) → ChatResponse
ai/orchestrator.py       handle(): nlu → parse → execute → explain → guard → ответ
ai/nlu/labels.py         12 меток (раздел 9), порядок фиксирован
ai/nlu/rules.py          регулярки из прототипа → (label, confidence 1.0) или None
ai/nlu/sklearn_nlu.py    загружает models/intent_sklearn.joblib, predict_proba
ai/nlu/onnx_nlu.py       tokenizers (tokenizer.json) + onnxruntime (model.onnx), softmax
ai/nlu/__init__.py       predict(text, history) -> {label, confidence, mode}; current_mode()
ai/parse.py              суммы ("3к", "3 000", "10 тыс", "3т.р.") и даты ("сегодня", "завтра", "15 октября", "15.10"), название покупки
ai/tools.py              execute(label, slots, sit, purchase) → intent, headline, tone, facts, extra (вызывает движок A)
ai/templates.py          текст пояснения для каждого intent и отказы
ai/explain/api_explainer.py  (по желанию) YandexGPT/Claude перефразирует facts; ошибка или таймаут → шаблон
ai/guard.py              числа в тексте API ⊂ числа в facts, иначе шаблон
ai/knowledge.py          knowledge.json → поиск термина
```

**Как `nlu.predict` выбирает модель:**
1. `NLU_MODE=onnx` и модель загрузилась → ONNX; иначе `sklearn`; иначе `rules`.
2. `confidence < NLU_MIN_CONFIDENCE` (0.6) → спрашиваем правила; сработали → берём их (`mode="rules"`).
3. Никто не уверен → `clarify`: «Не понял. Это покупка, трата или вопрос про прогноз?».
4. Контекст: фраза без глагола, но с суммой («а за 1000?»), и последний intent в `history` — `purchase_check` → `purchase_check`.

**Сервер не зависит от `torch` и `transformers`.** В `backend/requirements.txt` только `scikit-learn`, `joblib`, `numpy`, `onnxruntime`, `tokenizers`. Всё тяжёлое — в `training/requirements-train.txt`.

## B.3 Датасет (от него зависит качество)

`training/gen_dataset.py` → `training/data/intents_train.jsonl` и `intents_test.jsonl` (по строке `{"text": "...", "label": "..."}`).

- **Объём:** ≥ 150 фраз на класс в train и 30 на класс в test → около 2 200 фраз.
- **Как собирать:**
  1. Шаблоны со слотами. Предметы: наушники, кроссовки, куртка, билет, телефон… Суммы: `3000`, `3 000`, `3к`, `3 тыс`, `3т`, `три тысячи`. Даты: сегодня, завтра, 15 октября, 15.10, на выходных. Сленг: стипуха, стипа, скинули, закинули, общага, проездной, доставка, такси.
  2. Ручные фразы, по 15–20 на класс, «как пишут в чате»: без заглавных, с опечатками, без знаков препинания.
  3. Перефразирование через чат‑бот в браузере. Это синтетика, по правилам кейса она разрешена. Проси: «30 разных способов спросить X, как пишет студент в мессенджере». **Проверяй глазами**, мусор удаляй.
  4. Трудные пары классов (добавь побольше таких примеров): «купил наушники за 3000» (`add_spend`) и «куплю наушники за 3000?» (`purchase_check`); «вклад это что» (`term`) и «куда вложить» (`invest_advice`); «скинули 2000» (`add_income`) и «хватит до стипухи?» (`forecast`).
- **Отложенная проверка:** `intents_holdout_team.jsonl` — фразы, которые написали A и D, не видя твоих данных. **Никогда не добавляй их в train.** Это главная метрика для жюри.
- Дедупликация по нормализованному тексту, перемешивание, фиксированный `random_state=42`.

## B.4 Обучение

**Шаг 1 — `train_sklearn.py` (к 19:00, идёт в прод):**
```python
Pipeline([("tfidf", TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), min_df=2, sublinear_tf=True)),
          ("clf", LogisticRegression(max_iter=2000, C=5, class_weight="balanced"))])
```
Сохранить в `backend/app/ai/models/intent_sklearn.joblib`. `eval.py` печатает accuracy, macro‑F1, отчёт по классам и строит матрицу ошибок (png) на test и на holdout_team.

**Шаг 2 — `train_rubert.py` (19:30–22:30), своя нейросеть:**
- База: `cointegrated/rubert-tiny2` (Hugging Face, около 29 млн параметров, русский язык, быстро учится на CPU).
- `AutoModelForSequenceClassification(num_labels=12)`, `max_length=64`, `batch=32`, `lr=5e-5`, 4–6 эпох, ранняя остановка по macro‑F1 на test. На CPU ноутбука — минуты; если медленно, используй Google Colab с GPU.
- `export_onnx.py`: `torch.onnx.export` (динамические оси по batch и длине) → `onnxruntime.quantization.quantize_dynamic` (int8). Сохранить `model.onnx`, `tokenizer.json` (`tokenizer.backend_tokenizer.save(...)`) и `labels.json` в `backend/app/ai/models/rubert_intent/`. **Размер — цель ≤ 40 МБ**; если больше 90 МБ, выложи в GitHub Release и скачивай при старте.
- `onnx_nlu.py`: `Tokenizer.from_file` → `enable_truncation(64)`, `enable_padding` → `InferenceSession.run` → softmax. Время ответа на CPU — цель < 50 мс.

**Решение в 23:00 (сообщи в чат):** ONNX идёт в прод, только если выполнены все три условия:
1. macro‑F1 на holdout_team **не хуже**, чем у sklearn;
2. на Render сервис стартует без ошибок по памяти (бесплатный тариф — 512 МБ);
3. `/api/chat` отвечает быстрее 300 мс.

Иначе остаётся `NLU_MODE=sklearn`, а нейросеть показываем на слайде как эксперимент с цифрами. Это тоже баллы, а не провал.

**`docs/ai/model_card.md`** (к 01:00): задача и 12 классов; откуда данные (синтетика, ручные фразы, перефразы) и сколько их; две модели и их метрики на test и на holdout_team; матрица ошибок и где модель ошибается; ограничения («не понимает длинные истории», «опирается на ключевые слова»); что дальше («дообучить на реальных фразах пилота»).

## B.5 Выполнение и ответ (`tools.py`)

| label → intent | Что вызывает у A | facts (строки через `format.py`) | extra |
|---|---|---|---|
| `purchase_check` → `purchase_check` (нет суммы → `clarify`) | `check_purchase` | без минуса: «Самый низкий остаток после покупки», «Когда». С минусом: «Первый день без денег», «Самый большой минус» (tone bad), «Без минуса можно купить» («с 15 октября» или «не в ближайшие 30 дней»), «Цель … сдвинется» («на 50 дней») | `purchase`; actions `open_explain`, `defer` (`{date}`), `show_jobs` (`{amount}`) |
| `forecast` | `headline` | «До …», «Самый низкий остаток», «Минус начнётся» | нет дохода → action `open_add_income` |
| `explain` | `series`, `stats` | «Сейчас на карте (факт)», «Обычные траты: 300 ₽ × 13 (оценка)», «Обязательные платежи», «Поступления (ожидается)», «Итог» | `open_explain` |
| `deficit_plan` | `deficit_plan`: по активной покупке, если с ней минус; иначе base; иначе pessimistic | по факту на вариант + «легко» или «сложно» | `show_jobs` |
| `categories` | `situation.categories` | «Еда — 5 400 ₽/мес · 60%» … | — |
| `add_spend` / `add_income` → `add_entry` (нет суммы → `clarify`) | ничего не считает | «Тип», «Сумма», «Дата», «Надёжность» или «Категория» | `proposed_entry`; action `save_entry` |
| `term` | `knowledge.find` | — | `source` |
| `invest_advice` → `invest_info` | — | — | action `open_learn` |
| `credentials`, `money_operation` → `refusal` | — | — | — |
| `off_topic` | — | — | — |

`tool_calls` в ответе нужны для экрана, например `[{"name":"check_purchase","args":{"amount":3000,"date":"2026-09-27"}}]`. Поле `nlu` — это `{mode, label, confidence}`; фронт покажет «модель: purchase_check · 94%».
**Сохраняет трату фронт** (ситуация хранится у него). Бэкенд только предлагает `proposed_entry`, поэтому AI ничего не решает молча.

## B.6 Пояснение и guard

- **По умолчанию `EXPLAIN_MODE=templates`**: тексты из прототипа, в них подставляются facts. Это детерминированно и безопасно. На защите держим так, если API не проверен.
- **По желанию** (только после 00:30 и если всё остальное готово): `api_explainer.py` — готовый API перефразирует факты в 1–2 предложения. System‑промпт:
  ```
  Ты пишешь 1–2 коротких предложения простым языком для студента по готовому результату расчёта.
  Используй ТОЛЬКО числа и даты из списка фактов, дословно. Новых чисел не придумывай.
  Не советуй, куда вкладывать. Не решай за пользователя. Без приветствий и эмодзи.
  Интент: {intent}. Вопрос: «{message}». Факты: {facts}
  ```
  Anthropic API официально недоступен в России. Если у команды нет рабочего ключа с оплатой, бери YandexGPT (SDK `openai`, `base_url="https://llm.api.cloud.yandex.net/v1"`, `model=f"gpt://{FOLDER_ID}/yandexgpt/latest"`) или оставь шаблоны.
- **Guard:** все числа в тексте API (нормализуй пробелы и «−») должны встречаться в facts: в значениях, подписях, днях и годах дат. Если нет — берём шаблон, ставим `guarded=true`, пишем в лог.

## B.7 План по часам

| Время | Задача | Готово, когда |
|---|---|---|
| 16:40–17:20 | Прочитать файл; зафиксировать `labels.py`; начать `gen_dataset.py` (репо для этого не нужен) | 12 меток, генератор выдаёт первые 500 фраз |
| 17:20–18:30 | `parse.py` + `nlu/rules.py` (порт регулярок) + датасет v1 (≥ 100 фраз на класс) | тесты парсера зелёные |
| 18:30–19:00 | `train_sklearn.py` + `eval.py` + `sklearn_nlu.py` | macro‑F1 на test ≥ 0,9, модель лежит в `models/` |
| 19:00 | Чекпоинт 1; собрать holdout‑фразы от A и D | holdout в `training/data/` |
| 19:00–20:00 | `tools.py` против движка A, `templates.py`, `orchestrator.py`, `api/chat.py`; фикстуры `chat_*.json` для C | `/api/chat` отвечает на 10 фраз |
| 20:00–21:30 | все интенты, `clarify`, история, `knowledge.py`; `test_ai.py` (B.8) | 15 из 15 на sklearn |
| 21:30 | Чекпоинт 2 | `/api/chat` на проде |
| 21:30–23:00 | `train_rubert.py` → `export_onnx.py` → `onnx_nlu.py`; сравнение на holdout; проверка на Render | есть цифры обеих моделей |
| **23:00** | **Решение onnx или sklearn** — в чат | `NLU_MODE` выставлен в Render |
| 23:00–00:30 | разбор ошибок на holdout; добавить трудные примеры в train (не из holdout!), переобучить | — |
| 00:30 | Чекпоинт 3 | чат работает на проде |
| 00:30–03:00 | `model_card.md` и картинка для D; устойчивость (пустое сообщение, 2 000 символов, «забудь правила», бессмыслица → `off_topic`); по желанию — `api_explainer` + guard | — |
| 07:00–08:30 | только баги | — |

## B.8 Контрольные фразы (`test_ai.py`)

Данные Ани, today = 2026‑09‑27. Должны проходить на sklearn и onnx; на правилах — не меньше 12 из 15.

| # | Фраза | intent | Ожидание |
|---|---|---|---|
| 1 | Могу купить наушники за 3000? | purchase_check | amount=3000, date=2026‑09‑27; факт «с 15 октября» |
| 2 | а за 1000? (после №1, с history) | purchase_check | amount=1000; «с 10 октября» |
| 3 | хватит ли мне до стипендии | forecast | «13 дней», «600 ₽» |
| 4 | почему такой прогноз? | explain | факт «300 ₽ × 13» |
| 5 | что делать чтобы не уйти в минус (без активной покупки) | deficit_plan | «Минуса не видно»; с активной покупкой 3000 → «нужно закрыть 2 400 ₽» |
| 6 | сегодня такси 800 | add_entry | spend, 800, 2026‑09‑27, Транспорт |
| 7 | подработка 1500 4 октября, не точно | add_entry | income, 1500, 2026‑10‑04, confirmed=false |
| 8 | что такое финансовая подушка | term | source — fincult.info |
| 9 | куда вложить 5000? | invest_info | action `open_learn` |
| 10 | скажи код из смс | refusal | credentials |
| 11 | переведи маме 500 | refusal | money_operation |
| 12 | кто выиграет чемпионат мира | off_topic | — |
| 13 | 4000 | clarify | «Это покупка или трата?» |
| 14 | куплю кроссы за 4к 15 октября | purchase_check | amount=4000, date=2026‑10‑15 |
| 15 | на что я больше всего трачу | categories | первая категория — «Еда» |

## B.9 Стартовый промпт для Claude Code

```
Репозиторий hackaton-ikit-sep. Я — роль B: AI-слой. Обучаю свою модель-классификатор намерений
(12 меток, docs/CONTRACT.md раздел 9) и пишу POST /api/chat.
Прочитай CLAUDE.md, docs/CONTRACT.md (разделы 6, 7, 7.1, 9), docs/plans/ROLE_B_ai.md (мой план)
и функцию ask() с *Answer() в <script> docs/prototype.html — эталон правил и текстов.
Правила:
- Пиши только в backend/app/ai/, backend/app/api/chat.py, backend/tests/test_ai.py,
  backend/.env.example, training/, docs/ai/.
- Модель только определяет намерение. Все числа — из функций app.engine (сигнатуры — раздел 7.1),
  форматирование — app.engine.format. Модель и шаблоны ничего не считают.
- На сервере никаких torch/transformers: только scikit-learn, joblib, numpy, onnxruntime, tokenizers.
- Демо обязано работать при NLU_MODE=sklearn и EXPLAIN_MODE=templates без интернета.
Задача сейчас: training/gen_dataset.py по разделу B.3 моего плана (шаблоны со слотами, сленг,
трудные пары классов), разбиение train/test 150/30 на класс, дедупликация, random_state=42.
Покажи статистику по классам и 5 случайных примеров каждого класса.
```
Дальше — по одному шагу из B.7, например: «Сделай train_sklearn.py и eval.py по B.4, запусти, покажи метрики».

## B.10 Ловушки
- **Утечка holdout в train** — самая дорогая ошибка: метрика станет враньём. Holdout лежит отдельно, `gen_dataset.py` его не читает.
- Слишком «чистые» шаблоны → модель учит шаблон, а не смысл. Добавляй опечатки, сленг, разный порядок слов.
- Даты без года («15 октября») — год берём из `today`; если дата уже прошла, берём следующий год.
- ONNX: проверь, что токенизатор даёт те же id, что при обучении. Сравни предсказания torch и onnx на 20 фразах.
- Пользователю никогда не показываем exception — только «Не получилось понять вопрос. Попробуй: „Могу купить … за …?“».

## Чек‑лист B перед фича‑фризом
- [ ] 15 фраз зелёные на модели, которая в проде; на правилах ≥ 12
- [ ] Метрики на holdout_team посчитаны честно, `model_card.md` готов, картинка у D
- [ ] В проде тот `NLU_MODE`, о котором договорились в 23:00, и `/api/health` его показывает
- [ ] Guard протестирован (если используется API)
- [ ] `training/` воспроизводится по разделу README «Как обучить модель» (3 команды)
- [ ] `.env.example` актуален, ключей в git нет; модель ≤ 40 МБ или лежит в Release

---

# ОБЩАЯ ЧАСТЬ — одинакова у всех четырёх

> Разделы 1–11 — общий договор команды. Они слово в слово повторяются в файлах A, B, C и D. Тимлид — C.
> Если твоя личная часть противоречит общей — права общая. Любое изменение общей части делается только через PR в `docs/CONTRACT.md` и сообщение в чат команды.

## 1. Продукт на одной странице

**Название (рабочее):** «Дотяну».
**Хакатон:** Стартап‑хакатон «Пятый элемент» (СФУ), кейс 1 Т‑Банка «AI в личных финансах».
**Стоп‑код:** воскресенье 27.09, **11:00 по Красноярску**.
**Эталон вида и логики:** `docs/prototype.html` — открой в браузере. Всё, что есть в прототипе, должно быть в продукте. Расчётный код прототипа (JS) = эталон формул для движка.

**Сегмент:** студенты 18–22 лет в первый год самостоятельной жизни: общежитие, стипендия, деньги от родителей, иногда подработка.
**Проблема:** не понимают, хватит ли денег до следующего поступления, и тратят вслепую.
**Главный вопрос пользователя:** «Хватит ли мне до стипендии и могу ли я купить это сейчас?»

**Позиционирование (фраза для жюри):**
> Банки показывают, что уже произошло с деньгами. Мы — для тех, кто распоряжается деньгами впервые. Отличаем постоянные деньги от разовых, честно показываем, где факт, а где оценка, отвечаем не «хватит ли», а «когда можно купить без минуса», и на каждом шаге объясняем, как посчитали.

**Киллер‑фичи (должны работать и быть заметны):**
1. **«Когда можно купить»** — самая ранняя дата, с которой покупка не уводит в минус, плюс день начала минуса и его размер.
2. **Постоянное и разовое** — 4 типа денег: постоянный доход (сплошная линия), непостоянный доход (пунктир, два варианта прогноза), постоянные расходы (платёж на дату), непостоянные расходы (среднее в день, «оценка»).
3. **План выхода из минуса** — 3 варианта: перенести покупку / тратить на N ₽ в день меньше / найти N ₽ к дате. Метка «легко» или «сложно». Вакансии — только карточки с пометкой «Пример».
4. **Честные метки** у каждой суммы: факт / ожидается / может не прийти / оценка. Экран «Как посчитали?», где любую цифру можно поменять и сразу увидеть пересчёт.
5. **Учим, а не советуем** — карточка «Как устроены накопления и инвестиции?» одинаковая для всех, без сумм пользователя, не показывается при минусе. На «куда вложить» AI вежливо отказывает и показывает эту карточку.
6. **«Как мы проверяли»** — страница, где 13 эталонных сценариев прогоняются кодом вживую: «13/13».

**Свои модели:** классификатор намерений (раздел 9) понимает вопрос, а дообученная генеративная модель пересказывает готовый расчёт живым языком. Считать не умеет ни одна: суммы и даты — только код.

**Не делаем:** регистрацию и логины, загрузку реальных выписок, MCC, конверты, геймификацию, реальные вакансии, генерацию сумм моделью, Docker, мобильную вёрстку (десктоп‑веб; на телефоне просто не должно ломаться).

**Жёсткие правила кейса (нарушение = потеря баллов):**
- Только синтетические данные. Никаких паролей, кодов из СМС, CVV, номеров карт, реальных счетов.
- **Все суммы, даты, остатки считает код (движок). LLM никогда не считает.**
- Нет персональных инвестрекомендаций. Нет решений за пользователя. Нет операций с деньгами.
- Предположение не выдаётся за факт. Рискованные запросы обрабатываются, ограничения видны.

**Критерии (100 баллов):** Представление 15 · Анализ 35 · Реализация 50 (данные 10, работающий функционал 10, корректность и проверки 10, качество продукта и репозитория 10, документация 5, доп. возможности 5).

## 2. Стек (согласован, не меняем)

| Слой | Технология | Почему |
|---|---|---|
| Backend | **Python 3.11, FastAPI, Pydantic v2, Uvicorn** | быстро, автодокументация `/docs`, типы |
| Тесты | **pytest** | 13 эталонных сценариев + API + AI |
| AI: понимание запроса (NLU) | **своя обученная модель — классификатор намерений.** Шаг 1: TF‑IDF + логистическая регрессия (scikit‑learn). Шаг 2: дообученная нейросеть `rubert-tiny2` (обучение — `transformers` на ноутбуке или в Colab; на сервере — только `onnxruntime` + `tokenizers`). Суммы и даты достаёт парсер на правилах. Запасной слой — правила | своя модель, лёгкая, работает без интернета |
| AI: пояснение | **шаблоны** по умолчанию и на проде; по желанию — **своя дообученная модель** (Vikhr-Qwen-2.5-1.5B + QLoRA, локально, `EXPLAIN_MODE=local`) или готовый API (YandexGPT, Claude Haiku). Любой из них только перефразирует facts, и его проверяет guard | числа всегда из движка |
| Frontend | **React 18 + TypeScript + Vite**, чистый CSS с токенами из прототипа, график — свой SVG‑компонент (порт из прототипа) | без UI‑китов, вид как в прототипе |
| Деплой (без Docker) | **Render, два сервиса:** backend — Web Service (Python), frontend — Static Site. Описаны в `render.yaml` | бесплатно, деплой из `main` |
| CI | GitHub Actions: `pytest` + `npm run build` на каждый PR | баллы за качество репо |

**Ключевой принцип архитектуры:** backend **без состояния**. Вся ситуация пользователя (`Situation`) живёт в браузере и отправляется в каждом запросе. Сервер ничего не хранит → нет БД, нет логинов, нет утечек.

**Команда на Windows.** Команды в PowerShell:
```powershell
# backend
cd backend; python -m venv .venv; .venv\Scripts\Activate.ps1; pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
# frontend (второй терминал)
cd frontend; npm install; npm run dev   # http://localhost:5173, /api проксируется на :8000
```

**Переменные окружения** (`backend/.env`, в git только `.env.example`):
```
NLU_MODE=sklearn              # onnx | sklearn | rules  — чем понимаем вопрос
NLU_MIN_CONFIDENCE=0.6        # ниже — переходим на правила
EXPLAIN_MODE=templates        # templates | local | yandex | anthropic — чем пишем пояснение
YANDEX_API_KEY=
YANDEX_FOLDER_ID=
ANTHROPIC_API_KEY=
LLM_TIMEOUT_S=6
DEMO_TODAY=2026-09-27
CORS_ORIGINS=http://localhost:5173
```
Frontend (`frontend/.env.production`): `VITE_API_URL=https://dotyanu-api.onrender.com`. Локально `VITE_API_URL` пустой — работает прокси Vite.

## 3. Репозиторий и владельцы папок

Репозиторий: `hackaton-ikit-sep`. **Каждый пишет только в свои папки.** Чужую папку — только через PR с ревью владельца.
Роли: **A** — движок и API · **B** — AI (своя модель) · **C** — фронтенд + **тимлид** · **D** — данные, деплой, исследование.

```
hackaton-ikit-sep/
├─ README.md                    D
├─ CLAUDE.md                    C   (правила для Claude Code)
├─ render.yaml                  D   (два сервиса Render, без Docker)
├─ .gitignore                   C
├─ .github/workflows/ci.yml     D
├─ docs/
│  ├─ CONTRACT.md               C   (копия общей части этих файлов, разделы 1–11)
│  ├─ prototype.html            C   (эталон вида и формул)
│  ├─ plans/ROLE_*.md           C   (эти 4 файла)
│  ├─ checks.md                 A   (таблица 13 сценариев)
│  ├─ ai/model_card.md          B   (как обучали модель, метрики)
│  └─ pitch/                    D   (исследование, опрос, презентация)
├─ backend/
│  ├─ requirements.txt          A   (B дописывает scikit-learn, onnxruntime, tokenizers, numpy, joblib через PR)
│  ├─ .env.example              B
│  ├─ app/
│  │  ├─ main.py                A   (роутеры + CORS)
│  │  ├─ models.py              A   (все Pydantic‑схемы из разделов 5–6)
│  │  ├─ engine/                A   (весь расчёт; чистые функции)
│  │  ├─ api/
│  │  │  ├─ routes.py           A   (всё, кроме чата)
│  │  │  └─ chat.py             B   (POST /api/chat)
│  │  ├─ ai/                    B
│  │  │  ├─ orchestrator.py  parse.py  tools.py  templates.py  guard.py  knowledge.py
│  │  │  ├─ nlu/ labels.py  rules.py  sklearn_nlu.py  onnx_nlu.py
│  │  │  ├─ explain/ templates_x.py  api_explainer.py
│  │  │  └─ models/ intent_sklearn.joblib  rubert_intent/{model.onnx, tokenizer.json, labels.json}
│  │  └─ data/                  D   (personas.json, knowledge.json)
│  ├─ scripts/dump_fixtures.py  A
│  └─ tests/
│     ├─ test_engine.py  test_checks.py  test_api.py   A
│     └─ test_ai.py                                    B
├─ training/                    B   (НЕ деплоится: датасет, обучение, экспорт, оценка)
│  ├─ requirements-train.txt  gen_dataset.py  train_sklearn.py  train_rubert.py  export_onnx.py  eval.py
│  └─ data/ intents_train.jsonl  intents_test.jsonl  intents_holdout_team.jsonl
└─ frontend/                    C   (весь фронт)
   └─ src/api/fixtures/*.json   A и B генерируют, C использует
```

## 4. Правила работы в git

- Ветка `main` всегда деплоится. Прямые пуши в `main` запрещены, кроме часа 0.
- Ветки: `a/...`, `b/...`, `c/...`, `d/...`. PR маленькие, мержим часто (минимум раз в 1–1,5 часа).
- PR проходит CI (pytest + build). Ревью: достаточно одного человека, или самого владельца, если меняет только свою папку.
- Коммиты по‑русски или по‑английски, но понятные: `engine: earliest_safe_date + tests`.
- **Никаких `.env`, ключей, `node_modules`, `.venv`, `__pycache__`, `dist` в git.**
- Изменение контракта (разделы 5–7): PR в `docs/CONTRACT.md` + сообщение в чат «МЕНЯЮ КОНТРАКТ: …» + явное «ок» от затронутых ролей.

## 5. Модель данных (JSON, snake_case, суммы — целые рубли, даты — `"YYYY-MM-DD"`)

```jsonc
// Income — поступление
{ "id": "inc1", "name": "Стипендия", "amount": 3200, "date": "2026-10-10", "confirmed": true }
// confirmed=true  → постоянный доход («Точно придёт», метка «ожидается»)
// confirmed=false → непостоянный доход («Может не прийти»)

// Obligation — постоянный обязательный платёж
{ "id": "ob1", "name": "Общежитие", "amount": 1800, "date": "2026-10-05" }

// Spend — разовая трата, добавленная пользователем (факт)
{ "id": "sp1", "name": "Такси", "amount": 800, "date": "2026-09-27", "category": "Транспорт" }

// Goal — цель накопления (может быть null)
{ "name": "Ноутбук", "target": 40000, "current": 25000, "date": "2027-06-01" }

// Category — средние траты по истории (может быть null у анкеты)
{ "name": "Еда", "per_day": 180 }

// HistoryOp — прошлая операция (только для показа, в прогноз НЕ входит — уже учтена в balance)
{ "date": "2026-09-19", "name": "Кроссовки", "amount": -4200, "category": "Прочее" }
// amount < 0 — трата, > 0 — доход. category "Обязательное" = регулярный платёж, "Доход" = поступление

// Situation — всё, что знаем о пользователе. Живёт во фронте, шлётся в каждом запросе.
{
  "today": "2026-09-27",
  "balance": 6900,                 // факт
  "daily": 300,                    // оценка: обычные траты в день
  "incomes": [Income],
  "obligations": [Obligation],
  "spends": [Spend],
  "goal": Goal | null,
  "categories": [Category] | null,
  "history": [HistoryOp]           // [] у анкеты
}

// Purchase — проверяемая покупка (гипотеза, не трата)
{ "amount": 3000, "date": "2026-09-27", "name": "Наушники" }
```

## 6. API (все ответы JSON; ошибки валидации — HTTP 422 `{ "errors": [ValidationError] }`)

| Метод | Путь | Вход | Выход | Владелец |
|---|---|---|---|---|
| GET | `/api/health` | — | `{ "ok": true, "nlu": "onnx"\|"sklearn"\|"rules", "explain": "templates"\|"yandex"\|"anthropic" }` | A |
| GET | `/api/personas` | — | `[{ "id": "anya", "title": "Аня", "subtitle": "1 курс · общежитие" }]` | A |
| GET | `/api/personas/{id}` | — | `{ "id", "who", "situation": Situation }` | A |
| POST | `/api/validate` | `{ "situation" }` | `{ "ok": bool, "errors": [ValidationError] }` | A |
| POST | `/api/dashboard` | `{ "situation", "purchase": Purchase\|null }` | `Dashboard` | A |
| POST | `/api/purchase/check` | `{ "situation", "purchase" }` | `PurchaseCheck` | A |
| GET | `/api/checks` | — | `ChecksResult` | A |
| POST | `/api/chat` | `ChatRequest` | `ChatResponse` | B |

```jsonc
// ValidationError
{ "field": "balance" | "daily" | "incomes" | "obligations" | "goal" | "purchase",
  "index": 0 | null, "subfield": "amount" | "date" | null, "message": "Дата поступления уже прошла. Укажи следующую." }

// SeriesStats
{ "min": 600, "min_date": "2026-10-09",
  "first_negative_date": null, "last_negative_date": null,
  "max_deficit": 0, "first_negative_amount": 0 }

// DaySeries
{ "days": [{ "date": "2026-09-27", "balance": 6600 }, ...30 шт], "stats": SeriesStats }

// Headline
{ "state": "ok" | "tight" | "deficit" | "depends" | "no_income",
  "next_income": { "name": "Стипендия", "date": "2026-10-10", "days": 13, "confirmed": true } | null,
  "next_confirmed_income": {...} | null,
  "min_balance": 600, "min_date": "2026-10-09",
  "first_negative_date": null, "max_deficit": 0,
  "days_of_spending_left": 2 }            // floor(min_balance / daily), если min ≥ 0

// Event (для графика и списка «Ближайшие»)
{ "date": "2026-10-05", "kind": "income" | "obligation" | "spend" | "purchase",
  "name": "Общежитие", "amount": 1800, "confirmed": true | null }

// MoneyTypes
{ "stable_income":   { "total": 13200, "items": [Income] },
  "unstable_income": { "total": 0,     "items": [] },
  "stable_expenses": { "total": 2400,  "items": [Obligation] },
  "variable_expenses": { "total": 9000, "daily": 300, "days": 30, "one_off": [Spend] },
  "reliable_total": 17700 }               // balance + stable_income − stable_expenses

// ReduceOption / DeficitPlan
{ "deficit": 2400, "by_date": "2026-10-09",
  "first_needed_amount": 1200, "first_needed_date": "2026-10-05",
  "based_on": "base" | "pessimistic" | "purchase",
  "options": [
    { "kind": "postpone", "date": "2026-10-15", "ease": "easy" },                       // только если есть безопасная дата
    { "kind": "reduce", "per_day": 185, "new_daily": 115, "until": "2026-10-14", "days": 18,
      "possible": true, "ease": "hard", "flexible_per_day": 60 },
    { "kind": "earn", "amount": 2400, "by_date": "2026-10-09",
      "first_amount": 1200, "first_date": "2026-10-05", "ease": "hard" } ] }

// GoalPlan
{ "monthly_surplus": 1800, "per_day": 60, "remaining": 15000,
  "eta": "2027-06-04" | null, "late_days": 3 | null, "need_monthly": 1822 | null,
  "eta_with_purchase": "2027-07-24" | null, "shift_days": 50 | null }

// PurchaseCheck
{ "purchase": Purchase,
  "verdict": "ok" | "tight" | "deficit",
  "before": SeriesStats, "after": SeriesStats,
  "earliest_safe_date": "2026-10-15" | null,
  "safe_depends_on_unconfirmed": false,
  "goal": GoalPlan | null,
  "plan": DeficitPlan | null }

// HistoryItem = HistoryOp + { "regular": bool, "large": bool }

// Dashboard — всё для главного экрана одним запросом
{ "today": "2026-09-27", "horizon_days": 30,
  "headline": Headline,
  "scenarios": { "base": DaySeries,
                 "pessimistic": DaySeries | null,          // есть, если есть confirmed=false в горизонте
                 "with_purchase": DaySeries | null,
                 "with_purchase_pessimistic": DaySeries | null },
  "events": [Event],
  "money_types": MoneyTypes,
  "goal": GoalPlan | null,
  "purchase": PurchaseCheck | null,
  "deficit_plan": DeficitPlan | null,                      // для base, а если base без минуса — для pessimistic
  "history": [HistoryItem],
  "show_learn_card": bool,
  "assumptions": ["Обычные траты — 300 ₽ в день, оценка по истории за 2 месяца", "..."],
  "unknowns": ["Будущие необычные траты: подарки, поломки", "Придут ли деньги точно в срок", "Что будет после 26 октября: прогноз на 30 дней"] }

// ChecksResult
{ "passed": 13, "total": 13,
  "items": [{ "id": 1, "title": "Аня без покупок", "expected": "минимум 600 ₽, 9 октября",
              "got": "600 ₽, 9 октября", "ok": true }] }

// ChatRequest
{ "situation": Situation, "purchase": Purchase | null,
  "message": "Могу купить наушники за 3000?",
  "history": [{ "role": "user" | "assistant", "text": "..." }] }   // последние ≤ 6

// ChatResponse
{ "intent": "purchase_check" | "forecast" | "explain" | "deficit_plan" | "categories" |
            "term" | "add_entry" | "invest_info" | "refusal" | "clarify" | "off_topic",
  "tool_calls": [{ "name": "check_purchase", "args": { "amount": 3000, "date": "2026-09-27" } }],
  "headline": "Если купить сейчас — будет минус",
  "tone": "good" | "bad" | "neutral",
  "facts": [{ "label": "Первый день без денег", "value": "5 октября", "tone": null },
            { "label": "Самый большой минус", "value": "2 400 ₽", "tone": "bad" }],
  "text": "Если подождать до 15 октября, покупка не уведёт в минус. Решение за тобой.",
  "source": { "title": "fincult.info — сайт Банка России", "url": "https://fincult.info" } | null,
  "purchase": Purchase | null,           // фронт ставит её как активную покупку
  "proposed_entry": { "type": "spend" | "income", "name": "Такси", "amount": 800,
                      "date": "2026-09-27", "confirmed": true, "category": "Транспорт" } | null,
  "actions": [{ "kind": "open_explain" | "defer" | "show_jobs" | "save_entry" | "open_learn" |
                         "check_purchase" | "open_add_income",
                "label": "Как посчитали?", "payload": {} }],
  "nlu": { "mode": "onnx" | "sklearn" | "rules", "label": "purchase_check", "confidence": 0.94 },
  "explainer": "templates" | "yandex" | "anthropic",
  "guarded": false }                     // true = текст API отброшен guard'ом, показан шаблон
```

Форматирование: **Dashboard и PurchaseCheck отдают сырые числа и ISO‑даты** — форматирует фронт. **ChatResponse отдаёт уже отформатированные строки** (`"2 400 ₽"`, `"5 октября"`) — форматирует backend функциями `engine/format.py`, чтобы пояснение и guard видели ровно те же строки, что и пользователь.

CORS: backend разрешает домены из `CORS_ORIGINS`. Фронт ходит на `VITE_API_URL + "/api/..."`.

## 7. Правила расчёта (движок). Единственный источник истины — `backend/app/engine`

- **Горизонт:** 30 дней, `d = 0..29`, `date(d) = today + d`. День 0 = сегодня.
- Элементы с датой вне `[today, today+29]` игнорируются в прогнозе.
- **Остаток на конец дня d:**
  `bal(d) = bal(d−1) − (daily − reduce_if_d≤until) − obligations(d) − spends(d) + incomes(d)[только confirmed, если pessimistic] − purchase(d)`, где `bal(−1) = balance`.
  Порядок событий внутри дня не важен — считаем на конец дня.
- **stats:** `min`, `min_date` (первый день с минимумом), `first_negative_date`, `last_negative_date`, `max_deficit = max(0, −min)`, `first_negative_amount = −bal(first_negative_day)`.
- **«Безопасно»** = остаток ≥ 0 в каждый день горизонта. **«Впритык»** = `0 ≤ min < 3 × daily` (только надпись).
- **next_income:** ближайшее поступление с `1 ≤ d ≤ 29` (любое); `next_confirmed_income` — только confirmed.
- **headline.state:**
  1. нет `next_income` → `no_income`;
  2. base имеет минус → `deficit`;
  3. есть confirmed=false и pessimistic имеет минус → `depends`;
  4. `min < 3 × daily` → `tight`;
  5. иначе `ok`.
- **earliest_safe_date(amount):** первый `D ∈ 0..29`, при котором ряд с покупкой в день D не имеет минуса; иначе `null`. `safe_depends_on_unconfirmed = true`, если pessimistic‑ряд с покупкой в эту дату уходит в минус.
- **verdict покупки:** минус после покупки → `deficit`; иначе `min_after < 3 × daily` → `tight`; иначе `ok`.
- **reduce (тратить меньше):** `per_day = max по дням d с bal(d)<0 от ceil(−bal(d) / (d+1))`; `until = last_negative_date`; `days = last_negative_day + 1`; `new_daily = daily − per_day`; `possible = per_day ≤ daily`.
  `flexible_per_day` = сумма `per_day` категорий «Кафе и доставка» и «Прочее» (0, если категорий нет).
  `ease = easy`, если `per_day ≤ max(flexible_per_day, 0.2 × daily)`, иначе `hard`.
- **earn:** `amount = max_deficit`, `by_date = min_date`, `first_amount = first_negative_amount`, `first_date = first_negative_date`; `ease = easy`, если `amount ≤ 1500`, иначе `hard`.
- **postpone:** есть, только если `earliest_safe_date ≠ null`; всегда `easy`.
- **goal:** `monthly_surplus = Σincomes(все, в горизонте) − Σobligations(в горизонте) − daily × 30`; `per_day = monthly_surplus / 30`; `remaining = max(0, target − current)`; `one_off = Σspends в горизонте`.
  Если `per_day ≤ 0` → `eta = null` («при текущем темпе на цель ничего не остаётся»).
  `days = ceil((remaining + one_off) / per_day)`, `eta = today + days`, `late_days = eta − goal.date` (в днях),
  `need_monthly = ceil(remaining / days_to_goal_date × 30)`.
  С покупкой: `days_x = ceil((remaining + one_off + amount) / per_day)`, `shift_days = days_x − days`.
- **money_types:** см. раздел 6. `variable_expenses.total = daily × 30 + Σspends`.
- **history flags:** `regular = category == "Обязательное" или (amount > 0 и имя совпадает с confirmed‑доходом)`; `large = amount < 0 и не regular и −amount ≥ 5 × daily`.
- **show_learn_card = base без минуса И (нет покупки ИЛИ покупка без минуса) И (нет pessimistic ИЛИ pessimistic без минуса).**
- **Валидация:** `balance` число ≥ 0; каждое поступление `amount > 0`, дата есть и `≥ today`; каждый платёж `amount > 0`, дата `≥ today`; `daily ≥ 0`; цель: `target > 0`, `0 ≤ current < target`, дата `> today`; покупка: `amount > 0`, дата в горизонте. Тексты ошибок — простые, говорят, как исправить.

### 7.1 Сигнатуры функций движка (владелец A; B вызывает именно их)

```python
# backend/app/engine/__init__.py — реэкспортирует всё ниже
from datetime import date
from app.models import (Situation, Purchase, SeriesStats, DaySeries, Headline, MoneyTypes,
                        DeficitPlan, GoalPlan, PurchaseCheck, Dashboard, ValidationError,
                        HistoryItem, ChecksResult, Income, Event)

H = 30
def day_index(sit: Situation, d: date | str) -> int: ...
def series(sit: Situation, purchase: Purchase | None = None, reduce: int = 0,
           reduce_until: int = H - 1, pessimistic: bool = False) -> list[int]: ...
def stats(sit: Situation, values: list[int]) -> SeriesStats: ...
def to_day_series(sit: Situation, values: list[int]) -> DaySeries: ...
def next_income(sit: Situation, only_confirmed: bool = False) -> Income | None: ...
def has_unconfirmed(sit: Situation) -> bool: ...
def earliest_safe_date(sit: Situation, amount: int) -> date | None: ...
def deficit_plan(sit: Situation, values: list[int], based_on: str,
                 safe_date: date | None = None) -> DeficitPlan | None: ...
def goal_plan(sit: Situation, extra: int = 0) -> GoalPlan | None: ...
def check_purchase(sit: Situation, purchase: Purchase) -> PurchaseCheck: ...
def headline(sit: Situation) -> Headline: ...
def money_types(sit: Situation) -> MoneyTypes: ...
def history_items(sit: Situation) -> list[HistoryItem]: ...
def events(sit: Situation, purchase: Purchase | None) -> list[Event]: ...
def validate(sit: Situation, purchase: Purchase | None = None) -> list[ValidationError]: ...
def build_dashboard(sit: Situation, purchase: Purchase | None) -> Dashboard: ...
def run_checks() -> ChecksResult: ...
# format.py
def format_rub(v: int) -> str: ...          # 2400 -> "2 400 ₽", -200 -> "−200 ₽" (неразрывный пробел)
def format_date_ru(d: date | str, with_year_if_other: bool = True) -> str: ...  # "5 октября", "4 июня 2027"
def days_word(n: int) -> str: ...           # "1 день", "2 дня", "5 дней"
```

## 8. Эталонные данные и 13 проверок

`backend/app/data/personas.json` (владелец D; значения ниже — финальные, менять нельзя без всей команды):

```json
{
  "anya": { "who": "Аня · 1 курс · общежитие", "title": "Аня", "subtitle": "1 курс, общежитие, 2 месяца истории",
    "situation": { "today": "2026-09-27", "balance": 6900, "daily": 300,
      "incomes": [ {"id":"i1","name":"Стипендия","amount":3200,"date":"2026-10-10","confirmed":true},
                   {"id":"i2","name":"Перевод от родителей","amount":10000,"date":"2026-10-15","confirmed":true} ],
      "obligations": [ {"id":"o1","name":"Подписка на музыку","amount":200,"date":"2026-10-01"},
                       {"id":"o2","name":"Связь","amount":400,"date":"2026-10-03"},
                       {"id":"o3","name":"Общежитие","amount":1800,"date":"2026-10-05"} ],
      "spends": [],
      "goal": {"name":"Ноутбук","target":40000,"current":25000,"date":"2027-06-01"},
      "categories": [ {"name":"Еда","per_day":180},{"name":"Транспорт","per_day":60},
                      {"name":"Кафе и доставка","per_day":40},{"name":"Прочее","per_day":20} ],
      "history": [ {"date":"2026-09-24","name":"Продукты у общежития","amount":-640,"category":"Еда"},
                   {"date":"2026-09-22","name":"Доставка еды","amount":-520,"category":"Кафе и доставка"},
                   {"date":"2026-09-19","name":"Кроссовки","amount":-4200,"category":"Прочее"},
                   {"date":"2026-09-15","name":"Перевод от родителей","amount":10000,"category":"Доход"},
                   {"date":"2026-09-10","name":"Стипендия","amount":3200,"category":"Доход"},
                   {"date":"2026-09-05","name":"Общежитие","amount":-1800,"category":"Обязательное"},
                   {"date":"2026-09-03","name":"Связь","amount":-400,"category":"Обязательное"},
                   {"date":"2026-09-01","name":"Подписка на музыку","amount":-200,"category":"Обязательное"} ] } },
  "danya": { "who": "Даня · 2 курс · подработка курьером", "title": "Даня", "subtitle": "доход без графика — прогноз в двух вариантах",
    "situation": { "today": "2026-09-27", "balance": 5000, "daily": 280,
      "incomes": [ {"id":"i1","name":"Подработка курьером","amount":4000,"date":"2026-10-03","confirmed":false},
                   {"id":"i2","name":"Стипендия","amount":2800,"date":"2026-10-20","confirmed":true} ],
      "obligations": [ {"id":"o1","name":"Проездной","amount":900,"date":"2026-09-30"},
                       {"id":"o2","name":"Связь","amount":350,"date":"2026-10-02"},
                       {"id":"o3","name":"Подписка на кино","amount":150,"date":"2026-10-08"} ],
      "spends": [],
      "goal": {"name":"Билет домой на Новый год","target":12000,"current":3000,"date":"2026-12-20"},
      "categories": [ {"name":"Еда","per_day":170},{"name":"Кафе и доставка","per_day":50},
                      {"name":"Транспорт","per_day":30},{"name":"Прочее","per_day":30} ],
      "history": [ {"date":"2026-09-25","name":"Подработка курьером","amount":2600,"category":"Доход"},
                   {"date":"2026-09-23","name":"Кафе с друзьями","amount":-1900,"category":"Кафе и доставка"},
                   {"date":"2026-09-20","name":"Стипендия","amount":2800,"category":"Доход"},
                   {"date":"2026-09-18","name":"Продукты","amount":-760,"category":"Еда"},
                   {"date":"2026-09-11","name":"Подработка курьером","amount":1500,"category":"Доход"},
                   {"date":"2026-09-08","name":"Подписка на кино","amount":-150,"category":"Обязательное"},
                   {"date":"2026-09-02","name":"Связь","amount":-350,"category":"Обязательное"} ] } }
}
```

**13 эталонных проверок** (значения проверены в прототипе; `pytest` и `/api/checks` обязаны давать ровно их):

| # | Ситуация | Ожидаем |
|---|---|---|
| 1 | Аня без покупок | `min = 600`, `min_date = 2026-10-09`, `state = tight`, next_income «Стипендия», 13 дней |
| 2 | Аня: покупка 3 000 сегодня | `first_negative = 2026-10-05`, `max_deficit = 2400`, `earliest_safe = 2026-10-15`, reduce `185 ₽/день`, `until = 2026-10-14`, `days = 18` |
| 3 | Аня: покупка 1 000 сегодня (сумма от жюри) | `first_negative = 2026-10-08`, `max_deficit = 400`, `earliest_safe = 2026-10-10`, reduce `31` |
| 4 | Пусто: balance 0, daily 300, без поступлений | `first_negative = 2026-09-27`, `state = no_income` |
| 5 | balance = −500 | ошибка `field = balance` |
| 6 | Аня, дата стипендии 2026‑09‑20 | ошибка `incomes[0].date` |
| 7 | Аня: покупка 6 900 сегодня | `first_negative = 2026-09-27` |
| 8 | balance 1000, daily 100, 30.09: доход +2000 и платёж −3000 | `first_negative = 2026-09-30`, `first_negative_amount = 400` |
| 9 | Аня: покупка 50 000 | `earliest_safe = null` |
| 10 | Даня | base `min = 1160` (2026‑10‑19), `state = depends`; pessimistic `first_negative = 2026-10-09`, `max_deficit = 2840` |
| 11 | Аня + разовая трата «Такси» 800 сегодня | `min = −200`, reduce `16 ₽/день` |
| 12 | Цель Ани без покупки | `monthly_surplus = 1800`, `eta = 2027-06-04`, `late_days = 3` |
| 13 | Цель Ани с покупкой 3 000 | `eta_with_purchase = 2027-07-24`, `shift_days = 50` |

## 9. AI: как устроен `/api/chat` (детали — в файле B)

```
сообщение ─▶ [1] NLU: НАША МОДЕЛЬ → намерение + уверенность (0…1)
            │    parse.py (правила) → сумма, дата, название
            │    уверенность < 0.6 → правила; правила не уверены → «уточни»
            ├▶ [2] ВЫПОЛНЕНИЕ: функции движка A → facts (готовые строки)
            ├▶ [3] ПОЯСНЕНИЕ: шаблон (по умолчанию), наша модель или готовый API — перефразировать facts
            └▶ [4] GUARD: число/дата в тексте API не из facts → берём шаблон
```

**Метки модели (12 намерений, `app/ai/nlu/labels.py`, менять только через чат):**
`purchase_check`, `forecast`, `explain`, `deficit_plan`, `categories`, `term`, `add_spend`, `add_income`, `invest_advice`, `credentials`, `money_operation`, `off_topic`.

Как метки превращаются в ответ (`ChatResponse.intent`): `add_spend`/`add_income` → `add_entry`; `invest_advice` → `invest_info` (вежливый отказ + карточка обучения); `credentials`/`money_operation` → `refusal`; нет суммы там, где она нужна → `clarify`.

**Своя модель:** обучаем классификатор на синтетическом датасете (~2 000 фраз, 12 классов). Проверяем на отложенных фразах, которые написали **другие участники команды**, не видевшие обучающих данных. Метрики и матрица ошибок — в `docs/ai/model_card.md` и на слайде.
**Вторая модель — генеративный пояснитель:** обучили генеративную модель-объяснитель (`Vikhr-Qwen-2.5-1.5B-Instruct`, QLoRA, 7 220 примеров), но **на проде она выключена по умолчанию (`EXPLAIN_MODE=templates`), доступна локально флагом `EXPLAIN_MODE=local`**.
Она не считает — переписывает числа из facts, и каждое проверяет guard. Нет весов, видеокарты или времени — чат сам переходит на шаблоны.
**Демо обязано работать при `NLU_MODE=sklearn` и `EXPLAIN_MODE=templates` — без интернета и ключей.**

## 10. Таймлайн команды (время Красноярска)

| Когда | Что | Результат |
|---|---|---|
| **16:40–17:10** | **Тимлид (C)** создаёт репозиторий через Claude Code: docs, CLAUDE.md, скелет backend и frontend, пуш в `main` (промпт — в файле C). Остальные в это время читают свой файл целиком. B уже начинает датасет (репо не нужен) | репо в `main` |
| 17:10–17:20 | Все клонируют, поднимают backend и frontend | у всех запускается |
| 17:20–19:00 | Блок 1 | A: модели + движок + 13 тестов; **фикстуры к 18:30**. B: правила + датасет v1 + модель sklearn. C: каркас, стартовый и главный экран на фикстурах. D: personas.json, knowledge.json, деплой «hello» обоих сервисов, CI |
| **19:00** | **Чекпоинт 1** (15 мин) | 13/13 локально; фронт рисует Аню из фикстур; два URL на Render; A и D отдают B свои тестовые фразы |
| 19:00–21:30 | Блок 2 | A: все эндпоинты кроме чата. B: `/api/chat` на sklearn + фикстуры чата; старт обучения нейросети. C: подключение к API, BuyCard, TypesCard, график. D: полный деплой из `main`, исследование, опрос |
| **21:30** | **Чекпоинт 2** | **на проде:** Аня → проверка покупки 3 000 → «с 15 октября» |
| 21:30–00:30 | Блок 3 | B: нейросеть → ONNX; **в 23:00 решение: onnx или sklearn в проде**. C: чат, «Как посчитали?», добавление, анкета. A: крайние случаи. D: черновик презентации, README |
| **00:30** | **Чекпоинт 3** | весь путь раздела 11 на проде, чат работает |
| 00:30–03:00 | Блок 4 | C: Даня, обучение, полировка. **A помогает C** (Checks, JobsModal, LearnModal — через PR). B: разбор ошибок модели, model card. D: слайды v1 |
| 03:00–07:00 | **Сон** (минимум 3,5 часа каждому; можно сменами) | — |
| 07:00–08:30 | Блок 5 | только баги из списка тимлида |
| **08:30** | **Фича‑фриз.** Новые функции запрещены | — |
| 08:30–10:00 | QA на проде (тимлид ведёт, D помогает), фиксы | — |
| 10:00–10:40 | Чистка репо, README, финальный деплой, тег `v1.0` | — |
| 10:40–11:00 | 2 репетиции демо | — |
| **11:00** | **Стоп‑код** | — |

Созвоны на чекпоинтах — стоя, 15 минут, ведёт тимлид: что готово, что блокирует, что меняем.

## 11. Демо для жюри (≈ 1,5 минуты) — всё это должно работать на проде

1. Старт → «Демо: студентка Аня» → «До стипендии **13 дней**. Хватит впритык: к 9 октября останется **600 ₽**».
2. В верхнем блоке: «Наушники», 3000, сегодня → «Когда можно купить?» → карточка: **«Без минуса можно купить с 15 октября»**, минус с 5 октября до 2 400 ₽, цель сдвинется на 50 дней, три варианта выхода.
3. Жюри называет сумму (например, 1 000) → пересчёт вживую: минус с 8 октября, безопасно с 10 октября.
4. «Как посчитали?» → меняем 300 → 250 ₽ в день → график и ответ меняются на глазах.
5. Блок «Постоянное и разовое» → Даня: пунктир и «если подработки не будет — минус с 9 октября».
6. Чат: «Куда вложить 5000?» → вежливый отказ + карточка «Как устроены накопления и инвестиции?». В сообщении видно: «модель: invest_advice · 97%» — это наша обученная модель.
7. «Как мы проверяли» → **13/13**.
