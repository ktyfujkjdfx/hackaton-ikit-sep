const BASE = import.meta.env.VITE_API_URL ?? ''

export async function health() {
  const res = await fetch(`${BASE}/api/health`)
  if (!res.ok) {
    throw new Error(`health check failed: ${res.status}`)
  }
  return res.json()
}
