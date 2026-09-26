import { useAppDispatch, useAppState } from '../state/store'
import { Brand } from './Brand'

export function TopBar() {
  const { who } = useAppState()
  const dispatch = useAppDispatch()

  return (
    <header className="topbar">
      <div className="wrap">
        <Brand />
        <span className="demo-chip">Демо: 27 сентября 2026</span>
        {who && <span className="chip">{who}</span>}
        <span className="spacer" />
        <button className="btn ghost sm" type="button" onClick={() => dispatch({ type: 'OPEN_EXPLAIN' })}>
          Как посчитали?
        </button>
        <button className="btn ghost sm" type="button" onClick={() => dispatch({ type: 'GO', screen: 'checks' })}>
          Как мы проверяли
        </button>
        <button className="btn sm" type="button" onClick={() => dispatch({ type: 'GO', screen: 'start' })}>
          Сменить профиль
        </button>
      </div>
    </header>
  )
}
