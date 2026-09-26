import { useEffect, useState } from 'react'
import { DASHBOARD_MOCK_UNSUPPORTED, getDashboard } from '../api/client'
import { TopBar } from '../components/TopBar'
import { Hero } from '../components/Hero'
import { BalanceChart } from '../components/BalanceChart'
import { TypesCard } from '../components/TypesCard'
import { InlineBuy } from '../components/InlineBuy'
import { BuyCard } from '../components/BuyCard'
import { ExplainDrawer } from '../components/ExplainDrawer'
import { AskPanel } from '../components/AskPanel'
import { useAppDispatch, useAppState } from '../state/store'

export function Dashboard() {
  const { situation, purchase, dashboard, personaId, loading, error } = useAppState()
  const dispatch = useAppDispatch()
  const [retryTick, setRetryTick] = useState(0)
  const [slow, setSlow] = useState(false)

  useEffect(() => {
    if (!loading || dashboard) {
      setSlow(false)
      return
    }
    const t = setTimeout(() => setSlow(true), 4000)
    return () => clearTimeout(t)
  }, [loading, dashboard])

  useEffect(() => {
    if (!situation || !personaId) return
    let cancelled = false
    dispatch({ type: 'DASHBOARD_LOADING' })
    const timer = setTimeout(() => {
      getDashboard(personaId, situation, purchase)
        .then((d) => {
          if (!cancelled) dispatch({ type: 'DASHBOARD_LOADED', dashboard: d })
        })
        .catch((e: Error) => {
          if (cancelled) return
          const message =
            e.message === DASHBOARD_MOCK_UNSUPPORTED
              ? 'В демонстрационном режиме готовы только профиль Ани и покупки на 1000 и 3000 ₽. Включи сервер — и считаться будет всё.'
              : 'Сервер недоступен — обновить прогноз не удалось'
          dispatch({ type: 'DASHBOARD_ERROR', error: message })
        })
    }, 250)
    return () => {
      cancelled = true
      clearTimeout(timer)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [personaId, purchase, situation, dispatch, retryTick])

  if (!situation) return null

  const refreshing = loading && !!dashboard

  return (
    <section id="app">
      <TopBar />
      <div className="wrap app-grid">
        <div className="col">
          {error && (
            <div className="card">
              <p className="errmsg">
                {error}
                {dashboard ? ' — на экране прошлый расчёт, он мог устареть.' : ''}
              </p>
              <div className="hero-actions" style={{ marginTop: 8 }}>
                <button className="btn sm" type="button" onClick={() => setRetryTick((t) => t + 1)}>
                  Повторить
                </button>
              </div>
            </div>
          )}
          {loading && !dashboard && !error && (
            <div className="card">
              <p className="sub">
                {slow ? 'Просыпаемся… это может занять до минуты (бесплатный сервер спал).' : 'Считаем прогноз на 30 дней...'}
              </p>
            </div>
          )}
          {dashboard && (
            <div className={`dash-content${refreshing ? ' refreshing' : ''}`} aria-busy={refreshing}>
              {refreshing && (
                <p className="recalc-note" role="status">
                  Пересчитываем… пока показан прошлый прогноз.
                </p>
              )}
              <Hero dashboard={dashboard} situation={situation} />
              <InlineBuy />
              {dashboard.purchase && <BuyCard dashboard={dashboard} />}
              <BalanceChart dashboard={dashboard} />
              <TypesCard dashboard={dashboard} />
              <ExplainDrawer dashboard={dashboard} situation={situation} />
            </div>
          )}
        </div>
        {dashboard && <AskPanel />}
      </div>
    </section>
  )
}
