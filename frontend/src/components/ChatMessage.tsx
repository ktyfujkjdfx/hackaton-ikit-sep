import type { ChatResponse } from '../types'
import { SHOW_DEBUG } from '../lib/debug'
import { useAppDispatch } from '../state/store'

const NLU_MODE_LABEL: Record<ChatResponse['nlu']['mode'], string> = {
  onnx: 'onnx',
  sklearn: 'sklearn',
  rules: 'правила',
}

// Кнопки из ответа показываем только те, которым в интерфейсе есть куда вести.
// Остальные виды действий уже закрыты своими карточками (покупка, добавление траты).
const RENDERED_ACTIONS = new Set(['open_explain'])

export function ChatMessage({ resp, greeting }: { resp: ChatResponse; greeting?: boolean }) {
  const dispatch = useAppDispatch()
  const isRefusal = !greeting && resp.intent === 'refusal'
  const isClarify = !greeting && resp.intent === 'clarify'
  const [lead, ...rest] = resp.facts
  const actions = resp.actions.filter((a) => RENDERED_ACTIONS.has(a.kind))

  return (
    <div className={`msg bot${isRefusal ? ' refusal' : ''}${isClarify ? ' clarify' : ''}`}>
      {isRefusal && (
        <div className="msg-kind refusal">
          <span aria-hidden="true">⚠</span> Отказ
        </div>
      )}
      {isClarify && (
        <div className="msg-kind clarify">
          <span aria-hidden="true">?</span> Нужно уточнение
        </div>
      )}
      {SHOW_DEBUG && !greeting && (
        <div className="nlu-badge">
          модель: {resp.nlu.label} · {Math.round(resp.nlu.confidence * 100)}%
          <span className="nlu-mode">{NLU_MODE_LABEL[resp.nlu.mode]}</span>
        </div>
      )}
      {SHOW_DEBUG &&
        resp.tool_calls.map((tc, i) => (
          <div className="tool" key={i}>
            → вызов: {tc.name}({Object.entries(tc.args).map(([k, v]) => `${k}=${v}`).join(', ')})
          </div>
        ))}
      {resp.headline && (
        <div className={`headline ${resp.tone === 'bad' ? 'bad' : resp.tone === 'good' ? 'good' : ''}`}>{resp.headline}</div>
      )}
      {lead && (
        <div className="facts">
          <div className="lead">
            <span>{lead.label}</span>
            <b className={lead.tone === 'bad' ? 'bad' : lead.tone === 'good' ? 'good' : undefined}>{lead.value}</b>
          </div>
          {rest.map((f, i) => (
            <div key={i}>
              <span>{f.label}</span>
              <b className={f.tone === 'bad' ? 'bad' : undefined}>{f.value}</b>
            </div>
          ))}
        </div>
      )}
      {resp.text && <div className="ai">{resp.text}</div>}
      {resp.source && (
        <div className="msg-source">
          Источник:{' '}
          <a href={resp.source.url} target="_blank" rel="noopener noreferrer">
            {resp.source.title}
          </a>
        </div>
      )}
      {actions.length > 0 && (
        <div className="msg-actions">
          {actions.map((a, i) => (
            <button
              key={i}
              className="btn ghost sm"
              type="button"
              onClick={() => dispatch({ type: 'OPEN_EXPLAIN' })}
            >
              {a.label}
            </button>
          ))}
        </div>
      )}
      {resp.guarded && (
        <div className="guarded-note">Пояснение проверено: числа в тексте не совпадали с расчётом — показан шаблон.</div>
      )}
    </div>
  )
}
