import type { Dashboard } from '../types'
import { fd, rub } from '../lib/format'

export function TypesCard({ dashboard }: { dashboard: Dashboard }) {
  const mt = dashboard.money_types

  return (
    <div className="card" id="types-card">
      <div className="eyebrow">
        Постоянное и разовое
      </div>
      <h3 style={{ marginTop: 6, fontSize: 17 }}>
        Что у вас постоянное, а что нет — ближайшие {dashboard.horizon_days} дней
      </h3>
      <p className="sub">
        Постоянные деньги мы ставим в прогноз на точную дату. Разовые — либо как отдельный вариант, либо как среднее
        в день.
      </p>
      <div className="types">
        <div className="type inc-s">
          <h4>
            <span>Постоянный доход</span>
            <span className="tag exp">ожидается</span>
          </h4>
          <span className="sum num" style={{ color: 'var(--money-fixed)' }}>
            +{rub(mt.stable_income.total)}
          </span>
          {mt.stable_income.items.length ? (
            <ul>
              {mt.stable_income.items.map((i) => (
                <li key={i.id}>
                  {i.name} — {rub(i.amount)}, {fd(i.date)}
                </li>
              ))}
            </ul>
          ) : (
            <span className="how">Нет подтверждённых поступлений в ближайший месяц.</span>
          )}
          <span className="how">На графике — сплошная линия, приходит по графику.</span>
        </div>

        <div className="type inc-u">
          <h4>
            <span>Непостоянный доход</span>
            <span className="tag unc">может не прийти</span>
          </h4>
          <span className="sum num" style={{ color: 'var(--money-variable)' }}>
            {mt.unstable_income.items.length ? `+${rub(mt.unstable_income.total)}` : 'нет'}
          </span>
          {mt.unstable_income.items.length ? (
            <>
              <ul>
                {mt.unstable_income.items.map((i) => (
                  <li key={i.id}>
                    {i.name} — {rub(i.amount)}, {fd(i.date)}
                  </li>
                ))}
              </ul>
              <span className="how">На графике — пунктир. Показываем два варианта: если придёт и если нет.</span>
            </>
          ) : (
            <span className="how">Если есть подработка без графика — добавьте её, покажем два варианта прогноза.</span>
          )}
        </div>

        <div className="type out-s">
          <h4>
            <span>Постоянные расходы</span>
            <span className="tag reg">обязательные</span>
          </h4>
          <span className="sum num" style={{ color: 'var(--money-fixed)' }}>
            &minus;{rub(mt.stable_expenses.total)}
          </span>
          {mt.stable_expenses.items.length ? (
            <ul>
              {mt.stable_expenses.items.map((o) => (
                <li key={o.id}>
                  {o.name} — {rub(o.amount)}, {fd(o.date)}
                </li>
              ))}
            </ul>
          ) : (
            <span className="how">Нет обязательных платежей.</span>
          )}
          <span className="how">Вычитаем в день платежа. На графике — чёрные точки.</span>
        </div>

        <div className="type out-v">
          <h4>
            <span>Непостоянные расходы</span>
            <span className="tag est">оценка</span>
          </h4>
          <span className="sum num" style={{ color: 'var(--money-variable)' }}>
            &minus;{rub(mt.variable_expenses.total)}
          </span>
          <ul>
            <li>
              Обычные траты: {rub(mt.variable_expenses.daily)} × {mt.variable_expenses.days} дней ={' '}
              {rub(mt.variable_expenses.daily * mt.variable_expenses.days)}
            </li>
            {mt.variable_expenses.one_off.map((s) => (
              <li key={s.id}>
                {s.name} — {rub(s.amount)}, {fd(s.date)} <span className="tag fact">факт</span>
              </li>
            ))}
          </ul>
          <span className="how">Еду, такси и кафе не знаем по датам — берём среднее в день.</span>
        </div>
      </div>
      <div className="types-foot">
        <span>
          Надёжная часть: на карте + постоянный доход − постоянные расходы = <b>{rub(mt.reliable_total)}</b>.
        </span>
        <span>
          Из неё покрываются обычные траты ≈ <b>{rub(mt.variable_expenses.total)}</b>
          {mt.unstable_income.items.length ? `, и, возможно, поможет непостоянный доход +${rub(mt.unstable_income.total)}` : ''}.
        </span>
      </div>
    </div>
  )
}
