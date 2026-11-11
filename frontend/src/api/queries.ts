/**
 * Hooks TanStack Query : lecture (cache) et écriture (avec invalidation du cache concerné).
 */
import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { api, unwrap } from './client'
import type {
  DrawRequest,
  IngredientCreate,
  IngredientListParams,
  IngredientUpdate,
  RecipeCreate,
  RecipeListParams,
  RecipeUpdate,
} from './types'

export const queryKeys = {
  me: ['me'] as const,
  ingredients: ['ingredients'] as const,
  recipes: ['recipes'] as const,
  plans: ['plans'] as const,
}

// --- Utilisateur ---------------------------------------------------------------------------------

export function useMe() {
  return useQuery({
    queryKey: queryKeys.me,
    queryFn: () => unwrap(api.GET('/users/me')),
    staleTime: Infinity,
  })
}

// --- Ingrédients ---------------------------------------------------------------------------------

export function useIngredients(query: IngredientListParams = {}) {
  return useQuery({
    queryKey: [...queryKeys.ingredients, query],
    queryFn: () => unwrap(api.GET('/ingredients', { params: { query } })),
    placeholderData: keepPreviousData,
  })
}

export function useCreateIngredient() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (body: IngredientCreate) => unwrap(api.POST('/ingredients', { body })),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.ingredients }),
  })
}

export function useUpdateIngredient() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: IngredientUpdate }) =>
      unwrap(api.PATCH('/ingredients/{ingredient_id}', { params: { path: { ingredient_id: id } }, body })),
    onSuccess: () =>
      // Le nom et le rayon apparaissent aussi dans les recettes et les listes de courses
      Promise.all([
        queryClient.invalidateQueries({ queryKey: queryKeys.ingredients }),
        queryClient.invalidateQueries({ queryKey: queryKeys.recipes }),
        queryClient.invalidateQueries({ queryKey: queryKeys.plans }),
      ]),
  })
}

export function useDeleteIngredient() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) =>
      unwrap(api.DELETE('/ingredients/{ingredient_id}', { params: { path: { ingredient_id: id } } })),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.ingredients }),
  })
}

// --- Recettes ------------------------------------------------------------------------------------

export function useRecipes(query: RecipeListParams = {}) {
  return useQuery({
    queryKey: [...queryKeys.recipes, 'list', query],
    queryFn: () => unwrap(api.GET('/recipes', { params: { query } })),
    placeholderData: keepPreviousData,
  })
}

export function useRecipe(id: string) {
  return useQuery({
    queryKey: [...queryKeys.recipes, 'detail', id],
    queryFn: () => unwrap(api.GET('/recipes/{recipe_id}', { params: { path: { recipe_id: id } } })),
    enabled: id !== '',
  })
}

export function useCreateRecipe() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (body: RecipeCreate) => unwrap(api.POST('/recipes', { body })),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.recipes }),
  })
}

export function useUpdateRecipe() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: RecipeUpdate }) =>
      unwrap(api.PATCH('/recipes/{recipe_id}', { params: { path: { recipe_id: id } }, body })),
    onSuccess: () =>
      Promise.all([
        queryClient.invalidateQueries({ queryKey: queryKeys.recipes }),
        queryClient.invalidateQueries({ queryKey: queryKeys.plans }),
      ]),
  })
}

export function useDeleteRecipe() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) =>
      unwrap(api.DELETE('/recipes/{recipe_id}', { params: { path: { recipe_id: id } } })),
    onSuccess: () =>
      Promise.all([
        queryClient.invalidateQueries({ queryKey: queryKeys.recipes }),
        // Les ingrédients de la recette peuvent maintenant être supprimés
        queryClient.invalidateQueries({ queryKey: queryKeys.ingredients }),
      ]),
  })
}

// --- Plannings -----------------------------------------------------------------------------------

export function usePlans() {
  return useQuery({
    queryKey: [...queryKeys.plans, 'list'],
    queryFn: () => unwrap(api.GET('/plans')),
  })
}

export function usePlan(id: string) {
  return useQuery({
    queryKey: [...queryKeys.plans, 'detail', id],
    queryFn: () => unwrap(api.GET('/plans/{plan_id}', { params: { path: { plan_id: id } } })),
  })
}

export function useShoppingList(id: string, servings?: number) {
  return useQuery({
    queryKey: [...queryKeys.plans, 'shopping-list', id, servings ?? null],
    queryFn: () =>
      unwrap(
        api.GET('/plans/{plan_id}/shopping-list', {
          params: { path: { plan_id: id }, query: { servings } },
        }),
      ),
    placeholderData: keepPreviousData,
  })
}

export function useDrawPlan() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (body: DrawRequest) => unwrap(api.POST('/plans/draw', { body })),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.plans }),
  })
}

export function useDeletePlan() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) =>
      unwrap(api.DELETE('/plans/{plan_id}', { params: { path: { plan_id: id } } })),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.plans }),
  })
}
