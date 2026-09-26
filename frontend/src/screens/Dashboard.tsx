import { useEffect } from 'react'
import { getDashboard } from '../api/client'
import { TopBar } from '../components/TopBar'
import { Hero } from '../components/Hero'
import { useAppDispatch, useAppState } from '../state/store'

export function Dashboard() {
  const { situation, purchase, dashboard, personaId, loading, error } = useAppState()
  const dispatch = useAppDispatch()

  useEffect(() => {
    if (!situation || !personaId) return
    dispatch({ type: 'DASHBOARD_LOADING' })
    getDashboard(personaId, situation, purchase)
      .then((d) => dispatch({ type: 'DASHBOARD_LOADED', dashboard: d }))
      .catch(() => dispatch({ type: 'DASHBOARD_ERROR', error: 'Сервер недоступен — расчёт не выполнен' }))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [personaId])

  if (!situation) return null

  return (
    <section id="app">
      <TopBar />
      <div className="wrap app-grid">
        <div className="col">
          {error && (
            <div className="card">
              <p className="errmsg">{error}</p>
            </div>
          )}
          {loading && !dashboard && (
            <div className="card">
              <p className="sub">Считаем...</p>
            </div>
          )}
          {dashboard && <Hero dashboard={dashboard} situation={situation} />}
        </div>
      </div>
    </section>
  )
}
