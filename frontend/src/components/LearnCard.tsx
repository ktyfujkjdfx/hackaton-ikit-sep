import { useAppDispatch, useAppState } from '../state/store'

const FINCULT = 'https://fincult.info'

/** Короткая карточка на дашборде. Ни одной суммы пользователя — текст одинаковый для всех. */
export function LearnCard() {
  const dispatch = useAppDispatch()

  return (
    <div className="learn">
      <b>Как устроены накопления и инвестиции?</b>
      <p>
        Сначала — подушка безопасности, потом накопления на цель, и только потом инвестиции. Инвестиции
        могут принести доход, но могут и уменьшиться: гарантий нет.
      </p>
      <div className="learn-actions">
        <button className="btn sm" type="button" onClick={() => dispatch({ type: 'OPEN_LEARN' })}>
          Разобраться по шагам
        </button>
        <a className="btn sm ghost" href={FINCULT} target="_blank" rel="noopener noreferrer">
          fincult.info — сайт Банка России
        </a>
      </div>
    </div>
  )
}

/** Полный разбор. Открывается с дашборда и из чата, когда спрашивают «куда вложить». */
export function LearnModal() {
  const { learnOpen } = useAppState()
  const dispatch = useAppDispatch()
  if (!learnOpen) return null
  const close = () => dispatch({ type: 'CLOSE_LEARN' })

  return (
    <>
      <div className="scrim" onClick={close} />
      <div className="modal wide" role="dialog" aria-modal="true" aria-label="Как устроены накопления и инвестиции">
        <h3>Как устроены накопления и инвестиции</h3>
        <ol className="learn-steps">
          <li>
            <b>Подушка безопасности.</b> Запас на несколько месяцев обычных трат — на случай, если доход
            пропадёт. Её держат там, откуда деньги можно забрать в любой день.
          </li>
          <li>
            <b>Накопления на цель.</b> Деньги на конкретную покупку к конкретному сроку. Здесь важна не
            доходность, а то, что сумма будет на месте к нужной дате.
          </li>
          <li>
            <b>Инвестиции.</b> Только на деньги, которые не понадобятся в ближайшее время. Они могут
            принести доход, а могут и уменьшиться — гарантий нет, и это нормальное свойство инструмента,
            а не риск конкретного приложения.
          </li>
        </ol>
        <div className="example">
          <b>Т-Инвестиции — следующий шаг, когда первые два пункта закрыты</b>
          <span>
            Брокерский счёт открывают, когда есть подушка и закрыты цели на ближайший год. Вводить в
            него деньги, которые нужны на жизнь до стипендии, не стоит: их может не оказаться на месте
            в нужный день.
          </span>
        </div>
        <p className="learn-note">
          Мы учим, а не советуем: этот текст одинаковый для всех и не использует ваши суммы. Какой
          инструмент выбрать — решаете вы.
        </p>
        <div className="form-actions">
          <button className="btn primary" type="button" onClick={close}>
            Понятно
          </button>
          <a className="btn ghost" href={FINCULT} target="_blank" rel="noopener noreferrer">
            Читать на fincult.info
          </a>
        </div>
      </div>
    </>
  )
}
