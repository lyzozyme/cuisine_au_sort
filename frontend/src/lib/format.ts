import type { Unit } from '../api/types'

const numberFormat = new Intl.NumberFormat('fr-FR', { maximumFractionDigits: 3 })

const PLURALIZABLE: Partial<Record<Unit, [string, string]>> = {
  piece: ['pièce', 'pièces'],
  pinch: ['pincée', 'pincées'],
}

const SPOONS: Partial<Record<Unit, string>> = {
  tsp: 'c. à café',
  tbsp: 'c. à soupe',
}

/** « 1500 g » -> « 1,5 kg », « 3 piece » -> « 3 pièces », « 2 tbsp » -> « 2 c. à soupe ». */
export function formatQuantity(quantity: number, unit: Unit): string {
  if (unit === 'g' && quantity >= 1000) return `${numberFormat.format(quantity / 1000)} kg`
  if (unit === 'ml' && quantity >= 1000) return `${numberFormat.format(quantity / 1000)} l`
  const value = numberFormat.format(quantity)
  const plural = PLURALIZABLE[unit]
  if (plural) return `${value} ${quantity > 1 ? plural[1] : plural[0]}`
  return `${value} ${SPOONS[unit] ?? unit}`
}

/** Date ISO (AAAA-MM-JJ) interprétée en date locale, sans décalage de fuseau. */
export function parseIsoDate(iso: string): Date {
  const [year, month, day] = iso.split('-').map(Number)
  return new Date(year, month - 1, day)
}

export function toIsoDate(date: Date): string {
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
}

const longDate = new Intl.DateTimeFormat('fr-FR', { weekday: 'long', day: 'numeric', month: 'long' })
const fullDate = new Intl.DateTimeFormat('fr-FR', { day: 'numeric', month: 'long', year: 'numeric' })

/** « lundi 16 novembre » */
export function formatDayDate(iso: string): string {
  return longDate.format(parseIsoDate(iso))
}

/** « Semaine du 16 novembre 2026 » */
export function formatWeek(weekStart: string): string {
  return `Semaine du ${fullDate.format(parseIsoDate(weekStart))}`
}

/** Lundi de la semaine à venir (aujourd'hui si on est lundi), même règle que le backend. */
export function upcomingMonday(today: Date = new Date()): string {
  const daysUntilMonday = (8 - today.getDay()) % 7 // getDay : 0 = dimanche, 1 = lundi
  const monday = new Date(today.getFullYear(), today.getMonth(), today.getDate() + daysUntilMonday)
  return toIsoDate(monday)
}

export function isMonday(iso: string): boolean {
  return parseIsoDate(iso).getDay() === 1
}

/** « dessert, Rapide ,, » -> ["dessert", "rapide"] (le backend normalise aussi en minuscules). */
export function parseTags(text: string): string[] {
  const tags = text
    .split(',')
    .map((tag) => tag.trim().toLowerCase())
    .filter(Boolean)
  return [...new Set(tags)]
}
