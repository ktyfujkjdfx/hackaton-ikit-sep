import { useState, type FormEvent } from 'react'
import { useAppDispatch, useAppState } from '../state/store'
import { AddModal, type AddModalPrefill } from './AddModal'

export function AskPanel() {
  const { messages, situation } = useAppState()
  const dispatch = useAppDispatch()
  const [input, setInput] = useState('')
  const [modal, setModal] = useState<AddModalPrefill | null>(null)

  if (!situation) return null
  const today = situation.today

  function pushUser(text: string) {
    dispatch({ type: 'ADD_MESSAGE', message: { role: 'user', text } })
  }
  function pushBot(text: string) {
    dispatch({ type: 'ADD_MESSAGE', message: { role: 'bot', text } })
  }

  function askPurchase3000() {
    pushUser('Могу купить наушники за 3000?')
    dispatch({ type: 'SET_PURCHASE', purchase: { amount: 3000, date: today, name: 'Наушники' } })
    pushBot('Смотри карточку покупки выше — там дата, с которой можно купить без минуса, и план на случай минуса.')
  }
  function askSpendTaxi() {
    pushUser('Сегодня такси 800')
    setModal({ type: 'spend', name: 'Такси', amount: 800, date: today, category: 'Транспорт' })
  }
  function askIncome() {
    pushUser('Подработка 1500 4 октября, не точно')
    setModal({ type: 'income', name: 'Подработка', amount: 1500 })
  }
  function askTerm() {
    pushUser('Что такое финансовая подушка?')
    pushBot(
      'Финансовая подушка — запас денег на случай, если доход пропал или случилась непредвиденная трата. Источник: fincult.info — сайт Банка России.',
    )
  }
  function askInvest() {
    pushUser('Куда вложить 5000?')
    pushBot(
      'Я не советую, во что вкладывать, и не использую твои суммы для таких советов. Сначала подушка безопасности, потом накопления на цели, и только потом инвестиции.',
    )
  }

  function submitFreeText(e: FormEvent) {
    e.preventDefault()
    if (!input.trim()) return
    pushUser(input)
    pushBot('Пока понимаю только кнопки ниже и явные поля — свободный текст разберёт модель роли B, когда будет готова.')
    setInput('')
  }

  return (
    <aside className="panel" aria-label="Спросить">
      <div className="panel-head">
        <b>Спросить</b>
        <span>Пока без разбора свободного текста — жми кнопки или добавляй запись явно.</span>
      </div>
      <div className="msgs" aria-live="polite">
        {messages.map((m, i) => (
          <div key={i} className={`msg ${m.role}`}>
            {m.text}
          </div>
        ))}
      </div>
      <div className="sugg">
        <button type="button" onClick={askPurchase3000}>
          Могу купить наушники за 3000?
        </button>
        <button type="button" onClick={askSpendTaxi}>
          Сегодня такси 800
        </button>
        <button type="button" onClick={askIncome}>
          Подработка 1500 4 октября, не точно
        </button>
        <button type="button" onClick={askTerm}>
          Что такое финансовая подушка?
        </button>
        <button type="button" onClick={askInvest}>
          Куда вложить 5000?
        </button>
      </div>
      <form className="ask-form" onSubmit={submitFreeText}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Могу купить наушники за 3000?"
          autoComplete="off"
        />
        <button className="btn primary" type="submit">
          →
        </button>
      </form>
      <div className="proto-note">
        Свободный текст пока не разбираем — ждём модель роли B (<code>/api/chat</code>). Действия ниже вызывают
        реальный код движка.
      </div>
      <div style={{ padding: '0 14px 14px' }}>
        <button
          className="btn sm"
          type="button"
          style={{ width: '100%', justifyContent: 'center' }}
          onClick={() => setModal({ type: 'spend', date: today })}
        >
          + Добавить трату или доход
        </button>
      </div>
      {modal && <AddModal prefill={modal} onClose={() => setModal(null)} />}
    </aside>
  )
}
