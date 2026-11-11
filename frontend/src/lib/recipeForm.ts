/**
 * État du formulaire de recette et conversion vers la requête API.
 * Logique pure (sans React) pour pouvoir être testée unitairement.
 */
import type { InputUnit, Recipe, RecipeCreate, Visibility } from '../api/types'
import { parseTags } from './format'

export type IngredientLine = {
  key: number
  ingredientId: string
  quantity: string
  /** '' = unité par défaut de l'ingrédient */
  unit: InputUnit | ''
}

export type RecipeFormState = {
  name: string
  description: string
  servings: string
  instructions: string
  tags: string
  visibility: Visibility
  lines: IngredientLine[]
}

let nextLineKey = 0

export function emptyLine(): IngredientLine {
  return { key: nextLineKey++, ingredientId: '', quantity: '', unit: '' }
}

export function emptyRecipeForm(): RecipeFormState {
  return {
    name: '',
    description: '',
    servings: '2',
    instructions: '',
    tags: '',
    visibility: 'private',
    lines: [emptyLine()],
  }
}

export function recipeToForm(recipe: Recipe): RecipeFormState {
  return {
    name: recipe.name,
    description: recipe.description ?? '',
    servings: String(recipe.servings),
    instructions: recipe.instructions,
    tags: recipe.tags.join(', '),
    visibility: recipe.visibility,
    lines: recipe.ingredients.map((line) => ({
      key: nextLineKey++,
      ingredientId: line.ingredient.id,
      quantity: String(line.quantity),
      unit: line.unit, // unités normalisées : sous-ensemble des unités de saisie
    })),
  }
}

/** Accepte la virgule décimale française (« 0,5 »). */
function parseNumber(text: string): number {
  const normalized = text.trim().replace(',', '.')
  return normalized === '' ? Number.NaN : Number(normalized)
}

export type FormResult = { ok: true; payload: RecipeCreate } | { ok: false; errors: string[] }

/** Valide le formulaire et construit la requête. Les lignes entièrement vides sont ignorées. */
export function formToPayload(state: RecipeFormState): FormResult {
  const errors: string[] = []

  const name = state.name.trim()
  if (!name) errors.push('Le nom est obligatoire.')

  const servings = parseNumber(state.servings)
  if (!Number.isInteger(servings) || servings < 1 || servings > 100) {
    errors.push('Le nombre de portions doit être un entier entre 1 et 100.')
  }

  const lines = state.lines.filter((line) => line.ingredientId || line.quantity.trim())
  const seen = new Set<string>()
  const ingredients: RecipeCreate['ingredients'] = []
  lines.forEach((line, index) => {
    const label = `Ingrédient n° ${index + 1}`
    if (!line.ingredientId) {
      errors.push(`${label} : choisissez un ingrédient.`)
      return
    }
    if (seen.has(line.ingredientId)) {
      errors.push(`${label} : cet ingrédient est déjà dans la recette.`)
    }
    seen.add(line.ingredientId)
    const quantity = parseNumber(line.quantity)
    if (!(quantity > 0)) {
      errors.push(`${label} : la quantité doit être un nombre positif.`)
      return
    }
    ingredients.push({
      ingredient_id: line.ingredientId,
      quantity,
      ...(line.unit ? { unit: line.unit } : {}),
    })
  })

  if (errors.length > 0) return { ok: false, errors }
  return {
    ok: true,
    payload: {
      name,
      description: state.description.trim() || null,
      servings,
      instructions: state.instructions.trim(),
      tags: parseTags(state.tags),
      visibility: state.visibility,
      ingredients,
    },
  }
}
