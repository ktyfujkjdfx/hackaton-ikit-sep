import type { Dashboard } from '../types'
import { daysWord, fd, rub } from '../lib/format'
import { DeficitPlanCards } from './DeficitPlanCards'
import { useAppDispatch } from '../state/store'

export function BuyCard({ dashboard }: { dashboard: Dashboard }) {
  const dispatch = useAppDispatch()
  const check = dashboard.purchase
  if (!check) return null

  const { purchase, after, before, earliest_safe_date, safe_depends_on_unconfirmed, goal, plan } = check
  const when = purchase.date === dashboard.today ? 'сегодня' : fd(purchase.date)
  const safe = after.first_negative_date === null

  function defer() {
    if (earliest_safe_date) {
      dispatch({
        type: 'ADD_DEFERRED',
        deferred: { name: purchase.name, amount: purchase.amount, safe_date: earliest_safe_date },
      })
    }
    dispatch({ type: 'SET_PURCHASE', purchase: null })
  }

  return (
    <div className="card buy-card">
      <div className="eyebrow">
        <span className="star">Главная фишка</span> Проверка покупки · считает код
      </div>
      <h2>
        {purchase.name} за {rub(purchase.amount)}, {when}
      </h2>

      {safe ? (
        <div className="buy-top">
          <div className="safe-big ok">
            <small>Минуса не будет</small>
            <b>Можно {purchase.date === dashboard.today ? 'сейчас' : when}</b>
          </div>
          <p className="buy-why">
            Самый низкий остаток после покупки — <b>{rub(after.min)}</b>, {fd(after.min_date)}. Решение за тобой.
          </p>
        </div>
      ) : (
        <div className="buy-top">
          <div className="safe-big">
            <small>Без минуса можно купить</small>
            <b>{earliest_safe_date ? `с ${fd(earliest_safe_date)}` : 'не в ближайшие 30 дней'}</b>
          </div>
          <p className="buy-why">
            Если купить {when}, денег не хватит с{' '}
            <b style={{ color: 'var(--status-critical)' }}>
              {after.first_negative_date ? fd(after.first_negative_date) : '—'}
            </b>
            .{safe_depends_on_unconfirmed ? ' Безопасная дата зависит от непостоянного дохода.' : ''} Решать тебе —
            ниже варианты, как купить раньше.
          </p>
        </div>
      )}

      <div className="kfacts">
        {safe ? (
          <>
            <div>
              <span>Остаток до покупки, минимум</span>
              <b className="num">{rub(before.min)}</b>
            </div>
            <div>
              <span>После покупки, минимум</span>
              <b className="num">{rub(after.min)}</b>
            </div>
          </>
        ) : (
          <>
            <div>
              <span>Первый день без денег</span>
              <b>{after.first_negative_date ? fd(after.first_negative_date) : '—'}</b>
            </div>
            <div>
              <span>Самый большой минус</span>
              <b className="num" style={{ color: 'var(--status-critical)' }}>
                {rub(after.max_deficit)}
              </b>
            </div>
          </>
        )}
        <div>
          <span>Цель сдвинется</span>
          <b>{goal?.eta ? `на ${daysWord(goal.shift_days ?? 0)}` : '—'}</b>
        </div>
      </div>

      {!safe && plan && (
        <div>
          <div className="eyebrow" style={{ marginBottom: 8 }}>
            <span className="star">Фишка</span> План выхода из минуса
          </div>
          <DeficitPlanCards plan={plan} />
        </div>
      )}

      <div className="hero-actions">
        {earliest_safe_date && !safe && (
          <button className="btn primary" type="button" onClick={defer}>
            Отложить до {fd(earliest_safe_date)}
          </button>
        )}
        <button className="btn ghost" type="button" onClick={() => dispatch({ type: 'SET_PURCHASE', purchase: null })}>
          Убрать покупку
        </button>
      </div>
    </div>
  )
}
