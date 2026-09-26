# Дотяну

AI-помощник для студентов первого года самостоятельной жизни: показывает, хватит ли денег до стипендии, и отвечает не «хватит ли», а **когда можно купить без минуса**.
Кейс 1 Т-Банка «AI в личных финансах», стартап-хакатон «Пятый элемент» (СФУ).
Все суммы и даты считает код, AI только понимает вопрос и объясняет ответ.

**Сайт:** https://dotyanu.onrender.com · **API:** https://dotyanu-api.onrender.com ([документация /docs](https://dotyanu-api.onrender.com/docs))

> Бесплатный сервер на Render засыпает после ~15 минут простоя, и первый запрос может идти до минуты.
> Откройте https://dotyanu-api.onrender.com/api/health и дождитесь `{"ok": true, ...}`.

Роли: A — движок и API · B — AI, своя модель · C — фронтенд и тимлид · D — данные, деплой, исследование.
Документы: [CLAUDE.md](CLAUDE.md) · [docs/CONTRACT.md](docs/CONTRACT.md) · [docs/checks.md](docs/checks.md) · [docs/ai/model_card.md](docs/ai/model_card.md)

## Как запустить локально

Нужны Python 3.11 и Node.js 20. Docker не нужен.

**Windows (PowerShell)**

```powershell
# backend — первый терминал
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --port 8000

# frontend — второй терминал
cd frontend
npm install
npm run dev
```

**macOS / Linux (bash)**

```bash
# backend — первый терминал
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000

# frontend — второй терминал
cd frontend
npm install
npm run dev
```

Откройте http://localhost:5173. Запросы `/api` фронт сам проксирует на `localhost:8000`, поэтому `VITE_API_URL` локально оставляем пустым.
Документация API: http://localhost:8000/docs.

**Тесты:** `cd backend` и `pytest` — в том числе 13 эталонных сценариев из [docs/checks.md](docs/checks.md).
**Сборка фронта:** `cd frontend` и `npm run build`.

**Переменные окружения** (`backend/.env`, в git лежит только `.env.example`):

| Переменная | По умолчанию | Что значит |
|---|---|---|
| `NLU_MODE` | `sklearn` | чем понимаем вопрос: `onnx` / `sklearn` / `rules` |
| `NLU_MIN_CONFIDENCE` | `0.6` | ниже этой уверенности модели переходим на правила |
| `EXPLAIN_MODE` | `templates` | чем пишем пояснение: `templates` / `yandex` / `anthropic` |
| `DEMO_TODAY` | `2026-09-27` | «сегодня» для демо |
| `CORS_ORIGINS` | `http://localhost:5173` | с каких адресов фронт может ходить в API |

Демо полностью работает без интернета и ключей: `NLU_MODE=sklearn`, `EXPLAIN_MODE=templates`.

## Пример входных данных

Демо-персоны лежат в [backend/app/data/personas.json](backend/app/data/personas.json). Все данные синтетические.
Ситуация студентки Ани (сокращено: без истории операций и категорий трат):

```json
{
  "today": "2026-09-27",
  "balance": 6900,
  "daily": 300,
  "incomes": [
    { "id": "i1", "name": "Стипендия", "amount": 3200, "date": "2026-10-10", "confirmed": true },
    { "id": "i2", "name": "Перевод от родителей", "amount": 10000, "date": "2026-10-15", "confirmed": true }
  ],
  "obligations": [
    { "id": "o1", "name": "Подписка на музыку", "amount": 200, "date": "2026-10-01" },
    { "id": "o2", "name": "Связь", "amount": 400, "date": "2026-10-03" },
    { "id": "o3", "name": "Общежитие", "amount": 1800, "date": "2026-10-05" }
  ],
  "spends": [],
  "goal": { "name": "Ноутбук", "target": 40000, "current": 25000, "date": "2027-06-01" }
}
```

- `balance` — факт: сколько денег сейчас.
- `daily` — оценка: обычные траты в день.
- `incomes` — поступления; `confirmed: true` — точно придёт, `false` — может не прийти (тогда прогноз строится в двух вариантах).
- `obligations` — обязательные платежи на дату; `spends` — разовые траты.
- Суммы — целые рубли, даты — `YYYY-MM-DD`.

Что получится: без покупок минимум **600 ₽ к 9 октября** («впритык»). Наушники за 3 000 ₽ сегодня уведут в минус с 5 октября (до −2 400 ₽), а **без минуса их можно купить с 15 октября**.

Проверить через API:

```bash
curl -s https://dotyanu-api.onrender.com/api/personas/anya
curl -s -X POST https://dotyanu-api.onrender.com/api/purchase/check \
  -H "Content-Type: application/json" \
  -d '{"situation": <situation из ответа выше>, "purchase": {"amount": 3000, "date": "2026-09-27", "name": "Наушники"}}'
```

## Известные ограничения

- **Прогноз на 30 дней.** Что будет позже, мы не показываем и прямо пишем об этом.
- **Обычные траты в день — оценка**, а не факт: среднее по истории или то, что указал пользователь. Необычные будущие траты (подарки, поломки) прогноз не знает.
- **Демо-дата зафиксирована:** «сегодня» = 27 сентября 2026 (`DEMO_TODAY`), чтобы цифры демо всегда совпадали с эталоном.
- **Модель понимания вопросов обучена на синтетических фразах.** На живых формулировках она может ошибаться; при низкой уверенности включаются правила или бот просит уточнить. Метрики — в [docs/ai/model_card.md](docs/ai/model_card.md).
- **Данные не сохраняются.** Нет регистрации и базы: ситуация живёт в браузере и пропадает после закрытия вкладки.
- **Только синтетические данные.** Реальные выписки, счета и карты не подключаются; никаких операций с деньгами.
- **Нет инвестиционных советов.** На вопросы «куда вложить» бот вежливо отказывает и показывает общую обучающую карточку.
- **Десктоп-веб.** На телефоне сайт открывается, но отдельной мобильной вёрстки нет.
- **Бесплатный хостинг:** сервер засыпает после простоя, первый запрос может идти до минуты.
