# ФинКом — AI-помощник для студентов (кейс 1 Т-Банка)
Договор команды: docs/CONTRACT.md — читать перед любой задачей. План своей роли: docs/plans/ROLE_*.md.
Эталон UI, текстов и формул: docs/prototype.html.

## Роли и ветки
A — движок и API (ветка dev/a-engine) · B — AI, своя модель (dev/b-ai) ·
C — фронтенд и тимлид (dev/c-frontend) · D — данные, деплой, исследование (dev/d-data).
Работай только в ветке своей роли или в коротких ветках от неё. В main — только через Pull Request.

## Железные правила
- Все суммы, даты и остатки считает только backend/app/engine. Модель AI, шаблоны и фронт не считают.
- Схемы и имена полей API — строго по docs/CONTRACT.md, раздел 6. Изменить контракт — только PR в CONTRACT.md + сообщение в чат команды.
- Пиши только в папки своей роли (раздел 3 CONTRACT.md). Чужие папки не трогай.
- Только синтетические данные. Никаких ключей, .env и паролей в git.
- Каждая функция движка — с тестом; эталонные значения — раздел 8 CONTRACT.md.
- Docker не используем. Сейчас сервис поднимается локально; публикация — за реверс-прокси на VDS (см. README).

## Команды (Windows PowerShell)
backend:  cd backend; python -m venv .venv; .venv\Scripts\Activate.ps1; pip install -r requirements.txt
          uvicorn app.main:app --reload --port 8000; pytest
frontend: cd frontend; npm install; npm run dev; npm run build
Перед началом работы: git checkout <своя ветка>; git pull; git merge origin/main

## Стиль
Интерфейс — простым русским языком, тексты берём из прототипа. Коммиты маленькие и понятные.
Без print/console.log и закомментированного кода в main.
