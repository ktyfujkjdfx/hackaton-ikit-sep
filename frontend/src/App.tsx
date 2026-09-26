import { useEffect, useState } from 'react'
import { health } from './api/client'

function App() {
  const [status, setStatus] = useState<string>('проверяем...')

  useEffect(() => {
    health()
      .then((data) => setStatus(`ok: ${JSON.stringify(data)}`))
      .catch((err) => setStatus(`ошибка: ${err.message}`))
  }, [])

  return (
    <div>
      <h1>Дотяну — скелет</h1>
      <p>{status}</p>
    </div>
  )
}

export default App
