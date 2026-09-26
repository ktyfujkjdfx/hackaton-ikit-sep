import { useEffect, useState } from 'react'
import { getPersona, getPersonas } from '../api/client'
import type { Persona } from '../types'
import { useAppDispatch } from '../state/store'
import { Brand } from '../components/Brand'

export function Start() {
  const dispatch = useAppDispatch()
  const [personas, setPersonas] = useState<Persona[]>([])
  const [personasLoading, setPersonasLoading] = useState(true)
  const [personasError, setPersonasError] = useState<string | null>(null)
  const [pickError, setPickError] = useState<string | null>(null)

  useEffect(() => {
    getPersonas()
      .then((p) => {
        setPersonas(p)
        setPersonasLoading(false)
      })
      .catch(() => {
        setPersonasError('Не удалось загрузить список демо-профилей. Можно всё равно заполнить анкету.')
        setPersonasLoading(false)
      })
  }, [])

  async function loadPersona(id: string) {
    setPickError(null)
    dispatch({ type: 'LOAD_PERSONA_START', personaId: id })
    try {
      const detail = await getPersona(id)
      dispatch({ type: 'LOAD_PERSONA_DONE', personaId: id, who: detail.who, situation: detail.situation })
      dispatch({ type: 'GO', screen: 'app' })
    } catch {
      setPickError('Не удалось загрузить профиль — сервер недоступен. Попробуйте ещё раз.')
    }
  }

  return (
    <section id="start">
      <div className="start-card">
        <Brand />
        <h1 className="start-title">
          ФинКом — сервис по <mark>распределению&nbsp;дохода</mark>
        </h1>
        <p className="start-sub">Посчитайте сегодня, чтобы не жалеть завтра</p>
        <div className="feats">
          <div className="feat">
            <b>Когда можно купить</b>
            <span>Не «да/нет», а дата, с которой покупка не выведет за границы бюджета</span>
          </div>
          <div className="feat">
            <b>Постоянное и разовое</b>
            <span>
              Разделяет стипендию и разовые поступления, обязательные платежи и повседневные траты
            </span>
          </div>
          <div className="feat">
            <b>Как остаться в границах бюджета</b>
            <span>Три варианта с пометкой «легко» или «сложно»</span>
          </div>
          <div className="feat">
            <b>Честно о точности</b>
            <span>У каждой суммы метка: факт, ожидается или оценка</span>
          </div>
        </div>
        {pickError && <p className="errmsg">{pickError}</p>}
        <div className="choices">
          {personasLoading && <p className="sub">Загружаем демо-профили...</p>}
          {personasError && <p className="errmsg">{personasError}</p>}
          {personas.map((p) => (
            <button key={p.id} className="choice main" type="button" onClick={() => loadPersona(p.id)}>
              <span className="ico">{p.title.charAt(0)}</span>
              <span>
                <b>Демо: {p.title}</b>
                <span>{p.subtitle}</span>
              </span>
              <span className="arrow">→</span>
            </button>
          ))}
          <button className="choice" type="button" onClick={() => dispatch({ type: 'GO', screen: 'form' })}>
            <span className="ico">+</span>
            <span>
              <b>Заполнить свою анкету</b>
              <span>5 вопросов, около 2 минут</span>
            </span>
            <span className="arrow">→</span>
          </button>
        </div>
        <p className="safe-note">
          <span className="tag est">Учебный режим</span>
          <span>
            Используйте только придуманные данные. Не указывайте номер карты, пароли и коды из СМС.
          </span>
        </p>
      </div>
    </section>
  )
}
