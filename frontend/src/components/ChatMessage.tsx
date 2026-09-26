import type { ChatResponse } from '../types'

export function ChatMessage({ resp }: { resp: ChatResponse }) {
  return (
    <div className="msg bot">
      {resp.tool_calls.map((tc, i) => (
        <div className="tool" key={i}>
          → вызов: {tc.name}({Object.entries(tc.args).map(([k, v]) => `${k}=${v}`).join(', ')})
        </div>
      ))}
      {resp.headline && <div className={`headline ${resp.tone === 'bad' ? 'bad' : resp.tone === 'good' ? 'good' : ''}`}>{resp.headline}</div>}
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
        <div style={{ fontSize: 12.5, color: 'var(--muted)' }}>
          Источник:{' '}
          <a href={resp.source.url} target="_blank" rel="noopener noreferrer">
            {resp.source.title}
          </a>
        </div>
      )}
    </div>
  )
}
