import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'

import type { Ingredient, Recipe } from '../api/types'
import { mockApi, renderPage } from '../test/utils'
import { RecipeFormPage } from './RecipeFormPage'
import { RecipesPage } from './RecipesPage'

const flour: Ingredient = {
  id: 'farine',
  name: 'Farine',
  default_unit: 'g',
  aisle: 'grocery',
  created_at: '2026-11-11T00:00:00Z',
  updated_at: '2026-11-11T00:00:00Z',
}

const crepes: Recipe = {
  id: 'r1',
  owner_id: 'u1',
  name: 'Crêpes',
  description: null,
  servings: 4,
  instructions: '',
  tags: ['dessert'],
  visibility: 'public',
  source_recipe_id: null,
  ingredients: [],
  created_at: '2026-11-11T00:00:00Z',
  updated_at: '2026-11-11T00:00:00Z',
}

describe('RecipesPage', () => {
  it('affiche les recettes renvoyées par l’API', async () => {
    mockApi({ 'GET /recipes': [crepes] })

    renderPage(<RecipesPage />, { path: '/recipes', url: '/recipes' })

    expect(await screen.findByRole('link', { name: 'Crêpes' })).toHaveAttribute('href', '/recipes/r1')
    expect(screen.getByText('dessert')).toBeInTheDocument()
    expect(screen.getByText(/Publique/)).toBeInTheDocument()
  })

  it('affiche l’erreur renvoyée par l’API', async () => {
    mockApi({}) // aucune route simulée : 404 avec un message
    renderPage(<RecipesPage />, { path: '/recipes', url: '/recipes' })

    expect(await screen.findByRole('alert')).toHaveTextContent('Non simulé : GET /recipes')
  })
})

describe('RecipeFormPage', () => {
  it('crée une recette avec ses ingrédients', async () => {
    const user = userEvent.setup()
    const calls = mockApi({
      'GET /ingredients': [flour],
      'POST /recipes': (body: unknown) => ({ ...crepes, ...(body as object), id: 'created' }),
    })
    renderPage(<RecipeFormPage />, { path: '/recipes/new', url: '/recipes/new' })

    await user.type(await screen.findByLabelText('Nom'), 'Crêpes')
    await user.type(screen.getByLabelText(/Tags/), 'Dessert')
    await user.selectOptions(screen.getByLabelText('Ingrédient n° 1'), 'farine')
    await user.type(screen.getByLabelText('Quantité n° 1'), '0,25')
    await user.selectOptions(screen.getByLabelText('Unité n° 1'), 'kg')
    await user.click(screen.getByRole('button', { name: 'Créer la recette' }))

    await screen.findByText('Page : redirigé') // redirection vers /recipes/created
    expect(calls.find((c) => c.method === 'POST')?.body).toEqual({
      name: 'Crêpes',
      description: null,
      servings: 2,
      instructions: '',
      tags: ['dessert'],
      visibility: 'private',
      ingredients: [{ ingredient_id: 'farine', quantity: 0.25, unit: 'kg' }],
    })
  })

  it('n’envoie rien si le formulaire est invalide', async () => {
    const user = userEvent.setup()
    const calls = mockApi({ 'GET /ingredients': [flour] })
    renderPage(<RecipeFormPage />, { path: '/recipes/new', url: '/recipes/new' })

    await user.click(await screen.findByRole('button', { name: 'Créer la recette' }))

    expect(await screen.findByText('Le nom est obligatoire.')).toBeInTheDocument()
    await waitFor(() => expect(calls.filter((c) => c.method === 'POST')).toEqual([]))
  })
})
