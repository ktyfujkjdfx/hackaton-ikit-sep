import { useState, type FormEvent } from 'react'
import { addDays, dayIndex } from '../lib/dates'
import { useAppDispatch, useAppState } from '../state/store'

export function InlineBuy() {
  const { situation, purchase } = useAppState()
  const dispatch = useAppDispatch()
  const [name, setName] = useState(purchase?.name ?? '')
  const [amount, setAmount] = useState<string>(purchase ? String(purchase.amount) : '')
  const [date, setDate] = useState(purchase?.date ?? situation?.today ?? '')
  const [err, setErr] = useState<string | null>(null)

  if (!situation) return null

  const minDate = situation.today
  const maxDate = addDays(situation.today, 29)

  function submit(e: FormEvent) {
    e.preventDefault()
    const amt = Number(amount)
    if (!(amt > 0)) {
      setErr('Укажи цену больше нуля.')
      return
    }
    if (!situation) return
    const idx = dayIndex(situation.today, date || situation.today)
    if (idx < 0 || idx >= 30) {
      setErr('Дата должна быть в ближайшие 30 дней.')
      return
    }
    setErr(null)
    dispatch({
      type: 'SET_PURCHASE',
      purchase: { amount: amt, date: date || situation.today, name: name || 'Покупка' },
    })
  }

  return (
    <div className="card">
      <form className="inline-buy" onSubmit={submit}>
        <div className="ib-title eyebrow">
          <span className="star">Главная фишка</span> Проверь покупку до того, как потратишь
        </div>
        <label className="f">
          Что хочу купить
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Наушники"
          />
        </label>
        <label className="f">
          Сколько стоит, ₽
          <input
            type="number"
            min={1}
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            placeholder="3000"
          />
        </label>
        <label className="f">
          Когда
          <input
            type="date"
            min={minDate}
            max={maxDate}
            value={date}
            onChange={(e) => setDate(e.target.value)}
          />
        </label>
        <button className="btn primary" type="submit">
          Когда можно купить?
        </button>
        {err && (
          <span className="errmsg" style={{ flexBasis: '100%' }}>
            {err}
          </span>
        )}
      </form>
    </div>
  )
}
