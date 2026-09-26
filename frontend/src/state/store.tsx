import { createContext, useContext, useReducer, type Dispatch, type ReactNode } from 'react'
import type { Dashboard, Purchase, Situation } from '../types'

export type Screen = 'start' | 'form' | 'app' | 'checks'

// Заглушка до готовности /api/chat у роли B: без свободного текста и NLU,
// только явные кнопки/поля. Когда подключим B — заменим на ChatResponse.
export type ChatMsg = { role: 'user' | 'bot'; text: string }

export type DeferredPurchase = { name: string; amount: number; safe_date: string }

export type State = {
  screen: Screen
  who: string
  personaId: string | null
  situation: Situation | null
  purchase: Purchase | null
  deferred: DeferredPurchase[]
  messages: ChatMsg[]
  dashboard: Dashboard | null
  loading: boolean
  error: string | null
  explainOpen: boolean
}

export const initialState: State = {
  screen: 'start',
  who: '',
  personaId: null,
  situation: null,
  purchase: null,
  deferred: [],
  messages: [],
  dashboard: null,
  loading: false,
  error: null,
  explainOpen: false,
}

export type Action =
  | { type: 'GO'; screen: Screen }
  | { type: 'LOAD_PERSONA_START'; personaId: string }
  | { type: 'LOAD_PERSONA_DONE'; personaId: string; who: string; situation: Situation }
  | { type: 'SET_PURCHASE'; purchase: Purchase | null }
  | { type: 'DASHBOARD_LOADING' }
  | { type: 'DASHBOARD_LOADED'; dashboard: Dashboard }
  | { type: 'DASHBOARD_ERROR'; error: string }
  | { type: 'ADD_MESSAGE'; message: ChatMsg }
  | { type: 'ADD_DEFERRED'; deferred: DeferredPurchase }
  | { type: 'SET_SITUATION'; situation: Situation }
  | { type: 'OPEN_EXPLAIN' }
  | { type: 'CLOSE_EXPLAIN' }

function reducer(state: State, action: Action): State {
  switch (action.type) {
    case 'GO':
      return { ...state, screen: action.screen }
    case 'LOAD_PERSONA_START':
      return { ...state, loading: true, error: null, personaId: action.personaId }
    case 'LOAD_PERSONA_DONE':
      return {
        ...state,
        loading: false,
        who: action.who,
        situation: action.situation,
        purchase: null,
        deferred: [],
        messages: [
          {
            role: 'bot',
            text: 'Привет! Пока без свободного текста — жми кнопки ниже или «+ Добавить трату или доход».',
          },
        ],
        dashboard: null,
      }
    case 'SET_PURCHASE':
      return { ...state, purchase: action.purchase }
    case 'DASHBOARD_LOADING':
      return { ...state, loading: true, error: null }
    case 'DASHBOARD_LOADED':
      return { ...state, loading: false, dashboard: action.dashboard }
    case 'DASHBOARD_ERROR':
      return { ...state, loading: false, error: action.error }
    case 'ADD_MESSAGE':
      return { ...state, messages: [...state.messages, action.message] }
    case 'ADD_DEFERRED':
      return { ...state, deferred: [...state.deferred, action.deferred] }
    case 'SET_SITUATION':
      return { ...state, situation: action.situation }
    case 'OPEN_EXPLAIN':
      return { ...state, explainOpen: true }
    case 'CLOSE_EXPLAIN':
      return { ...state, explainOpen: false }
    default:
      return state
  }
}

const StateContext = createContext<State>(initialState)
const DispatchContext = createContext<Dispatch<Action>>(() => {})

export function AppStateProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(reducer, initialState)
  return (
    <StateContext.Provider value={state}>
      <DispatchContext.Provider value={dispatch}>{children}</DispatchContext.Provider>
    </StateContext.Provider>
  )
}

export function useAppState() {
  return useContext(StateContext)
}

export function useAppDispatch() {
  return useContext(DispatchContext)
}
