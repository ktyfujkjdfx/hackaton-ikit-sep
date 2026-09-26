function parseIsoDate(iso: string): Date {
  const [y, m, d] = iso.split('-').map(Number)
  return new Date(y, m - 1, d)
}

function toIso(date: Date): string {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
}

// Смещение даты в днях относительно today (день 0 = today).
export function dayIndex(today: string, iso: string): number {
  const t = parseIsoDate(today)
  const d = parseIsoDate(iso)
  return Math.round((d.getTime() - t.getTime()) / 86400000)
}

// today + n дней, в ISO.
export function addDays(today: string, n: number): string {
  const t = parseIsoDate(today)
  return toIso(new Date(t.getFullYear(), t.getMonth(), t.getDate() + n))
}
