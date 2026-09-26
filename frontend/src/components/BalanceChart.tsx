import { useMemo, useRef, useState } from 'react'
import type { Dashboard, Event } from '../types'
import { fd, fdShort, rub } from '../lib/format'
import { addDays, dayIndex } from '../lib/dates'

type Line = {
  id: string
  label: string
  values: number[]
  stroke: 'solid' | 'dashed'
  color: string
  corridorWith?: string
  criticalOverlay: boolean
}

function buildLines(dashboard: Dashboard): { lines: Line[]; primaryId: string } {
  const { base, pessimistic, with_purchase, with_purchase_pessimistic } = dashboard.scenarios
  const baseValues = base.days.map((d) => d.balance)

  if (with_purchase) {
    const lines: Line[] = [
      {
        id: 'base_dim',
        label: 'Без покупки',
        values: baseValues,
        stroke: 'solid',
        color: 'var(--text-muted)',
        criticalOverlay: false,
      },
    ]
    if (with_purchase_pessimistic) {
      lines.push(
        {
          id: 'with_purchase_pessimistic',
          label: 'Если подработки не будет',
          values: with_purchase_pessimistic.days.map((d) => d.balance),
          stroke: 'solid',
          color: 'var(--money-fixed)',
          criticalOverlay: true,
        },
        {
          id: 'with_purchase',
          label: 'Если подработка будет',
          values: with_purchase.days.map((d) => d.balance),
          stroke: 'dashed',
          color: 'var(--money-variable)',
          corridorWith: 'with_purchase_pessimistic',
          criticalOverlay: true,
        },
      )
      return { lines, primaryId: 'with_purchase' }
    }
    lines.push({
      id: 'with_purchase',
      label: 'С покупкой',
      values: with_purchase.days.map((d) => d.balance),
      stroke: 'solid',
      color: 'var(--money-fixed)',
      criticalOverlay: true,
    })
    return { lines, primaryId: 'with_purchase' }
  }

  if (pessimistic) {
    return {
      lines: [
        {
          id: 'pessimistic',
          label: 'Если подработки не будет',
          values: pessimistic.days.map((d) => d.balance),
          stroke: 'solid',
          color: 'var(--money-fixed)',
          criticalOverlay: true,
        },
        {
          id: 'base',
          label: 'Если подработка будет',
          values: baseValues,
          stroke: 'dashed',
          color: 'var(--money-variable)',
          corridorWith: 'pessimistic',
          criticalOverlay: true,
        },
      ],
      primaryId: 'base',
    }
  }

  return {
    lines: [
      {
        id: 'base',
        label: 'Прогноз',
        values: baseValues,
        stroke: 'solid',
        color: 'var(--money-fixed)',
        criticalOverlay: true,
      },
    ],
    primaryId: 'base',
  }
}

function niceStep(span: number): number {
  const raw = span / 5
  const mag = Math.pow(10, Math.floor(Math.log10(raw || 1)))
  const candidates = [1, 2, 2.5, 5, 10].map((k) => k * mag)
  return candidates.find((s) => s >= raw) ?? candidates[candidates.length - 1]
}

const W = 760
const CH = 300
const MARGIN = { l: 62, r: 14, t: 14, b: 52 }
const EV_Y = CH - MARGIN.b + 14

export function BalanceChart({ dashboard }: { dashboard: Dashboard }) {
  const H = dashboard.horizon_days
  const { lines, primaryId } = useMemo(() => buildLines(dashboard), [dashboard])
  const [hidden, setHidden] = useState<Set<string>>(new Set())
  const [hoverDay, setHoverDay] = useState<number | null>(null)
  // После касания браузер дорисовывает мышиные события и сразу «уводит курсор» —
  // без этого флага подсказка на телефоне гасла бы в тот же миг, что и появилась.
  const touched = useRef(false)

  const visible = lines.filter((l) => !hidden.has(l.id))

  const allValues = visible.flatMap((l) => l.values)
  let lo = Math.min(0, ...allValues)
  let hi = Math.max(0, ...allValues)
  const span = hi - lo || 1
  const step = niceStep(span)
  lo = Math.floor(lo / step) * step
  hi = Math.ceil(hi / step) * step

  const X = (d: number) => MARGIN.l + (d * (W - MARGIN.l - MARGIN.r)) / (H - 1)
  const Y = (v: number) => MARGIN.t + ((hi - v) * (CH - MARGIN.t - MARGIN.b)) / (hi - lo || 1)

  const path = (values: number[]) =>
    values.map((v, d) => `${d ? 'L' : 'M'}${X(d).toFixed(1)} ${Y(v).toFixed(1)}`).join(' ')

  const gridRows: number[] = []
  for (let v = lo; v <= hi + 1e-6; v += step) gridRows.push(v)

  const xLabels: number[] = []
  for (let d = 0; d < H; d += 7) xLabels.push(d)

  function moveTo(clientX: number, rect: DOMRect) {
    const px = ((clientX - rect.left) / rect.width) * W
    const d = Math.max(0, Math.min(H - 1, Math.round((px - MARGIN.l) / ((W - MARGIN.l - MARGIN.r) / (H - 1)))))
    setHoverDay(d)
  }

  const primary = lines.find((l) => l.id === primaryId)
  let minDay = 0
  let minVal = 0
  if (primary) {
    minVal = Infinity
    primary.values.forEach((v, d) => {
      if (v < minVal) {
        minVal = v
        minDay = d
      }
    })
  }

  const eventsOnDay = (d: number): Event[] =>
    dashboard.events.filter((e) => dayIndex(dashboard.today, e.date) === d)

  // Заливка появляется только когда обе линии коридора видимы — тогда же и подпись к ней.
  const corridorLine = visible.find((l) => l.corridorWith && visible.some((o) => o.id === l.corridorWith))

  return (
    <div className="card chart-card">
      <div className="chart-head">
        <div>
          <h3>Остаток по дням</h3>
          <div className="sub">{H} дней вперёд · на конец каждого дня</div>
        </div>
        <div className="legend">
          {lines.map((l) => (
            <button
              key={l.id}
              type="button"
              className="legend-toggle"
              aria-pressed={!hidden.has(l.id)}
              onClick={() =>
                setHidden((prev) => {
                  const next = new Set(prev)
                  if (next.has(l.id)) next.delete(l.id)
                  else next.add(l.id)
                  return next
                })
              }
            >
              <i
                style={{
                  borderTopStyle: l.stroke === 'dashed' ? 'dashed' : 'solid',
                  borderTopColor: l.color,
                  opacity: hidden.has(l.id) ? 0.35 : 1,
                }}
              />
              {l.label}
            </button>
          ))}
          <span>
            <i className="inc" />
            поступление точно
          </span>
          {dashboard.events.some((e) => e.kind === 'income' && !e.confirmed) && (
            <span>
              <svg className="inc-unc" viewBox="0 0 13 10" aria-hidden="true">
                <path d="M6.5 1 12 9H1Z" fill="none" stroke="var(--status-good)" strokeWidth="1.5" />
              </svg>
              может не прийти
            </span>
          )}
          <span>
            <i className="obl" />
            платёж
          </span>
          {corridorLine && (
            <span>
              <i className="corr" />
              разница сценариев
            </span>
          )}
          {lo < 0 && (
            <span>
              <i className="neg" />
              превышение бюджета
            </span>
          )}
        </div>
      </div>
      {visible.length === 0 ? (
        <p className="sub">Все линии скрыты — включи хотя бы одну в легенде выше.</p>
      ) : (
      <div className="chart-wrap">
        {/* На узком экране график не сжимаем до нечитаемых подписей, а прокручиваем вбок.
            Обработчики мыши и касания — именно здесь: размеры этого блока совпадают с svg даже при прокрутке. */}
        <div
          className="chart-inner"
          onMouseMove={(e) => moveTo(e.clientX, e.currentTarget.getBoundingClientRect())}
          onMouseLeave={() => {
            if (touched.current) touched.current = false
            else setHoverDay(null)
          }}
          onTouchStart={(e) => {
            touched.current = true
            moveTo(e.touches[0].clientX, e.currentTarget.getBoundingClientRect())
          }}
          onTouchMove={(e) => {
            touched.current = true
            moveTo(e.touches[0].clientX, e.currentTarget.getBoundingClientRect())
          }}
        >
        <svg className="chart" viewBox={`0 0 ${W} ${CH}`} role="img" aria-label="График остатка по дням">
          <defs>
            <clipPath id="negclip">
              <rect
                x={MARGIN.l}
                y={Y(0)}
                width={W - MARGIN.l - MARGIN.r}
                height={Math.max(0, Y(lo) - Y(0))}
              />
            </clipPath>
          </defs>
          {lo < 0 && (
            <rect
              x={MARGIN.l}
              y={Y(0)}
              width={W - MARGIN.l - MARGIN.r}
              height={Y(lo) - Y(0)}
              fill="var(--status-critical)"
              opacity={0.08}
            />
          )}
          {gridRows.map((v) => (
            <g key={v}>
              <line
                x1={MARGIN.l}
                x2={W - MARGIN.r}
                y1={Y(v)}
                y2={Y(v)}
                stroke={v === 0 ? 'var(--text-muted)' : 'var(--gridline)'}
                strokeWidth={v === 0 ? 1.5 : 1}
              />
              <text x={MARGIN.l - 8} y={Y(v) + 4} textAnchor="end" fontSize={11.5} fill="var(--text-muted)" className="num">
                {new Intl.NumberFormat('ru-RU').format(v)}
              </text>
            </g>
          ))}
          {xLabels.map((d) => (
            <text
              key={d}
              x={X(d)}
              y={CH - MARGIN.b + 34}
              textAnchor="middle"
              fontSize={11.5}
              fill="var(--text-muted)"
            >
              {d === 0 ? 'сегодня' : fdShort(addDays(dashboard.today, d))}
            </text>
          ))}
          {dashboard.events.map((ev, i) => {
            const d = dayIndex(dashboard.today, ev.date)
            if (d < 0 || d >= H) return null
            const x = X(d)
            if (ev.kind === 'income') {
              return (
                <path
                  key={i}
                  d={`M${x - 6} ${EV_Y + 5} L${x + 6} ${EV_Y + 5} L${x} ${EV_Y - 5} Z`}
                  fill={ev.confirmed ? 'var(--status-good)' : 'none'}
                  stroke="var(--status-good)"
                  strokeWidth={1.5}
                />
              )
            }
            return (
              <circle
                key={i}
                cx={x}
                cy={EV_Y}
                r={4.5}
                fill={ev.kind === 'obligation' || ev.kind === 'purchase' ? 'var(--text-primary)' : 'none'}
                stroke="var(--text-primary)"
                strokeWidth={ev.kind === 'spend' ? 1.5 : 0}
              />
            )
          })}
          {(() => {
            if (!corridorLine) return null
            const other = visible.find((o) => o.id === corridorLine.corridorWith)!
            const pts = corridorLine.values
              .map((v, d) => `${X(d)},${Y(v)}`)
              .concat(
                [...other.values]
                  .map((v, d) => `${X(d)},${Y(v)}`)
                  .reverse(),
              )
            return <polygon points={pts.join(' ')} fill="var(--money-variable)" opacity={0.15} />
          })()}
          {visible.map((l) => (
            <g key={l.id}>
              <path
                d={path(l.values)}
                fill="none"
                stroke={l.color}
                strokeWidth={l.id === 'base_dim' ? 2 : 2.5}
                strokeDasharray={l.stroke === 'dashed' ? '6 5' : undefined}
                strokeLinejoin="round"
                strokeLinecap="round"
              />
              {l.criticalOverlay && (
                <path
                  d={path(l.values)}
                  fill="none"
                  stroke="var(--status-critical)"
                  strokeWidth={l.id === 'base_dim' ? 2 : 3}
                  strokeDasharray={l.stroke === 'dashed' ? '6 5' : undefined}
                  strokeLinejoin="round"
                  clipPath="url(#negclip)"
                />
              )}
            </g>
          ))}
          {primary && (
            <>
              <circle
                cx={X(minDay)}
                cy={Y(minVal)}
                r={5}
                fill={minVal < 0 ? 'var(--status-critical)' : 'var(--status-good)'}
                stroke="var(--surface-card)"
                strokeWidth={2}
              />
              <text
                x={Math.min(Math.max(X(minDay), MARGIN.l + 40), W - MARGIN.r - 40)}
                y={Y(minVal) + (Y(minVal) > CH - MARGIN.b - 30 ? -12 : 20)}
                textAnchor="middle"
                fontSize={12}
                fontWeight={700}
                fill={minVal < 0 ? 'var(--status-critical)' : 'var(--text-primary)'}
              >
                {rub(minVal)}
              </text>
            </>
          )}
          {hoverDay !== null && (
            <line
              x1={X(hoverDay)}
              x2={X(hoverDay)}
              y1={MARGIN.t}
              y2={CH - MARGIN.b}
              stroke="var(--text-secondary)"
              strokeWidth={1}
              opacity={0.5}
            />
          )}
          <rect
            x={MARGIN.l}
            y={MARGIN.t}
            width={W - MARGIN.l - MARGIN.r}
            height={CH - MARGIN.t - MARGIN.b + 24}
            fill="transparent"
          />
        </svg>
        {hoverDay !== null && (
          <div className="tip" style={{ left: `${(X(hoverDay) / W) * 100}%`, top: 8 }}>
            <b>{hoverDay === 0 ? 'сегодня' : fd(addDays(dashboard.today, hoverDay))}</b>
            {visible.map((l) => (
              <div key={l.id} className="tip-row">
                <span>{l.label}</span>
                <b className="num">{rub(l.values[hoverDay])}</b>
              </div>
            ))}
            {eventsOnDay(hoverDay).map((e, i) => (
              <div key={i} className="ev">
                {e.kind === 'income' ? '+' : '−'}
                {rub(e.amount)} {e.name}
              </div>
            ))}
          </div>
        )}
        </div>
      </div>
      )}
    </div>
  )
}
