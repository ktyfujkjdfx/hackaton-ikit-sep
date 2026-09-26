import { useEffect, useState } from 'react'
import { getPersona, getPersonas } from '../api/client'
import type { Persona } from '../types'
import { useAppDispatch } from '../state/store'

export function Start() {
  const dispatch = useAppDispatch()
  const [personas, setPersonas] = useState<Persona[]>([])

  useEffect(() => {
    getPersonas()
      .then(setPersonas)
      .catch(() => setPersonas([]))
  }, [])

  async function loadPersona(id: string) {
    dispatch({ type: 'LOAD_PERSONA_START', personaId: id })
    try {
      const detail = await getPersona(id)
      dispatch({ type: 'LOAD_PERSONA_DONE', personaId: id, who: detail.who, situation: detail.situation })
      dispatch({ type: 'GO', screen: 'app' })
    } catch {
      dispatch({ type: 'DASHBOARD_ERROR', error: 'Не удалось загрузить профиль' })
    }
  }

  return (
    <section id="start">
      <div className="start-card">
        <div className="brand">
          <span className="brand-mark">₽</span>Дотяну
        </div>
        <h1 className="start-title">
          Хватит ли денег <mark>до&nbsp;стипендии?</mark>
        </h1>
        <p className="start-sub">
          Проверь покупку до того, как потратишь. Покажем, когда её можно сделать без минуса, и объясним, как
          посчитали.
        </p>
        <div className="feats">
          <div className="feat">
            <b>Когда можно купить</b>
            <span>Не «да/нет», а дата, с которой покупка не уведёт в минус</span>
          </div>
          <div className="feat">
            <b>Постоянное и разовое</b>
            <span>Отделяем стипендию от подработки, общагу от такси</span>
          </div>
          <div className="feat">
            <b>План выхода из минуса</b>
            <span>Три варианта с пометкой «легко» или «сложно»</span>
          </div>
          <div className="feat">
            <b>Честно о точности</b>
            <span>У каждой суммы метка: факт, ожидается или оценка</span>
          </div>
        </div>
        <div className="choices">
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
          <span>Только придуманные данные. Не вводи номер карты, пароли и коды из СМС.</span>
        </p>
      </div>
    </section>
  )
}
