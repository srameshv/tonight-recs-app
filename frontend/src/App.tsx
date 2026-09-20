import { useEffect, useState } from 'react'
import './App.css'
import { api, type User } from './api'
import { PreferencesScreen } from './PreferencesScreen'
import { TonightScreen } from './TonightScreen'

type Screen = 'tonight' | 'preferences'

function App() {
  const [users, setUsers] = useState<User[]>([])
  const [activeUserId, setActiveUserId] = useState<number | null>(null)
  const [screen, setScreen] = useState<Screen>('tonight')

  useEffect(() => {
    api.listUsers().then((u) => {
      setUsers(u)
      setActiveUserId(u[0]?.id ?? null)
    })
  }, [])

  return (
    <main className="app">
      <h1>Tonight</h1>

      <div className="profile-switch">
        <button
          className={screen === 'tonight' ? 'active' : ''}
          onClick={() => setScreen('tonight')}
        >
          What should we do tonight?
        </button>
        <button
          className={screen === 'preferences' ? 'active' : ''}
          onClick={() => setScreen('preferences')}
        >
          Preferences
        </button>
      </div>

      {screen === 'tonight' && <TonightScreen users={users} />}
      {screen === 'preferences' && (
        <PreferencesScreen
          users={users}
          activeUserId={activeUserId}
          onChangeUser={setActiveUserId}
        />
      )}
    </main>
  )
}

export default App
