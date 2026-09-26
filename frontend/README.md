# ФинКом — фронтенд

React 18 + TypeScript + Vite, чистый CSS (без UI-библиотек). Ничего не считает — все суммы и даты приходят из `/api/dashboard`, `/api/purchase/check`, `/api/chat` (описаны в `../docs/CONTRACT.md`).

## Запуск локально (PowerShell)

```powershell
cd frontend
npm install
npm run dev   # http://localhost:5173, /api проксируется на :8000 (см. vite.config.ts)
```

Бэкенд поднимается отдельно (`../backend`, см. корневой `CLAUDE.md`).

## Переменные окружения

`.env` (не в git, см. `.env.example`):

```
VITE_API_URL=       # пусто — работает прокси Vite на localhost:8000
VITE_USE_MOCKS=0    # 1 — брать данные из src/api/fixtures вместо реального бэкенда
```

`.env.production` (в git — там нет секретов, только публичный адрес прод-бэкенда) задаёт `VITE_API_URL` для собранной статики на Render.

## Сборка

```powershell
npm run build   # tsc -b && vite build → dist/
```

## Структура

```
src/
├─ screens/       Start, Form (анкета), Dashboard, Checks
├─ components/    Hero, BalanceChart, TypesCard, BuyCard, InlineBuy, DeficitPlanCards,
│                 ExplainDrawer, AskPanel, ChatMessage, AddModal, TopBar
├─ state/store.tsx  useReducer + context — единственный источник состояния
├─ api/client.ts    fetch к бэкенду + режим моков из api/fixtures
├─ lib/             format.ts (rub/fd/fdShort/daysWord), dates.ts, chatMock.ts
└─ styles/          tokens.css (палитра, см. ../docs/design-system.md), app.css
```

## Прогон вручную

Путь для проверки: Start → демо-профиль или анкета → Dashboard (Hero, график, InlineBuy → BuyCard → план выхода из минуса) → «Как посчитали?» → чат (в т. ч. фразу с кодом из СМС — должен быть вежливый отказ) → «Как мы проверяли» (13/13).
