import { AppStateProvider, useAppState } from './state/store'
import { Start } from './screens/Start'
import { Dashboard } from './screens/Dashboard'

function Screens() {
  const { screen } = useAppState()

  if (screen === 'app') return <Dashboard />
  return <Start />
}

function App() {
  return (
    <AppStateProvider>
      <Screens />
    </AppStateProvider>
  )
}

export default App
