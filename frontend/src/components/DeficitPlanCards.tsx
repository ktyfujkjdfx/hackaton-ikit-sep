import type { DeficitPlan } from '../types'
import { daysWord, fd, rub } from '../lib/format'

function easeWord(ease: 'easy' | 'hard'): string {
  return ease === 'easy' ? 'легко' : 'сложно'
}

export function DeficitPlanCards({ plan }: { plan: DeficitPlan }) {
  return (
    <div className="plan">
      <div className="plan-title">Чтобы остаться в границах бюджета, нужно закрыть {rub(plan.deficit)}</div>
      {plan.options.map((opt, i) => {
        if (opt.kind === 'postpone') {
          return (
            <div className="opt" key={i}>
              <b>Перенести покупку на {fd(opt.date)}</b>
              <span>
                Тогда превышения бюджета не будет. <i className="ease easy">легко</i>
              </span>
            </div>
          )
        }
        if (opt.kind === 'reduce') {
          return (
            <div className="opt" key={i}>
              <b>Сократить расходы на {rub(opt.per_day)} в день</b>
              <span>
                {opt.possible
                  ? `С сегодняшнего дня по ${fd(opt.until)} (${daysWord(opt.days)}). Обычные траты станут ${rub(opt.new_daily)} в день. `
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
