import { createContext, useContext, useReducer, type Dispatch, type ReactNode } from 'react'
import type { ChatResponse, Dashboard, Purchase, Situation } from '../types'

export type Screen = 'start' | 'form' | 'app' | 'checks'

export type ChatMsg =
  | { role: 'user'; text: string }
  | { role: 'bot'; resp: ChatResponse }

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
        messages: [],
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
