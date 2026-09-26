import type { Dashboard, Persona, PersonaDetail, Purchase, Situation } from '../types'
import personasFixture from './fixtures/personas.json'
import personaAnyaFixture from './fixtures/persona_anya.json'
import dashboardAnyaFixture from './fixtures/dashboard_anya.json'

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

export async function getDashboard(
  personaId: string,
  situation: Situation,
  purchase: Purchase | null,
): Promise<Dashboard> {
  if (USE_MOCKS) {
    const fixture = DASHBOARD_FIXTURES[personaId]
    if (!fixture) throw new Error(`no dashboard fixture for ${personaId}`)
    return fixture
  }
  return post<Dashboard>('/api/dashboard', { situation, purchase })
}
