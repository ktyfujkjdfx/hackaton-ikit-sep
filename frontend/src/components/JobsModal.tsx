import { useAppDispatch, useAppState } from '../state/store'
import { rub } from '../lib/format'

// Настоящие вакансии мы не публикуем (договор, раздел 3): это учебные примеры с пометкой,
// чтобы было понятно, сколько примерно приносит подработка и сколько времени занимает.
const EXAMPLES = [
  { title: 'Раздача листовок у ТЦ', detail: '2 вечера · ≈ 1 500 ₽' },
  { title: 'Пеший курьер по вечерам', detail: '3–4 заказа в день · ≈ 800 ₽ за вечер' },
  { title: 'Помощь на мероприятии в вузе', detail: '1 день · ≈ 1 200 ₽' },
]

export function JobsModal() {
  const { jobsOpen, dashboard } = useAppState()
  const dispatch = useAppDispatch()
  if (!jobsOpen) return null
  const close = () => dispatch({ type: 'CLOSE_JOBS' })

  // Сумму берём из готового расчёта движка. Если расчёта нет — просто не называем её.
  const need = dashboard?.purchase?.plan?.deficit ?? dashboard?.deficit_plan?.deficit ?? null

  return (
    <>
      <div className="scrim" onClick={close} />
      <div className="modal wide" role="dialog" aria-modal="true" aria-label="Где искать подработку">
        <h3>Где искать подработку</h3>
        <p className="sub">
          {need !== null ? <>Чтобы закрыть {rub(need)}, хватит одной-двух смен. </> : null}
          Ниже — учебные примеры, чтобы прикинуть порядок сумм. Это не настоящие вакансии.
        </p>
        {EXAMPLES.map((job) => (
          <div className="example" key={job.title}>
            <span className="tag unc">Пример</span>
            <b>{job.title}</b>
            <span>{job.detail}</span>
          </div>
        ))}
        <p className="learn-note">
          Где искать на самом деле: центр карьеры вашего вуза, hh.ru, Авито Работа. Не соглашайтесь на
          работу, где просят заплатить вперёд или дать данные карты, — так выглядит мошенничество.
        </p>
        <div className="form-actions">
          <button className="btn primary" type="button" onClick={close}>
            Понятно
          </button>
        </div>
      </div>
    </>
  )
}
