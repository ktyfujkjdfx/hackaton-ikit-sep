const MONTHS_GEN = [
  'января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
  'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря',
]
const MONTHS_SHORT = [
  'янв', 'фев', 'мар', 'апр', 'мая', 'июн',
  'июл', 'авг', 'сен', 'окт', 'ноя', 'дек',
]

// Даты из API — строки "YYYY-MM-DD". Парсим как локальную дату, не как UTC.
function parseIsoDate(iso: string): Date {
  const [y, m, d] = iso.split('-').map(Number)
  return new Date(y, m - 1, d)
}

export function rub(v: number): string {
  const sign = v < 0 ? '−' : ''
  const formatted = new Intl.NumberFormat('ru-RU').format(Math.abs(Math.round(v)))
  return `${sign}${formatted} ₽`
}

export function fd(iso: string, withYearIfOther = true): string {
  const date = parseIsoDate(iso)
  const now = new Date()
  const year = withYearIfOther && date.getFullYear() !== now.getFullYear() ? ` ${date.getFullYear()}` : ''
  return `${date.getDate()} ${MONTHS_GEN[date.getMonth()]}${year}`
}

export function fdShort(iso: string): string {
  const date = parseIsoDate(iso)
  return `${date.getDate()} ${MONTHS_SHORT[date.getMonth()]}`
}

function pluralForm(n: number, one: string, few: string, many: string): string {
  const abs = Math.abs(n) % 100
  const last = abs % 10
  if (abs > 10 && abs < 20) return many
  if (last > 1 && last < 5) return few
  if (last === 1) return one
  return many
}

export function daysWord(n: number): string {
  return `${n} ${pluralForm(n, 'день', 'дня', 'дней')}`
}
