import type { Dashboard, Situation } from '../types'
import { daysWord, fd, rub } from '../lib/format'

// Всё, что здесь показано, посчитал движок и прислал в поле goal ответа /api/dashboard.
// Компонент только раскладывает готовые числа — сам он ничего не вычисляет.
export function GoalCard({ dashboard, situation }: { dashboard: Dashboard; situation: Situation }) {
  const plan = dashboard.goal
  const goal = situation.goal
  if (!plan || !goal) return null

  const saved = Math.min(goal.current, goal.target)
  const percent = goal.target > 0 ? Math.round((saved / goal.target) * 100) : 0
  const inTime = plan.late_days !== null && plan.late_days <= 0

  return (
    <div className="card goal-card">
      <div className="eyebrow">Накопительная цель</div>
      <h3>{goal.name}</h3>

      <div className="goal-row">
        <span className="num">
          <b>{rub(saved)}</b> из {rub(goal.target)}
        </span>
        <span className="sub">срок — {fd(goal.date)}</span>
      </div>
      <div className="goal-bar" role="img" aria-label={`Накоплено ${percent}%`}>
        <div className="fill" style={{ width: `${Math.min(100, percent)}%` }} />
      </div>

      <div className="kfacts">
        <div>
          <span>Откладывается в месяц</span>
          <b className="num">{rub(plan.monthly_surplus)}</b>
        </div>
        <div>
          <span>Осталось накопить</span>
          <b className="num">{rub(plan.remaining)}</b>
        </div>
        <div>
          <span>Накопите к</span>
          <b className={plan.eta ? (inTime ? 'good' : 'bad') : undefined}>
            {plan.eta ? fd(plan.eta) : 'при таком темпе — не накопится'}
          </b>
        </div>
      </div>

      <p className="caveat">
        {plan.eta === null ? (
          <>
            При нынешнем темпе цель не закрывается: чтобы успеть к сроку, нужно откладывать{' '}
            {plan.need_monthly !== null ? <b>{rub(plan.need_monthly)} в месяц</b> : 'больше'}.
          </>
        ) : inTime ? (
          <>
            Успеваете к сроку. Темп — {rub(plan.per_day)} в день, это разница между доходами и
            тратами, а не отдельный платёж.
          </>
        ) : (
          <>
            Это на <b>{daysWord(plan.late_days ?? 0)}</b> позже срока.{' '}
            {plan.need_monthly !== null ? (
              <>
                Чтобы успеть, нужно откладывать <b>{rub(plan.need_monthly)} в месяц</b> вместо{' '}
                {rub(plan.monthly_surplus)}.
              </>
            ) : null}
          </>
        )}{' '}
        Расчёт по текущим доходам и тратам, это прогноз, а не гарантия.
      </p>

      {plan.eta_with_purchase && plan.shift_days ? (
        <p className="caveat bad-note">
          С учётом проверяемой покупки цель сдвигается на <b>{daysWord(plan.shift_days)}</b> — до{' '}
          {fd(plan.eta_with_purchase)}.
        </p>
      ) : null}
    </div>
  )
}
