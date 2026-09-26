import { useState } from 'react'
import type { Category, Goal, Income, Obligation, Situation, ValidationError } from '../types'
import { dayIndex } from '../lib/dates'
import { useAppDispatch } from '../state/store'
import personaAnya from '../api/fixtures/persona_anya.json'

const TODAY = '2026-09-27'

const OBLIGATION_PRESETS = ['Общежитие', 'Связь', 'Проездной', 'Подписка']
const DAILY_PRESETS = [200, 300, 400, 500]

function emptyIncome(): Income {
  return { id: crypto.randomUUID(), name: '', amount: 0, date: TODAY, confirmed: true }
}
function emptyObligation(): Obligation {
  return { id: crypto.randomUUID(), name: '', amount: 0, date: TODAY }
}

function validate(sit: {
  balance: number | null
  daily: number | null
  incomes: Income[]
  obligations: Obligation[]
  goal: Goal | null
}): ValidationError[] {
  const errors: ValidationError[] = []
  if (sit.balance === null || Number.isNaN(sit.balance)) {
    errors.push({ field: 'balance', index: null, subfield: null, message: 'Укажи сумму на карте (можно 0).' })
  } else if (sit.balance < 0) {
    errors.push({
      field: 'balance',
      index: null,
      subfield: null,
      message: 'Сумма не может быть отрицательной. Если на карте минус по кредитке — укажи 0.',
    })
  }
  sit.incomes.forEach((i, k) => {
    if (!(i.amount > 0)) {
      errors.push({ field: 'incomes', index: k, subfield: 'amount', message: 'Сумма поступления должна быть больше нуля.' })
    }
    if (!i.date) {
      errors.push({ field: 'incomes', index: k, subfield: 'date', message: 'Укажи дату поступления.' })
    } else if (dayIndex(TODAY, i.date) < 0) {
      errors.push({ field: 'incomes', index: k, subfield: 'date', message: 'Дата поступления уже прошла. Укажи следующую.' })
    }
  })
  sit.obligations.forEach((o, k) => {
    if (!(o.amount > 0)) {
      errors.push({ field: 'obligations', index: k, subfield: 'amount', message: 'Сумма платежа должна быть больше нуля.' })
    }
    if (!o.date) {
      errors.push({ field: 'obligations', index: k, subfield: 'date', message: 'Укажи дату платежа.' })
    } else if (dayIndex(TODAY, o.date) < 0) {
      errors.push({ field: 'obligations', index: k, subfield: 'date', message: 'Дата платежа уже прошла.' })
    }
  })
  if (sit.daily === null || Number.isNaN(sit.daily)) {
    errors.push({ field: 'daily', index: null, subfield: null, message: 'Укажи примерные траты в день или выбери диапазон.' })
  } else if (sit.daily < 0) {
    errors.push({ field: 'daily', index: null, subfield: null, message: 'Траты не могут быть отрицательными.' })
  }
  if (sit.goal) {
    const g = sit.goal
    if (!(g.target > 0)) {
      errors.push({ field: 'goal', index: null, subfield: null, message: 'Укажи, сколько нужно на цель.' })
    } else if (!(g.current >= 0)) {
      errors.push({ field: 'goal', index: null, subfield: null, message: 'Сколько уже накоплено — число от 0.' })
    } else if (g.current >= g.target) {
      errors.push({ field: 'goal', index: null, subfield: null, message: 'Цель уже накоплена — убери её или увеличь сумму.' })
    }
    if (!g.date || dayIndex(TODAY, g.date) <= 0) {
      errors.push({ field: 'goal', index: null, subfield: null, message: 'Дата цели должна быть в будущем.' })
    }
  }
  return errors
}

export function Form() {
  const dispatch = useAppDispatch()
  const [balance, setBalance] = useState<string>('')
  const [incomes, setIncomes] = useState<Income[]>([emptyIncome()])
  const [obligations, setObligations] = useState<Obligation[]>([emptyObligation()])
  const [daily, setDaily] = useState<string>('')
  const [goalName, setGoalName] = useState('')
  const [goalTarget, setGoalTarget] = useState('')
  const [goalCurrent, setGoalCurrent] = useState('')
  const [goalDate, setGoalDate] = useState('')
  const [errors, setErrors] = useState<ValidationError[]>([])

  function errorFor(field: string, index: number | null, subfield: string | null) {
    return errors.find((e) => e.field === field && e.index === index && e.subfield === subfield)?.message
  }

  function fillExample() {
    const sit = personaAnya.situation as Situation
    setBalance(String(sit.balance))
    setIncomes(sit.incomes.map((i) => ({ ...i })))
    setObligations(sit.obligations.map((o) => ({ ...o })))
    setDaily(String(sit.daily))
    if (sit.goal) {
      setGoalName(sit.goal.name)
      setGoalTarget(String(sit.goal.target))
      setGoalCurrent(String(sit.goal.current))
      setGoalDate(sit.goal.date)
    }
    setErrors([])
  }

  function submit() {
    const goal: Goal | null = goalName || goalTarget ? {
      name: goalName,
      target: Number(goalTarget),
      current: Number(goalCurrent || 0),
      date: goalDate,
    } : null

    const draft = {
      balance: balance === '' ? null : Number(balance),
      daily: daily === '' ? null : Number(daily),
      incomes,
      obligations,
      goal,
    }
    const found = validate(draft)
    setErrors(found)
    if (found.length > 0) return

    const categories: Category[] | null = null
    const situation: Situation = {
      today: TODAY,
      balance: Number(balance),
      daily: Number(daily),
      incomes,
      obligations,
      spends: [],
      goal,
      categories,
      history: [],
    }
    dispatch({ type: 'LOAD_PERSONA_START', personaId: 'custom' })
    dispatch({ type: 'LOAD_PERSONA_DONE', personaId: 'custom', who: 'Твоя анкета', situation })
    dispatch({ type: 'GO', screen: 'app' })
  }

  return (
    <section id="form">
      <header className="topbar">
        <div className="wrap">
          <div className="brand">
            <span className="brand-mark">₽</span>Дотяну
          </div>
          <span className="demo-chip">Демо: 27 сентября 2026</span>
          <span className="spacer" />
          <button className="btn ghost sm" type="button" onClick={() => dispatch({ type: 'GO', screen: 'start' })}>
            ← На старт
          </button>
        </div>
      </header>
      <div className="wrap">
        <div>
          <h2 style={{ fontFamily: 'var(--display)', fontSize: 26 }}>Анкета</h2>
          <p className="sub" style={{ color: 'var(--muted)', marginTop: 4 }}>
            Всё, что мы не знаем точно, пометим как оценку. Ничего не отправляется в банк.
          </p>
        </div>
        <div style={{ display: 'grid', gap: 16 }}>
          <div className="fblock">
            <h3>1. Сколько сейчас денег на карте?</h3>
            <label className="f" style={{ maxWidth: 220 }}>
              Сумма, ₽
              <input
                type="number"
                inputMode="numeric"
                placeholder="например, 6900"
                value={balance}
                onChange={(e) => setBalance(e.target.value)}
              />
            </label>
            <div className="errmsg">{errorFor('balance', null, null)}</div>
          </div>

          <div className="fblock">
            <h3>2. Когда придут деньги?</h3>
            <p className="hint">
              «Точно придёт» — постоянный доход по графику: стипендия, деньги от родителей. «Может не прийти» —
              разовый или нерегулярный: подработка, подарок.
            </p>
            <div style={{ display: 'grid', gap: 8 }}>
              {incomes.map((inc, k) => (
                <div className="frow" key={inc.id}>
                  <label className="f">
                    Название
                    <input
                      type="text"
                      value={inc.name}
                      onChange={(e) =>
                        setIncomes((list) => list.map((x, i) => (i === k ? { ...x, name: e.target.value } : x)))
                      }
                    />
                  </label>
                  <label className="f">
                    Сумма, ₽
                    <input
                      type="number"
                      className={errorFor('incomes', k, 'amount') ? 'err' : ''}
                      value={inc.amount || ''}
                      onChange={(e) =>
                        setIncomes((list) =>
                          list.map((x, i) => (i === k ? { ...x, amount: Number(e.target.value) } : x)),
                        )
                      }
                    />
                  </label>
                  <label className="f">
                    Дата
                    <input
                      type="date"
                      className={errorFor('incomes', k, 'date') ? 'err' : ''}
                      value={inc.date}
                      onChange={(e) =>
                        setIncomes((list) => list.map((x, i) => (i === k ? { ...x, date: e.target.value } : x)))
                      }
                    />
                  </label>
                  <label className="f">
                    Надёжность
                    <select
                      value={inc.confirmed ? 'yes' : 'no'}
                      onChange={(e) =>
                        setIncomes((list) =>
                          list.map((x, i) => (i === k ? { ...x, confirmed: e.target.value === 'yes' } : x)),
                        )
                      }
                    >
                      <option value="yes">Точно придёт</option>
                      <option value="no">Может не прийти</option>
                    </select>
                  </label>
                  <button
                    type="button"
                    className="x"
                    onClick={() => setIncomes((list) => list.filter((_, i) => i !== k))}
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>
            <div>
              <button type="button" className="btn sm" onClick={() => setIncomes((l) => [...l, emptyIncome()])}>
                + Ещё поступление
              </button>
            </div>
            <div className="errmsg">{errorFor('incomes', null, null)}</div>
          </div>

          <div className="fblock">
            <h3>3. Обязательные платежи в ближайший месяц</h3>
            <p className="hint">Постоянные расходы с датой: общежитие, связь, проезд, подписки.</p>
            <div className="presets">
              {OBLIGATION_PRESETS.map((name) => (
                <button
                  key={name}
                  type="button"
                  className="btn sm"
                  onClick={() =>
                    setObligations((l) => [...l, { id: crypto.randomUUID(), name, amount: 0, date: TODAY }])
                  }
                >
                  + {name}
                </button>
              ))}
            </div>
            <div style={{ display: 'grid', gap: 8 }}>
              {obligations.map((ob, k) => (
                <div className="frow ob" key={ob.id}>
                  <label className="f">
                    Название
                    <input
                      type="text"
                      value={ob.name}
                      onChange={(e) =>
                        setObligations((list) => list.map((x, i) => (i === k ? { ...x, name: e.target.value } : x)))
                      }
                    />
                  </label>
                  <label className="f">
                    Сумма, ₽
                    <input
                      type="number"
                      className={errorFor('obligations', k, 'amount') ? 'err' : ''}
                      value={ob.amount || ''}
                      onChange={(e) =>
                        setObligations((list) =>
                          list.map((x, i) => (i === k ? { ...x, amount: Number(e.target.value) } : x)),
                        )
                      }
                    />
                  </label>
                  <label className="f">
                    Дата
                    <input
                      type="date"
                      className={errorFor('obligations', k, 'date') ? 'err' : ''}
                      value={ob.date}
                      onChange={(e) =>
                        setObligations((list) => list.map((x, i) => (i === k ? { ...x, date: e.target.value } : x)))
                      }
                    />
                  </label>
                  <button
                    type="button"
                    className="x"
                    onClick={() => setObligations((list) => list.filter((_, i) => i !== k))}
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>
            <div>
              <button type="button" className="btn sm" onClick={() => setObligations((l) => [...l, emptyObligation()])}>
                + Ещё платёж
              </button>
            </div>
            <div className="errmsg">{errorFor('obligations', null, null)}</div>
          </div>

          <div className="fblock">
            <h3>4. Сколько в среднем тратишь в день на еду и мелочи?</h3>
            <p className="hint">
              Разовые траты (такси, кафе) сюда входят в среднем. Если не знаешь — прикинь, мы пометим это как оценку.
            </p>
            <div className="presets">
              {DAILY_PRESETS.map((v) => (
                <button key={v} type="button" className="btn sm" onClick={() => setDaily(String(v))}>
                  {v} ₽
                </button>
              ))}
            </div>
            <label className="f" style={{ maxWidth: 220 }}>
              ₽ в день
              <input
                type="number"
                inputMode="numeric"
                placeholder="например, 300"
                value={daily}
                onChange={(e) => setDaily(e.target.value)}
              />
            </label>
            <div className="errmsg">{errorFor('daily', null, null)}</div>
          </div>

          <div className="fblock">
            <h3>
              5. Копишь на что-то? <span className="chip">можно пропустить</span>
            </h3>
            <div className="frow goal">
              <label className="f">
                Цель
                <input type="text" value={goalName} onChange={(e) => setGoalName(e.target.value)} placeholder="Ноутбук" />
              </label>
              <label className="f">
                Нужно, ₽
                <input type="number" value={goalTarget} onChange={(e) => setGoalTarget(e.target.value)} placeholder="40000" />
              </label>
              <label className="f">
                Уже есть, ₽
                <input type="number" value={goalCurrent} onChange={(e) => setGoalCurrent(e.target.value)} placeholder="25000" />
              </label>
              <label className="f">
                К дате
                <input type="date" value={goalDate} onChange={(e) => setGoalDate(e.target.value)} />
              </label>
            </div>
            <div className="errmsg">{errorFor('goal', null, null)}</div>
          </div>

          <div className="form-actions">
            <button type="button" className="btn primary lg" onClick={submit}>
              Посчитать
            </button>
            <button type="button" className="btn" onClick={fillExample}>
              Заполнить примером
            </button>
          </div>
        </div>
      </div>
    </section>
  )
}
