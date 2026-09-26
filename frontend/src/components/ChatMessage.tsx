import type { ChatResponse } from '../types'

const NLU_MODE_LABEL: Record<ChatResponse['nlu']['mode'], string> = {
  onnx: 'onnx',
  sklearn: 'sklearn',
  rules: 'правила',
}

export function ChatMessage({ resp }: { resp: ChatResponse }) {
  const isRefusal = resp.intent === 'refusal'
  const isClarify = resp.intent === 'clarify'

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
      <div className="nlu-badge">
        модель: {resp.nlu.label} · {Math.round(resp.nlu.confidence * 100)}%
        <span className="nlu-mode">{NLU_MODE_LABEL[resp.nlu.mode]}</span>
      </div>
      {resp.tool_calls.map((tc, i) => (
        <div className="tool" key={i}>
          → вызов: {tc.name}({Object.entries(tc.args).map(([k, v]) => `${k}=${v}`).join(', ')})
        </div>
      ))}
      {resp.headline && (
        <div className={`headline ${resp.tone === 'bad' ? 'bad' : resp.tone === 'good' ? 'good' : ''}`}>{resp.headline}</div>
      )}
      {resp.facts.length > 0 && (
        <div className="facts">
          {resp.facts.map((f, i) => (
            <div key={i}>
              <span>{f.label}</span>
              <b style={f.tone === 'bad' ? { color: 'var(--status-critical)' } : undefined}>{f.value}</b>
            </div>
          ))}
        </div>
      )}
      {resp.text && <div className="ai">{resp.text}</div>}
      {resp.source && (
        <div style={{ fontSize: 12.5, color: 'var(--text-secondary)' }}>
          Источник:{' '}
          <a href={resp.source.url} target="_blank" rel="noopener noreferrer">
            {resp.source.title}
          </a>
        </div>
      )}
      {resp.guarded && (
        <div className="guarded-note">Пояснение проверено: числа в тексте не совпадали с фактами — показан шаблон.</div>
      )}
    </div>
  )
}
