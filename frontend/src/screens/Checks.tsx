import { useEffect, useState } from 'react'
import { getChecks } from '../api/client'
import type { ChecksResult } from '../types'
import { useAppDispatch } from '../state/store'

const FALLBACK: { id: number; title: string; expected: string }[] = [
  { id: 1, title: 'Аня без покупок', expected: 'минимум 600 ₽, 9 октября, состояние «впритык»' },
  { id: 2, title: 'Аня: покупка 3 000 сегодня', expected: 'минус с 5 октября, максимум минуса 2 400 ₽, безопасно с 15 октября' },
  { id: 3, title: 'Аня: покупка 1 000 сегодня', expected: 'минус с 8 октября, максимум минуса 400 ₽, безопасно с 10 октября' },
  { id: 4, title: 'Пусто: баланс 0, без поступлений', expected: 'минус с сегодняшнего дня, состояние «нет дохода»' },
  { id: 5, title: 'Баланс −500', expected: 'ошибка в поле balance' },
  { id: 6, title: 'Аня, дата стипендии в прошлом', expected: 'ошибка в поле incomes[0].date' },
  { id: 7, title: 'Аня: покупка 6 900 сегодня', expected: 'минус с сегодняшнего дня' },
  { id: 8, title: 'Баланс 1000, платёж и доход день в день', expected: 'минус с 30 сентября, на 400 ₽' },
  { id: 9, title: 'Аня: покупка 50 000', expected: 'безопасной даты в горизонте нет' },
  { id: 10, title: 'Даня', expected: 'база: минимум 1160 ₽; пессимистично: минус с 9 октября, 2 840 ₽' },
  { id: 11, title: 'Аня + разовая трата «Такси» 800', expected: 'минимум −200 ₽, сократить на 16 ₽/день' },
  { id: 12, title: 'Цель Ани без покупки', expected: 'остаток в месяц 1 800 ₽, цель к 4 июня 2027, отставание 3 дня' },
  { id: 13, title: 'Цель Ани с покупкой 3 000', expected: 'цель сдвигается на 50 дней' },
]

export function Checks() {
  const dispatch = useAppDispatch()
  const [result, setResult] = useState<ChecksResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getChecks()
      .then((r) => {
        setResult(r)
        setLoading(false)
      })
      .catch(() => {
        setError('/api/checks пока недоступен — показываем ожидаемые значения из раздела 8 CONTRACT.md.')
        setLoading(false)
      })
  }, [])

  const rows = result ? result.items : FALLBACK.map((s) => ({ ...s, got: '—', ok: null as boolean | null }))
  const score = result ? `${result.passed}/${result.total}` : 'pending'

  return (
    <section id="checks">
      <header className="topbar">
        <div className="wrap">
          <div className="brand">
            <span className="brand-mark">₽</span>Дотяну
          </div>
          <span className="demo-chip">Демо: 27 сентября 2026</span>
          <span className="spacer" />
          <button className="btn sm" type="button" onClick={() => dispatch({ type: 'GO', screen: 'start' })}>
            ← Назад
          </button>
        </div>
      </header>
      <div className="wrap" style={{ paddingBlock: '24px 60px', display: 'grid', gap: 16 }}>
        <div className="score">
          <span className="big">{loading ? '…' : score}</span>
          <div>
            <h2 style={{ fontSize: 20 }}>Как мы проверяли расчёты</h2>
            <p style={{ color: 'var(--muted)' }}>
              {loading
                ? 'Спрашиваем бэкенд...'
                : error
                  ? error
                  : 'Эти сценарии прогнал бэкенд роли A через /api/checks прямо сейчас.'}
            </p>
          </div>
        </div>
        <div className="tbl-wrap">
          <table>
            <thead>
              <tr>
                <th>#</th>
                <th>Ситуация</th>
                <th>Ожидаем</th>
                <th>Получили</th>
                <th>Итог</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((s) => (
                <tr key={s.id}>
                  <td>{s.id}</td>
                  <td>{s.title}</td>
                  <td>{s.expected}</td>
                  <td>{'got' in s ? s.got : '—'}</td>
                  <td className={s.ok === true ? 'ok' : s.ok === false ? 'fail' : undefined}>
                    {s.ok === true ? '✓' : s.ok === false ? '✗' : 'pending'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  )
}
