import { AppStateProvider, useAppState } from './state/store'
import { Start } from './screens/Start'
import { Form } from './screens/Form'
import { Dashboard } from './screens/Dashboard'
import { Checks } from './screens/Checks'

function Screens() {
  const { screen } = useAppState()

  if (screen === 'app') return <Dashboard />
  if (screen === 'form') return <Form />
  if (screen === 'checks') return <Checks />
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
