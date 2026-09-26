import type { DeficitPlan } from '../types'
import { daysWord, fd, rub } from '../lib/format'

function easeWord(ease: 'easy' | 'hard'): string {
  return ease === 'easy' ? 'легко' : 'сложно'
}

export function DeficitPlanCards({ plan }: { plan: DeficitPlan }) {
  return (
    <div className="plan">
      <div className="plan-title">Чтобы не уйти в минус, нужно закрыть {rub(plan.deficit)}</div>
      {plan.options.map((opt, i) => {
        if (opt.kind === 'postpone') {
          return (
            <div className="opt" key={i}>
              <b>Перенести покупку на {fd(opt.date)}</b>
              <span>
                Тогда минуса не будет. <i className="ease easy">легко</i>
              </span>
            </div>
          )
        }
        if (opt.kind === 'reduce') {
          return (
            <div className="opt" key={i}>
              <b>Тратить на {rub(opt.per_day)} в день меньше</b>
              <span>
                {opt.possible
                  ? `С исходной суммы в день до ${rub(opt.new_daily)}, ${daysWord(opt.days)} — до ${fd(opt.until)}. `
                  : 'Даже без обычных трат денег не хватит — этот вариант не сработает. '}
                <i className={`ease ${opt.ease}`}>{easeWord(opt.ease)}</i>
              </span>
            </div>
          )
        }
        return (
          <div className="opt" key={i}>
            <b>
              Найти {rub(opt.amount)} до {fd(opt.by_date)}
            </b>
            <span>
              Из них {rub(opt.first_amount)} нужны уже к {fd(opt.first_date)}.{' '}
              <i className={`ease ${opt.ease}`}>{easeWord(opt.ease)}</i>
            </span>
          </div>
        )
      })}
    </div>
  )
}
