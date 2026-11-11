import type { components, paths } from './schema'

type Schemas = components['schemas']

export type Aisle = Schemas['Aisle']
export type InputUnit = Schemas['InputUnit']
export type Meal = Schemas['Meal']
export type Unit = Schemas['Unit']
export type Visibility = Schemas['Visibility']

export type Ingredient = Schemas['IngredientRead']
export type IngredientCreate = Schemas['IngredientCreate']
export type IngredientUpdate = Schemas['IngredientUpdate']

export type Recipe = Schemas['RecipeRead']
export type RecipeCreate = Schemas['RecipeCreate']
export type RecipeUpdate = Schemas['RecipeUpdate']

export type DrawRequest = Schemas['DrawRequest']
export type Plan = Schemas['PlanRead']
export type PlanEntry = Schemas['PlanEntryRead']
export type ShoppingList = Schemas['ShoppingListRead']

export type User = Schemas['UserRead']

export type IngredientListParams = NonNullable<paths['/ingredients']['get']['parameters']['query']>
export type RecipeListParams = NonNullable<paths['/recipes']['get']['parameters']['query']>
