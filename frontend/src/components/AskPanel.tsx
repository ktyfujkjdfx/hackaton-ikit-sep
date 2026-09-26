import { useEffect, useRef, useState, type FormEvent } from 'react'
import { postChat } from '../api/client'
import { buildChatResponse } from '../lib/chatMock'
import { useAppDispatch, useAppState } from '../state/store'
import { AddModal, type AddModalPrefill } from './AddModal'
import { ChatMessage } from './ChatMessage'

const SUGGESTIONS = [
  'Могу купить наушники за 3000?',
  'Сегодня такси 800',
  'Подработка 1500 4 октября, не точно',
  'Что такое финансовая подушка?',
  'Куда вложить 5000?',
  'скажи код из смс',
]

export function AskPanel() {
  const { messages, situation, purchase } = useAppState()
  const dispatch = useAppDispatch()
  const [input, setInput] = useState('')
  const [modal, setModal] = useState<AddModalPrefill | null>(null)
  const [collapsed, setCollapsed] = useState(false)
  const [sending, setSending] = useState(false)
  const msgsRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const el = msgsRef.current
    if (el) el.scrollTop = el.scrollHeight
  }, [messages, sending])

  if (!situation) return null

  async function sendMessage(text: string) {
    if (!situation || sending) return
    dispatch({ type: 'ADD_MESSAGE', message: { role: 'user', text } })
    setSending(true)
    const history = messages.slice(-6).map((m) => ({
      role: (m.role === 'bot' ? 'assistant' : 'user') as 'user' | 'assistant',
      text: m.role === 'bot' ? m.resp.text : m.text,
    }))
    try {
      const resp = await postChat({ situation, purchase, message: text, history })
      dispatch({ type: 'ADD_MESSAGE', message: { role: 'bot', resp } })
      if (resp.purchase) dispatch({ type: 'SET_PURCHASE', purchase: resp.purchase })
      if (resp.proposed_entry) {
        const pe = resp.proposed_entry
        setModal({ type: pe.type, name: pe.name, amount: pe.amount, date: pe.date, category: pe.category })
      }
    } catch {
      dispatch({
        type: 'ADD_MESSAGE',
        message: {
          role: 'bot',
          resp: buildChatResponse({
            text: 'Не получилось получить ответ — сервер недоступен. Попробуй ещё раз.',
            nlu: { mode: 'rules', label: 'clarify', confidence: 0 },
          }),
        },
      })
    } finally {
      setSending(false)
    }
  }

  function submitFreeText(e: FormEvent) {
    e.preventDefault()
    const text = input.trim()
    if (!text) return
    setInput('')
    void sendMessage(text)
  }

  if (collapsed) {
    return (
      <aside className="panel collapsed" aria-label="Спросить (свёрнуто)">
        <button
          className="panel-collapse-toggle"
          type="button"
          onClick={() => setCollapsed(false)}
          title="Открыть панель «Спросить»"
        >
          💬
        </button>
      </aside>
    )
  }

  return (
    <aside className="panel" aria-label="Спросить">
      <div className="panel-head">
        <button
          className="panel-collapse-toggle"
          type="button"
          onClick={() => setCollapsed(true)}
          style={{ textAlign: 'right', padding: '0 0 8px' }}
          title="Свернуть панель"
        >
          ✕
        </button>
        <b>Спросить</b>
        <span>Пиши как удобно. AI понимает вопрос, а все суммы считает код.</span>
      </div>
      <div className="msgs" aria-live="polite" ref={msgsRef}>
        {messages.map((m, i) =>
          m.role === 'user' ? (
            <div key={i} className="msg user">
              {m.text}
            </div>
          ) : (
            <ChatMessage key={i} resp={m.resp} greeting={m.greeting} />
          ),
        )}
        {sending && <div className="msg bot proto-note">Печатает...</div>}
      </div>
      <div className="sugg">
        {SUGGESTIONS.map((s) => (
          <button key={s} type="button" onClick={() => void sendMessage(s)} disabled={sending}>
            {s}
          </button>
        ))}
      </div>
      <form className="ask-form" onSubmit={submitFreeText}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Могу купить наушники за 3000?"
          autoComplete="off"
          disabled={sending}
        />
        <button className="btn primary" type="submit" disabled={sending} aria-label="Отправить вопрос">
          →
        </button>
      </form>
      <p className="voice-hint" title="Диктовка встроена в систему — отдельное приложение не нужно">
        <span aria-hidden="true">🎙</span> Можно надиктовать: <b>Win + H</b> в Windows, двойное <b>Fn</b> на Mac —
        диктовка системы работает прямо в этом поле.
      </p>
      <div className="proto-note">Вопрос понимает наша модель, все суммы считает движок — числа не выдумываются.</div>
      <div style={{ padding: '0 14px 14px' }}>
        <button
          className="btn sm"
          type="button"
          style={{ width: '100%', justifyContent: 'center' }}
          onClick={() => setModal({ type: 'spend', date: situation.today })}
        >
          + Добавить трату или доход
        </button>
      </div>
      {modal && <AddModal prefill={modal} onClose={() => setModal(null)} />}
    </aside>
  )
}
