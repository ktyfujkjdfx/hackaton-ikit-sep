import { useEffect } from 'react'
import { DASHBOARD_MOCK_UNSUPPORTED, getDashboard } from '../api/client'
import { TopBar } from '../components/TopBar'
import { Hero } from '../components/Hero'
import { BalanceChart } from '../components/BalanceChart'
import { TypesCard } from '../components/TypesCard'
import { InlineBuy } from '../components/InlineBuy'
import { BuyCard } from '../components/BuyCard'
import { useAppDispatch, useAppState } from '../state/store'

export function Dashboard() {
  const { situation, purchase, dashboard, personaId, loading, error } = useAppState()
  const dispatch = useAppDispatch()

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
              ? `В демо-режиме посчитаны только суммы 1000 и 3000 ₽ — остальные подключим вместе с /api/dashboard роли A.`
              : 'Сервер недоступен — расчёт не выполнен'
          dispatch({ type: 'DASHBOARD_ERROR', error: message })
        })
    }, 250)
    return () => {
      cancelled = true
      clearTimeout(timer)
    }
  }, [personaId, purchase, situation, dispatch])

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
          {dashboard && (
            <>
              <Hero dashboard={dashboard} situation={situation} />
              <InlineBuy />
              {dashboard.purchase && <BuyCard dashboard={dashboard} />}
              <BalanceChart dashboard={dashboard} />
              <TypesCard dashboard={dashboard} />
            </>
          )}
        </div>
      </div>
    </section>
  )
}
