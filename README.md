# Дотяну

AI-помощник для студентов: понимает, хватит ли денег до стипендии и когда можно купить что-то без минуса (кейс 1 Т-Банка, хакатон «Пятый элемент»).

Роли: A — движок и API · B — AI, своя модель · C — фронтенд и тимлид · D — данные, деплой, исследование.

Документы: [CLAUDE.md](CLAUDE.md) · [docs/CONTRACT.md](docs/CONTRACT.md) · [docs/plans/](docs/plans/)

## Запуск

```powershell
# backend
cd backend; python -m venv .venv; .venv\Scripts\Activate.ps1; pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# frontend (второй терминал)
cd frontend; npm install; npm run dev
```

> README дописывает роль D.
