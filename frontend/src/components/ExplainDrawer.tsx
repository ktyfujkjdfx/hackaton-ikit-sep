import type { Dashboard, Situation } from '../types'
import { fd, rub } from '../lib/format'
import { useAppDispatch, useAppState } from '../state/store'

function updateIncomeAmount(situation: Situation, id: string, amount: number): Situation {
  return { ...situation, incomes: situation.incomes.map((i) => (i.id === id ? { ...i, amount } : i)) }
}
function updateObligationAmount(situation: Situation, id: string, amount: number): Situation {
  return { ...situation, obligations: situation.obligations.map((o) => (o.id === id ? { ...o, amount } : o)) }
}

export function ExplainDrawer({ dashboard, situation }: { dashboard: Dashboard; situation: Situation }) {
  const { explainOpen, purchase } = useAppState()
  const dispatch = useAppDispatch()

  if (!explainOpen) return null

  const st = dashboard.scenarios.base.stats

  return (
    <>
      <div className="scrim" onClick={() => dispatch({ type: 'CLOSE_EXPLAIN' })} />
      <aside className="drawer" aria-label="Как посчитали">
        <div className="drawer-head">
          <h2>Как посчитали?</h2>
          <button className="btn ghost sm" type="button" onClick={() => dispatch({ type: 'CLOSE_EXPLAIN' })}>
            Закрыть
          </button>
        </div>
        <div className="drawer-body">
          <div className="lesson">
            Меняйте любую цифру ниже — прогноз и график пересчитаются сразу. Считает всё движок на сервере, ничего
            не додумывается.
          </div>

          <div className="formula">
            <div>
              Самый низкий остаток — <code>{rub(st.min)}</code>, {fd(st.min_date)}.
            </div>
            <div>
              Обычные траты: {rub(situation.daily)} в день × {dashboard.horizon_days} дней ={' '}
              {rub(situation.daily * dashboard.horizon_days)}
            </div>
          </div>

          <div className="edit-table">
            <div className="er h">
              <span>Что</span>
              <span>Сумма</span>
              <span>Дата</span>
            </div>
            <div className="er">
              <div className="n">На карте сейчас</div>
              <input
                type="number"
                value={situation.balance}
                onChange={(e) =>
                  dispatch({ type: 'SET_SITUATION', situation: { ...situation, balance: Number(e.target.value) } })
                }
              />
              <span />
            </div>
            <div className="er">
              <div className="n">Обычные траты, ₽/день</div>
              <input
                type="number"
                value={situation.daily}
                onChange={(e) =>
                  dispatch({ type: 'SET_SITUATION', situation: { ...situation, daily: Number(e.target.value) } })
                }
              />
              <span />
            </div>
            {situation.incomes.map((inc) => (
              <div className="er" key={inc.id}>
                <div className="n">{inc.name}</div>
                <input
                  type="number"
                  value={inc.amount}
                  onChange={(e) => dispatch({ type: 'SET_SITUATION', situation: updateIncomeAmount(situation, inc.id, Number(e.target.value)) })}
                />
                <span>{fd(inc.date)}</span>
              </div>
            ))}
            {situation.obligations.map((ob) => (
              <div className="er" key={ob.id}>
                <div className="n">{ob.name}</div>
                <input
                  type="number"
                  value={ob.amount}
                  onChange={(e) => dispatch({ type: 'SET_SITUATION', situation: updateObligationAmount(situation, ob.id, Number(e.target.value)) })}
                />
                <span>{fd(ob.date)}</span>
              </div>
            ))}
            {purchase && (
              <div className="er">
                <div className="n">Покупка «{purchase.name}»</div>
                <input
                  type="number"
                  value={purchase.amount}
                  onChange={(e) => dispatch({ type: 'SET_PURCHASE', purchase: { ...purchase, amount: Number(e.target.value) } })}
                />
                <span>{fd(purchase.date)}</span>
              </div>
            )}
          </div>

          <div className="unknown">
            <b>Чего мы не знаем</b>
            <ul>
              {dashboard.unknowns.map((u) => (
                <li key={u}>{u}</li>
              ))}
            </ul>
          </div>

          <div className="live">
            <span className="tag fact">факт</span> — уже произошло · <span className="tag exp">ожидается</span> —
            подтверждённое поступление · <span className="tag unc">может не прийти</span> — непостоянный доход ·{' '}
            <span className="tag est">оценка</span> — посчитано по среднему
          </div>
        </div>
      </aside>
    </>
  )
}
