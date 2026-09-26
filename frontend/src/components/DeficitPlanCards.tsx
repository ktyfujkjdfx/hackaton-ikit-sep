import type { DeficitPlan } from '../types'
import { daysWord, fd, rub } from '../lib/format'

export function DeficitPlanCards({ plan }: { plan: DeficitPlan }) {
  return (
    <div className="plan">
      <div className="plan-title">Чтобы не уйти в минус, нужно закрыть {rub(plan.deficit)}</div>
      {plan.options.map((opt, i) => {
        if (opt.kind === 'postpone') {
          return (
            <div className="opt" key={i}>
              <div className="opt-top">
                <b>Перенести покупку на {fd(opt.date)}</b>
                <span className="ease easy">легко</span>
              </div>
              <span>Тогда минуса не будет.</span>
            </div>
          )
        }
        if (opt.kind === 'reduce') {
          return (
            <div className="opt" key={i}>
              <div className="opt-top">
                <b>Тратить на {rub(opt.per_day)} в день меньше</b>
                <span className={`ease ${opt.ease}`}>{opt.ease === 'easy' ? 'легко' : 'сложно'}</span>
              </div>
              <span>
                {opt.possible
                  ? `С исходной суммы в день до ${rub(opt.new_daily)}, ${daysWord(opt.days)} — до ${fd(opt.until)}.`
                  : 'Даже без обычных трат денег не хватит — этот вариант не сработает.'}
              </span>
            </div>
          )
        }
        return (
          <div className="opt" key={i}>
            <div className="opt-top">
              <b>Найти {rub(opt.amount)} до {fd(opt.by_date)}</b>
              <span className={`ease ${opt.ease}`}>{opt.ease === 'easy' ? 'легко' : 'сложно'}</span>
            </div>
            <span>
              Из них {rub(opt.first_amount)} нужны уже к {fd(opt.first_date)}.
            </span>
          </div>
        )
      })}
    </div>
  )
}
