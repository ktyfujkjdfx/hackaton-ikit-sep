import { useState } from 'react'
import { dayIndex } from '../lib/dates'
import { useAppDispatch, useAppState } from '../state/store'

export type AddModalPrefill = {
  type: 'spend' | 'income'
  name?: string
  amount?: number
  date?: string
  category?: string
}

export function AddModal({ prefill, onClose }: { prefill: AddModalPrefill; onClose: () => void }) {
  const { situation } = useAppState()
  const dispatch = useAppDispatch()
  const [type, setType] = useState<'spend' | 'income'>(prefill.type)
  const [name, setName] = useState(prefill.name ?? '')
  const [amount, setAmount] = useState(prefill.amount ? String(prefill.amount) : '')
  const [date, setDate] = useState(prefill.date ?? situation?.today ?? '')
  const [category, setCategory] = useState(prefill.category ?? 'Прочее')
  const [confirmed, setConfirmed] = useState(true)
  const [err, setErr] = useState<string | null>(null)

  if (!situation) return null

  function save() {
    const amt = Number(amount)
    if (!(amt > 0)) {
      setErr('Сумма должна быть больше нуля.')
      return
    }
    if (!situation) return
    if (!date || dayIndex(situation.today, date) < 0) {
      setErr('Дата не может быть в прошлом.')
      return
    }
    if (type === 'spend') {
      dispatch({
        type: 'SET_SITUATION',
        situation: {
          ...situation,
          spends: [
            ...situation.spends,
            { id: crypto.randomUUID(), name: name || 'Трата', amount: amt, date, category },
          ],
        },
      })
    } else {
      dispatch({
        type: 'SET_SITUATION',
        situation: {
          ...situation,
          incomes: [
            ...situation.incomes,
            { id: crypto.randomUUID(), name: name || 'Доход', amount: amt, date, confirmed },
          ],
        },
      })
    }
    onClose()
  }

  return (
    <>
      <div className="scrim" onClick={onClose} />
      <div className="modal" role="dialog" aria-modal="true">
        <div className="seg">
          <button type="button" aria-pressed={type === 'spend'} onClick={() => setType('spend')}>
            Трата
          </button>
          <button type="button" aria-pressed={type === 'income'} onClick={() => setType('income')}>
            Доход
          </button>
        </div>
        <label className="f">
          Название
          <input type="text" value={name} onChange={(e) => setName(e.target.value)} placeholder={type === 'spend' ? 'Такси' : 'Подработка'} />
        </label>
        <label className="f">
          Сумма, ₽
          <input type="number" min={1} value={amount} onChange={(e) => setAmount(e.target.value)} />
        </label>
        <label className="f">
          Дата
          <input type="date" min={situation.today} value={date} onChange={(e) => setDate(e.target.value)} />
        </label>
        {type === 'spend' ? (
          <label className="f">
            Категория
            <input type="text" value={category} onChange={(e) => setCategory(e.target.value)} />
          </label>
        ) : (
          <label className="f">
            Тип дохода
            <select value={confirmed ? 'yes' : 'no'} onChange={(e) => setConfirmed(e.target.value === 'yes')}>
              <option value="yes">Основной доход</option>
              <option value="no">Дополнительный доход</option>
            </select>
            <span className="field-hint">Основной — то, что точно придёт вовремя: стипендия, соцвыплаты. Дополнительный — то, что может не прийти: подработка, разовый перевод.</span>
          </label>
        )}
        {err && <span className="errmsg">{err}</span>}
        <div className="form-actions">
          <button className="btn primary" type="button" onClick={save}>
            Сохранить
          </button>
          <button className="btn ghost" type="button" onClick={onClose}>
            Отмена
          </button>
        </div>
      </div>
    </>
  )
}
