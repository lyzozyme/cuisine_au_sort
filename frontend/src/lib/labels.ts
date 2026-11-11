import type { Aisle, InputUnit, Meal, Unit, Visibility } from '../api/types'

/** Libellés français des valeurs d'énumération de l'API (l'ordre des clés = ordre d'affichage). */

export const UNIT_LABELS: Record<Unit, string> = {
  g: 'g',
  ml: 'ml',
  piece: 'pièce',
  tsp: 'c. à café',
  tbsp: 'c. à soupe',
  pinch: 'pincée',
}

export const INPUT_UNIT_LABELS: Record<InputUnit, string> = {
  g: 'g',
  kg: 'kg',
  ml: 'ml',
  cl: 'cl',
  dl: 'dl',
  l: 'l',
  piece: 'pièce',
  tsp: 'c. à café',
  tbsp: 'c. à soupe',
  pinch: 'pincée',
}

export const AISLE_LABELS: Record<Aisle, string> = {
  produce: 'Fruits et légumes',
  meat: 'Boucherie',
  fish: 'Poissonnerie',
  dairy: 'Crèmerie',
  bakery: 'Boulangerie',
  frozen: 'Surgelés',
  grocery: 'Épicerie',
  spices: 'Épices et condiments',
  beverages: 'Boissons',
  other: 'Autre',
}

export const MEAL_LABELS: Record<Meal, string> = {
  lunch: 'Déjeuner',
  dinner: 'Dîner',
}

export const VISIBILITY_LABELS: Record<Visibility, string> = {
  private: 'Privée',
  shared: 'Partagée',
  public: 'Publique',
}

/** Liste [valeur, libellé] pour alimenter un <select>. */
export function options<K extends string>(labels: Record<K, string>): [K, string][] {
  return Object.entries(labels) as [K, string][]
}
