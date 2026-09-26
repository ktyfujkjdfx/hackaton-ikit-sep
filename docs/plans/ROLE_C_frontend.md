# Роль C — Тимлид + фронтенд

> Команда «Дотяну» · 4 человека · 26–27 сентября 2026 · стоп‑код 11:00 (Красноярск).
> Роли: A — движок и API · B — AI (своя модель) · C — фронтенд и тимлид · D — данные, деплой, исследование. Общая часть в конце каждого файла одинакова.

> Твой личный план. Сначала прочитай свою часть, потом общую часть ниже.
> У тебя две шляпы: **тимлид** (репозиторий, договор, чекпоинты, баги, финальная проверка, демо) и **фронтенд** (жюри увидит только твою работу).
> Правило для себя: тимлидские дела занимают не больше 15 минут в час, остальное время — фронт.

---

## ЧАСТЬ 1. ТИМЛИД

### C.1 Час 0 (16:40–17:10): создаёшь репозиторий, пока остальные читают свои файлы

1. На GitHub создай **public** репозиторий `hackaton-ikit-sep` (иначе жюри не откроет) и добавь троих как collaborators.
2. Положи в пустую папку проекта 4 файла `ROLE_*.md` и `prototype.html`.
3. Открой в ней Claude Code и дай промпт:

```
Это старт репозитория hackaton-ikit-sep для хакатона. В папке лежат 4 плана ролей (ROLE_*.md)
и прототип prototype.html. Общая часть (разделы 1–11) во всех 4 файлах одинакова — это договор команды.
Сделай:
1. Проверь, что общая часть во всех 4 файлах совпадает слово в слово. Если нет — покажи отличия и остановись.
2. Разложи файлы:
   docs/plans/ROLE_A_engine_api.md, ROLE_B_ai.md, ROLE_C_frontend.md, ROLE_D_data_devops_pitch.md;
   docs/CONTRACT.md — только общая часть: от последней строки «---» перед заголовком общей части до конца файла;
   docs/prototype.html.
3. Создай CLAUDE.md (текст ниже) и .gitignore:
   .env, .venv/, __pycache__/, *.pyc, node_modules/, dist/, .DS_Store, *.log, training/runs/, training/.cache/
4. Создай скелет строго по разделам 2–3 CONTRACT.md, без лишнего:
   backend/: requirements.txt (fastapi, uvicorn[standard], pydantic>=2, python-dotenv, pytest, httpx);
   app/main.py с GET /api/health {"ok": true, "nlu": env NLU_MODE or "sklearn", "explain": env EXPLAIN_MODE or "templates"},
   CORSMiddleware с allow_origins из env CORS_ORIGINS (через запятую, по умолчанию http://localhost:5173);
   пустые APIRouter(prefix="/api") в app/api/routes.py и app/api/chat.py, подключённые в main;
   пустые пакеты app/engine/, app/ai/, app/ai/nlu/, app/data/; tests/test_health.py; .env.example по разделу 2.
   training/: пустой README.md и requirements-train.txt (torch, transformers, scikit-learn, onnx, onnxruntime, tokenizers, pandas, matplotlib).
   frontend/: Vite react-ts (npm create vite@latest frontend -- --template react-ts), в vite.config.ts proxy '/api' → http://localhost:8000;
   src/api/client.ts с базовым URL import.meta.env.VITE_API_URL ?? '' и одной функцией health().
5. Проверь, что backend запускается (uvicorn) и pytest зелёный, а frontend собирается (npm run build).
6. Сделай один коммит «bootstrap: docs, contract, skeleton» и запушь в main.
Docker не используем. Ничего сверх этого не пиши.
Текст CLAUDE.md:
<вставь блок C.2>
```
4. Проверь на GitHub, что всё на месте, и напиши в чат: **«Репо готово, клонируем. Читать: CLAUDE.md, docs/CONTRACT.md, docs/plans/ROLE_<твоя>.md»**.
5. После того как D настроит CI (≈19:00): Settings → Branches → защити `main` (require PR + status checks).

### C.2 Текст `CLAUDE.md`

```markdown
# Дотяну — AI-помощник для студентов (кейс 1 Т-Банка)
Договор команды: docs/CONTRACT.md — читать перед любой задачей. План своей роли: docs/plans/ROLE_*.md.
Эталон UI, текстов и формул: docs/prototype.html.

## Железные правила
- Все суммы, даты и остатки считает только backend/app/engine. Модель AI, шаблоны и фронт не считают.
- Схемы и имена полей API — строго по docs/CONTRACT.md, раздел 6. Изменить контракт — только PR в CONTRACT.md + сообщение в чат команды.
- Пиши только в папки своей роли (раздел 3 CONTRACT.md). Чужие папки не трогай.
- Только синтетические данные. Никаких ключей, .env и паролей в git.
- Каждая функция движка — с тестом; эталонные значения — раздел 8 CONTRACT.md.
- Docker не используем. Деплой — Render (render.yaml).

## Команды (Windows PowerShell)
backend:  cd backend; .venv\Scripts\Activate.ps1; uvicorn app.main:app --reload --port 8000; pytest
frontend: cd frontend; npm run dev; npm run build

## Стиль
Интерфейс — простым русским языком, тексты берём из прототипа. Коммиты маленькие и понятные.
Без print/console.log и закомментированного кода в main.
```

### C.3 Твои тимлидские обязанности по ходу ночи

| Когда | Что |
|---|---|
| 19:00 / 21:30 / 00:30 | Ведёшь чекпоинт 15 минут: каждый — готово / блокирует / что дальше. Сверяешь с таймлайном (раздел 10). Отстающую задачу режешь или переносишь, не ждёшь |
| весь вечер | Список багов в GitHub Issues: метка роли (`A`, `B`, `C`, `D`), приоритет `P0` (ломает демо) или `P1` |
| 23:00 | Принимаешь от B решение «onnx или sklearn» |
| 00:30 | Отдаёшь A простые компоненты фронта: `Checks.tsx`, `JobsModal.tsx`, `LearnModal.tsx` (A делает PR, ты ревьюишь) |
| 01:00 | Черновая репетиция демо (раздел 11) с D |
| 08:30 | Объявляешь фича‑фриз |
| 08:30–10:00 | Финальная проверка (C.9), баги раздаёшь владельцам |
| 10:40 | Две репетиции демо; ты показываешь, D говорит |

### C.4 Ответы на вопросы жюри (подготовь к 03:00, по 2–3 предложения)
- **Чем вы отличаетесь от аналитики трат в приложении банка?** Там показано прошлое. У нас — дата, когда покупка не уведёт в минус, разделение постоянных и разовых денег и прозрачный расчёт с правкой любой цифры.
- **Где тут AI, если всё считает код?** Наша обученная модель понимает, что спрашивает студент (12 намерений, метрика на фразах, которые модель не видела), и превращает фразу в вызов расчёта. Считать деньги нейросети нельзя — это правило кейса и здравый смысл.
- **Почему не своя LLM?** За сутки её не обучить, и она бы галлюцинировала числа. Мы обучили то, что нужно продукту, — понимание запроса.
- **Почему пользователь будет вводить данные руками?** 5 вопросов за 2 минуты и никакой истории не нужно. Интеграция с банком — следующий шаг.
- **Что если модель ошибётся?** Если она не уверена, работают правила или вопрос‑уточнение. Числа всё равно из движка, AI ничего не решает молча: перед сохранением траты пользователь её подтверждает.
- **Зачем это Т‑Банку?** Проверку «когда можно купить» можно встроить в ассистента банка. Это удержание молодых клиентов и финансовая грамотность.
- **Персональные данные?** Сервер ничего не хранит, только синтетика.

---

## ЧАСТЬ 2. ФРОНТЕНД

### C.5 Твоя зона за 30 секунд
- Папка: `frontend/` целиком. A помогает с 00:30 через PR.
- Стек: React 18 + TypeScript + Vite, **чистый CSS** (токены из прототипа), без UI‑библиотек, без роутера (экраны переключаются состоянием), без стейт‑менеджеров (useReducer + context).
- **Фронт ничего не считает.** Любое число (остаток, минус, дата, сдвиг цели, «до стипендии N дней», итог «в месяц») приходит из `/api/dashboard`, `/api/purchase/check` или `/api/chat`. Ты только форматируешь (`rub()`, `fd()`) и рисуешь.
- Эталон вёрстки, текстов и поведения — `docs/prototype.html`. Открой его рядом и переноси блок за блоком; CSS‑токены и классы можно брать почти как есть.

### C.6 Зависимости
| От кого | Что | Когда |
|---|---|---|
| A | `models.py` → ты делаешь `src/types.ts` (зеркало разделов 5–6) | 17:50 |
| A | фикстуры `src/api/fixtures/*.json` | 18:30 (до этого пиши мок по примерам раздела 6) |
| A | живые эндпоинты | 21:00 |
| B | фикстуры `chat_*.json` | 20:00 |
| B | живой `/api/chat` | 21:30 |
| D | Static Site на Render собирает `frontend/` из `main` | 19:00 |

### C.7 Структура, состояние, компоненты

```
frontend/src/
├─ main.tsx  App.tsx                 // экраны: 'start' | 'form' | 'app' | 'checks'
├─ styles/tokens.css  app.css        // из <style> прототипа (светлая и тёмная тема)
├─ types.ts                          // зеркало контракта
├─ api/client.ts                     // fetch(VITE_API_URL + '/api/...'), режим моков VITE_USE_MOCKS=1
├─ api/fixtures/*.json               // генерируют A и B (руками не редактировать)
├─ state/store.tsx                   // useReducer
├─ lib/format.ts                     // rub(), fd(), fdShort(), daysWord() — как в прототипе
├─ screens/Start.tsx  Form.tsx  Dashboard.tsx  Checks.tsx
└─ components/ TopBar Hero InlineBuy BuyCard DeficitPlan BalanceChart TypesCard Upcoming
               Categories GoalCard LearnCard History Deferred AskPanel ChatMessage
               ExplainDrawer AddModal JobsModal LearnModal Modal Tag
```

```ts
type State = {
  screen: 'start'|'form'|'app'|'checks';
  who: string;
  situation: Situation | null;      // данные пользователя живут только тут
  purchase: Purchase | null;        // активная проверяемая покупка
  deferred: {name:string; amount:number; safe_date:string}[];
  messages: ChatMsg[];              // {role:'user', text} | {role:'bot', resp: ChatResponse}
  dashboard: Dashboard | null;
  loading: boolean;
  error: string | null;
};
```
- **Любое изменение `situation` или `purchase` → `POST /api/dashboard`** с debounce 250 мс; предыдущий запрос отменяй через AbortController. Пока идёт загрузка, показывай старые данные чуть прозрачнее, без мигания.
- Ответ 422 → ошибки у полей (анкета, «Как посчитали?», AddModal). Сеть упала → баннер «Сервер недоступен — расчёт не выполнен» и кнопка «Повторить». **Ничего не досчитывай сам.**
- Бесплатный Render засыпает: первый запрос может идти до 50 с. Показывай «Просыпаемся… это займёт до минуты», а не ошибку.
- Чат: `POST /api/chat` с `situation`, `purchase` и последними 6 сообщениями. В ответе есть `purchase` → `setPurchase` (появятся BuyCard и вторая линия на графике). Есть `proposed_entry` → карточка подтверждения: «Сохранить» (добавить в `spends` или `incomes`, `id = crypto.randomUUID()`) и «Исправить» (AddModal с заполненными полями).

| Компонент | Данные | Что важно (всё есть в прототипе) |
|---|---|---|
| Start | `/api/personas` | блок 4 фишек, 3 карточки: Аня / анкета / Даня; «Учебный режим…» |
| TopBar | — | «Демо: 27 сентября 2026», чип `who`; кнопки: Как посчитали? · Учиться · Как мы проверяли · Сменить профиль |
| Hero | `headline`, `scenarios.pessimistic` | 5 состояний с текстами из прототипа; для `depends` — два блока «если будет / если не будет»; строка «Это прогноз, а не гарантия…»; кнопка «Что у меня постоянное?» скроллит к TypesCard |
| InlineBuy | локальная форма | метка «Главная фишка»; что, цена, дата (от today до today+29); submit → `setPurchase`, сообщение в чат, scroll к BuyCard |
| BuyCard | `dashboard.purchase` | жёлтая плашка «Без минуса можно купить с …» или зелёная «Можно сейчас»; 3 факта; DeficitPlan в 3 колонки; кнопки: Отложить / Как посчитали? / Убрать покупку |
| BalanceChart | `scenarios`, `events` | порт `drawChart`: сетка, красная зона ниже нуля, красный участок линии в минусе, жёлтый коридор между основной и пессимистичной линией, маркеры (▲ доход, пустой ▲ — непостоянный, ● платёж, ○ разовая трата), подпись минимума, тултип, легенда |
| TypesCard | `money_types` | 4 блока (зелёный / жёлтый пунктир / серый / пунктир), суммы, списки, «как учитываем», итог «Надёжная часть…»; кнопка «+ Добавить подработку», если нет непостоянного дохода |
| Upcoming | `events` без покупки | метки: постоянный расход / разовая трата / постоянный доход · ожидается / непостоянный · может не прийти |
| Categories | `situation.categories`, `money_types.variable_expenses.total` | полоски; без категорий — «Категории появятся, когда начнёшь добавлять траты» |
| GoalCard + LearnCard | `goal`, `show_learn_card` | прогресс, «≈ N ₽ в месяц (оценка)», дата, отставание, сдвиг от покупки; LearnCard **только если `show_learn_card`** |
| History | `history` | метки «регулярный» и «крупная трата» |
| AskPanel + ChatMessage | `messages` | sticky справа на всю высоту экрана; подсказки одной прокручиваемой строкой; строка **«модель: purchase_check · 94% → check_purchase(3000, 27.09)»** из `nlu` и `tool_calls`; headline с tone; facts; текст с префиксом «Пояснение AI»; source; actions; кнопка «+ Добавить трату или доход» |
| ExplainDrawer | `situation`, `dashboard` | жёлтый блок‑урок; живая сводка; формула словами; таблица с редактированием balance, daily, сумм и дат поступлений и платежей, суммы покупки; «Чего мы не знаем» из `unknowns`; легенда меток |
| AddModal | — | Трата/Доход, название, сумма, дата, надёжность дохода; проверки: сумма > 0, дата не в прошлом |
| JobsModal (A) | `amount` | 3 карточки с меткой «Пример», где искать на самом деле, предупреждение о предоплате |
| LearnModal (A) | — | 3 шага, «учим, а не советуем», плашка о курсе Т‑Банка (точную ссылку даёт D), fincult.info |
| Form (анкета) | `/api/validate` | 5 блоков, пресеты, «Заполнить примером»; ошибки 422 привязываются к полям по `field/index/subfield`; без поступлений пускаем, но в чате бот говорит об ограничении |
| Checks (A) | `/api/checks` | крупный счёт `13/13`, таблица, текст про риски |

### C.8 Фронтенд по часам (вперемешку с тимлидскими делами)

| Время | Задача | Готово, когда |
|---|---|---|
| 16:40–17:10 | бутстрап репо (C.1) | репо в main |
| 17:10–18:30 | токены CSS, `types.ts`, `client.ts` с моками, `format.ts`, Start, TopBar, Hero | Start → Аня → Hero «13 дней» из мока |
| 18:30–19:00 | BalanceChart (порт) на `dashboard_anya.json` | график как в прототипе |
| 19:00 | Чекпоинт 1 (ведёшь) | — |
| 19:00–21:00 | InlineBuy, BuyCard, DeficitPlan (фикстура `buy3000`), TypesCard, Upcoming, Categories, GoalCard, History | главный экран полностью на фикстурах |
| 21:00–21:30 | переход на живой API, debounce, ошибки, «просыпаемся» | реальные ответы |
| 21:30 | Чекпоинт 2 на проде | Аня → 3000 → «с 15 октября» |
| 21:30–00:30 | AskPanel + ChatMessage + proposed_entry; ExplainDrawer с редактированием; AddModal; Form | пункты 1–4 демо |
| 00:30 | Чекпоинт 3; отдать A Checks/Jobs/Learn | — |
| 00:30–03:00 | Даня (depends + коридор), LearnCard, Deferred, тёмная тема, ширины 1280–1920 и 400; ревью PR от A; ответы жюри (C.4) | пункты 5–7 демо |
| 07:00–08:30 | баги P0/P1, полировка | — |
| 08:30–10:00 | финальная проверка (C.9) | — |

### C.9 Финальная проверка на проде (08:30–10:00, ведёшь ты, D помогает)
- [ ] Оба URL открываются в режиме инкогнито; backend разбужен заранее, первый ответ < 5 с
- [ ] Раздел 11 проходит без ошибок 2 раза подряд
- [ ] Все 5 состояний Hero: Аня; Аня + «такси 800»; Даня; анкета без дохода; покупка 3000
- [ ] Анкета: пустая форма → понятные ошибки; «Заполнить примером» → прогноз
- [ ] Чат: 15 фраз B на проде, видны «модель: … %»
- [ ] «Как мы проверяли» = 13/13
- [ ] Тёмная тема, ширины 1366 и 1920; консоль без ошибок
- [ ] Репо: нет `.env`, ключей, `node_modules`, мусора; README актуален; CI зелёный; тег `v1.0`

### C.10 Стартовый промпт для фронта в Claude Code

```
Репозиторий hackaton-ikit-sep. Я — роль C: фронтенд (React 18 + TS + Vite, чистый CSS) и тимлид.
Прочитай CLAUDE.md, docs/CONTRACT.md (разделы 5–6 — типы и API, 11 — демо), docs/plans/ROLE_C_frontend.md
и docs/prototype.html — эталон вида, текстов и поведения. Переноси вёрстку и тексты максимально близко.
Правила:
- Пиши только во frontend/.
- Фронт НИЧЕГО не считает: все суммы и даты — из /api/dashboard, /api/purchase/check, /api/chat.
  Только форматирование (rub, fd) и отрисовка.
- Без UI-библиотек и роутера. Состояние — useReducer + context (схема State в моём плане, C.7).
- Базовый URL API — import.meta.env.VITE_API_URL ?? '' (локально работает прокси Vite).
- CSS-токены и тёмная тема — из <style> прототипа.
Задача сейчас: src/types.ts по разделам 5–6, src/api/client.ts (fetch + режим моков VITE_USE_MOCKS=1
из src/api/fixtures), src/lib/format.ts, экраны Start и Dashboard с Hero. Потом покажи, как запустить.
```
Дальше — по одному компоненту из C.7, например: «Перенеси drawChart из прототипа в BalanceChart.tsx; данные — dashboard.scenarios и events».

### C.11 Ловушки
- Не пересчитывай ничего на фронте, даже «до стипендии N дней» — это `headline.next_income.days`.
- Даты из API — строки `YYYY-MM-DD`. Парсь как локальную дату (`new Date(y, m-1, d)`), а не `new Date("2026-10-05")`: сдвиг UTC даст «4 октября».
- Ключи списков — `id`, не индекс, иначе поля в «Как посчитали?» теряют фокус.
- Панель чата: высота `calc(100vh - 96px)`, у `.msgs` — `min-height: 0`, иначе ответы обрезаются.
- Добавь `[hidden]{display:none!important}` в CSS, иначе скрытые модалки перекрывают клики.
- Кнопка, которая ничего не делает, хуже, чем её отсутствие. Не успеваешь — прячь.

## Чек‑лист C перед стоп‑кодом
- [ ] Финальная проверка C.9 пройдена
- [ ] `npm run build` без ошибок и предупреждений TS
- [ ] Нет `console.log`, закомментированного кода, неиспользуемых компонентов
- [ ] Ответы жюри (C.4) выучены, демо отрепетировано 2 раза

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

**Своя модель:** обучаем свой классификатор намерений (раздел 9) — AI понимает вопрос, код считает.

**Не делаем:** регистрацию и логины, загрузку реальных выписок, MCC, конверты, геймификацию, реальные вакансии, обучение генеративной LLM, Docker, мобильную вёрстку (десктоп‑веб; на телефоне просто не должно ломаться).

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
| AI: пояснение | **шаблоны** по умолчанию; по желанию — готовый API (YandexGPT или Claude Haiku) только для перефразирования, с guard | числа всегда из движка |
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
EXPLAIN_MODE=templates        # templates | yandex | anthropic — чем пишем пояснение
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
            ├▶ [3] ПОЯСНЕНИЕ: шаблон (по умолчанию) или готовый API (перефразировать facts)
            └▶ [4] GUARD: число/дата в тексте API не из facts → берём шаблон
```

**Метки модели (12 намерений, `app/ai/nlu/labels.py`, менять только через чат):**
`purchase_check`, `forecast`, `explain`, `deficit_plan`, `categories`, `term`, `add_spend`, `add_income`, `invest_advice`, `credentials`, `money_operation`, `off_topic`.

Как метки превращаются в ответ (`ChatResponse.intent`): `add_spend`/`add_income` → `add_entry`; `invest_advice` → `invest_info` (вежливый отказ + карточка обучения); `credentials`/`money_operation` → `refusal`; нет суммы там, где она нужна → `clarify`.

**Своя модель:** обучаем классификатор на синтетическом датасете (~2 000 фраз, 12 классов). Проверяем на отложенных фразах, которые написали **другие участники команды**, не видевшие обучающих данных. Метрики и матрица ошибок — в `docs/ai/model_card.md` и на слайде. Генеративную LLM не обучаем: за сутки это невозможно и не нужно — считать всё равно должен код.
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
