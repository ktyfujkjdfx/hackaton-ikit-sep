import type { ReactNode } from 'react'
import type { Dashboard, Situation } from '../types'
import { daysWord, fd, rub } from '../lib/format'

type Props = {
  dashboard: Dashboard
  situation: Situation
}

function titleFor(name: string): string {
  return /стипенд/i.test(name) ? 'До стипендии' : `До поступления «${name}»`
}

export function Hero({ dashboard, situation }: Props) {
  const { headline } = dashboard
  const pessimistic = dashboard.scenarios.pessimistic

  let pillClass = 'unknown'
  let pillText = 'Нет даты дохода'
  let verdict: ReactNode

  if (!headline.next_income) {
    verdict =
      headline.first_negative_date !== null ? (
        <>
          Без новых поступлений деньги закончатся <b className="bad">{fd(headline.first_negative_date)}</b>.
        </>
      ) : (
        <>
          Без новых поступлений на 30 дней хватит: минимум <b>{rub(headline.min_balance)}</b>.
        </>
      )
  } else if (headline.state === 'deficit') {
    pillClass = 'bad'
    pillText = '⚠ Может не хватить'
    verdict = (
      <>
        Может не хватить <b className="bad">{rub(headline.max_deficit)}</b>. Минус начнётся{' '}
        <b>{headline.first_negative_date ? fd(headline.first_negative_date) : '—'}</b>.
      </>
    )
  } else if (headline.state === 'depends' && pessimistic?.stats.first_negative_date) {
    pillClass = 'tight'
    pillText = 'Зависит от подработки'
    verdict = (
      <>
        Хватит, <b>если придёт подработка</b>. Если нет — не хватит{' '}
        <b className="bad">{rub(pessimistic.stats.max_deficit)}</b> с {fd(pessimistic.stats.first_negative_date)}.
      </>
    )
  } else if (headline.state === 'tight') {
    pillClass = 'tight'
    pillText = 'Впритык'
    verdict = (
      <>
        Хватит впритык: к <b>{fd(headline.min_date)}</b> останется <b>{rub(headline.min_balance)}</b>. Это{' '}
        {situation.daily > 0 ? daysWord(headline.days_of_spending_left) : ''} обычных трат.
      </>
    )
  } else {
    pillClass = 'ok'
    pillText = '✓ Хватит'
    verdict = (
      <>
        Хватит. Самый низкий остаток — <b>{rub(headline.min_balance)}</b>, {fd(headline.min_date)}.
      </>
    )
  }

  return (
    <div className="card hero">
      <div className="hero-top">
        <span className={`state-pill ${pillClass}`}>{pillText}</span>
        {headline.next_income && !headline.next_income.confirmed && (
          <span className="tag unc">поступление может не прийти</span>
        )}
      </div>
      <div className="days">
        {headline.next_income ? (
          <>
            {titleFor(headline.next_income.name)} <span className="n">{daysWord(headline.next_income.days)}</span>
          </>
        ) : (
          'Не знаем, когда придут деньги'
        )}
      </div>
      <p className="verdict">{verdict}</p>
      <p className="caveat">
        Это прогноз, а не гарантия. Обычные траты — {rub(situation.daily)} в день, оценка{' '}
        {situation.categories ? 'по истории за 2 месяца' : 'из анкеты'}.
      </p>
    </div>
  )
}
