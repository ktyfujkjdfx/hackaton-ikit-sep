import type { ChecksResult, Dashboard, Persona, PersonaDetail, Purchase, Situation } from '../types'
import personasFixture from './fixtures/personas.json'
import personaAnyaFixture from './fixtures/persona_anya.json'
import dashboardAnyaFixture from './fixtures/dashboard_anya.json'
import dashboardAnyaBuy3000Fixture from './fixtures/dashboard_anya_buy3000.json'
import dashboardAnyaBuy1000Fixture from './fixtures/dashboard_anya_buy1000.json'

const BASE = import.meta.env.VITE_API_URL ?? ''
const USE_MOCKS = import.meta.env.VITE_USE_MOCKS === '1'

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    throw new Error(`${path} failed: ${res.status}`)
  }
  return res.json()
}

export async function health() {
  const res = await fetch(`${BASE}/api/health`)
  if (!res.ok) {
    throw new Error(`health check failed: ${res.status}`)
  }
  return res.json()
}

export async function getPersonas(): Promise<Persona[]> {
  if (USE_MOCKS) return personasFixture as Persona[]
  const res = await fetch(`${BASE}/api/personas`)
  if (!res.ok) throw new Error(`personas failed: ${res.status}`)
  return res.json()
}

const PERSONA_FIXTURES: Record<string, PersonaDetail> = {
  anya: personaAnyaFixture as PersonaDetail,
}

export async function getPersona(id: string): Promise<PersonaDetail> {
  if (USE_MOCKS) {
    const fixture = PERSONA_FIXTURES[id]
    if (!fixture) throw new Error(`no fixture for persona ${id}`)
    return fixture
  }
  const res = await fetch(`${BASE}/api/personas/${id}`)
  if (!res.ok) throw new Error(`persona ${id} failed: ${res.status}`)
  return res.json()
}

const DASHBOARD_FIXTURES: Record<string, Dashboard> = {
  anya: dashboardAnyaFixture as Dashboard,
}

// Мок покрывает только суммы из раздела 8 CONTRACT.md (13 эталонных проверок).
// Другие суммы вернут DASHBOARD_MOCK_UNSUPPORTED — реальный расчёт появится с /api/dashboard от роли A.
const DASHBOARD_PURCHASE_FIXTURES: Record<string, Record<number, Dashboard>> = {
  anya: {
    3000: dashboardAnyaBuy3000Fixture as Dashboard,
    1000: dashboardAnyaBuy1000Fixture as Dashboard,
  },
}

export const DASHBOARD_MOCK_UNSUPPORTED = 'DASHBOARD_MOCK_UNSUPPORTED'

export async function getDashboard(
  personaId: string,
  situation: Situation,
  purchase: Purchase | null,
): Promise<Dashboard> {
  if (USE_MOCKS) {
    if (purchase) {
      const fixture = DASHBOARD_PURCHASE_FIXTURES[personaId]?.[purchase.amount]
      if (!fixture) throw new Error(DASHBOARD_MOCK_UNSUPPORTED)
      return fixture
    }
    const fixture = DASHBOARD_FIXTURES[personaId]
    if (!fixture) throw new Error(DASHBOARD_MOCK_UNSUPPORTED)
    return fixture
  }
  return post<Dashboard>('/api/dashboard', { situation, purchase })
}

export async function getChecks(): Promise<ChecksResult> {
  const res = await fetch(`${BASE}/api/checks`)
  if (!res.ok) throw new Error(`checks failed: ${res.status}`)
  return res.json()
}
