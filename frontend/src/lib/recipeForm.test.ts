import { describe, expect, it } from 'vitest'

import type { Recipe } from '../api/types'
import { type RecipeFormState, emptyLine, emptyRecipeForm, formToPayload, recipeToForm } from './recipeForm'

function form(overrides: Partial<RecipeFormState>): RecipeFormState {
  return { ...emptyRecipeForm(), name: 'Crêpes', ...overrides }
}

describe('formToPayload', () => {
  it('construit la requête', () => {
    const result = formToPayload(
      form({
        name: '  Crêpes ',
        description: ' ',
        servings: '4',
        tags: 'Dessert, rapide',
        visibility: 'public',
        lines: [
          { ...emptyLine(), ingredientId: 'farine', quantity: '0,25', unit: 'kg' },
          { ...emptyLine(), ingredientId: 'oeufs', quantity: '3', unit: '' },
          emptyLine(), // ligne vide ignorée
        ],
      }),
    )

    expect(result).toEqual({
      ok: true,
      payload: {
        name: 'Crêpes',
        description: null,
        servings: 4,
        instructions: '',
        tags: ['dessert', 'rapide'],
        visibility: 'public',
        ingredients: [
          { ingredient_id: 'farine', quantity: 0.25, unit: 'kg' },
          { ingredient_id: 'oeufs', quantity: 3 }, // pas d'unité : celle de l'ingrédient
        ],
      },
    })
  })

  it('signale toutes les erreurs', () => {
    const result = formToPayload(
      form({
        name: ' ',
        servings: '0',
        lines: [
          { ...emptyLine(), ingredientId: 'farine', quantity: 'beaucoup' },
          { ...emptyLine(), ingredientId: 'farine', quantity: '2' },
          { ...emptyLine(), ingredientId: '', quantity: '1' },
        ],
      }),
    )

    expect(result).toEqual({
      ok: false,
      errors: [
        'Le nom est obligatoire.',
        'Le nombre de portions doit être un entier entre 1 et 100.',
        'Ingrédient n° 1 : la quantité doit être un nombre positif.',
        'Ingrédient n° 2 : cet ingrédient est déjà dans la recette.',
        'Ingrédient n° 3 : choisissez un ingrédient.',
      ],
    })
  })
})

describe('recipeToForm', () => {
  it("reprend une recette existante et redonne la même requête", () => {
    const recipe: Recipe = {
      id: 'r1',
      owner_id: 'u1',
      name: 'Crêpes',
      description: 'Pour 4',
      servings: 4,
      instructions: 'Mélanger.',
      tags: ['dessert'],
      visibility: 'private',
      source_recipe_id: null,
      ingredients: [{ ingredient: { id: 'farine', name: 'Farine', aisle: 'grocery' }, quantity: 250, unit: 'g' }],
      created_at: '2026-11-11T00:00:00Z',
      updated_at: '2026-11-11T00:00:00Z',
    }

    const result = formToPayload(recipeToForm(recipe))

    expect(result).toEqual({
      ok: true,
      payload: {
        name: 'Crêpes',
        description: 'Pour 4',
        servings: 4,
        instructions: 'Mélanger.',
        tags: ['dessert'],
        visibility: 'private',
        ingredients: [{ ingredient_id: 'farine', quantity: 250, unit: 'g' }],
      },
    })
  })
})
