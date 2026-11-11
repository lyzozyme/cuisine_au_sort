import { type FormEvent, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router'

import type { Ingredient, Recipe } from '../api/types'
import { useCreateRecipe, useIngredients, useRecipe, useUpdateRecipe } from '../api/queries'
import { ErrorList, ErrorMessage, Loading } from '../components/Feedback'
import { INPUT_UNIT_LABELS, UNIT_LABELS, VISIBILITY_LABELS, options } from '../lib/labels'
import {
  type IngredientLine,
  type RecipeFormState,
  emptyLine,
  emptyRecipeForm,
  formToPayload,
  recipeToForm,
} from '../lib/recipeForm'

/** Création (/recipes/new) ou modification (/recipes/:id/edit) d'une recette. */
export function RecipeFormPage() {
  const { id } = useParams()
  const recipe = useRecipe(id ?? '')
  // Catalogue complet pour les listes déroulantes (limite de l'API : 200)
  const ingredients = useIngredients({ limit: 200 })

  if (id && recipe.isPending) return <Loading />
  if (id && recipe.error) return <ErrorMessage error={recipe.error} />
  if (ingredients.isPending) return <Loading />
  if (ingredients.error) return <ErrorMessage error={ingredients.error} />

  return (
    <RecipeForm
      key={id ?? 'new'}
      recipe={id ? recipe.data : undefined}
      catalog={ingredients.data ?? []}
    />
  )
}

function RecipeForm({ recipe, catalog }: { recipe?: Recipe; catalog: Ingredient[] }) {
  const navigate = useNavigate()
  const createRecipe = useCreateRecipe()
  const updateRecipe = useUpdateRecipe()
  const mutation = recipe ? updateRecipe : createRecipe
  const [form, setForm] = useState<RecipeFormState>(() =>
    recipe ? recipeToForm(recipe) : emptyRecipeForm(),
  )
  const [errors, setErrors] = useState<string[]>([])

  const set = <K extends keyof RecipeFormState>(field: K, value: RecipeFormState[K]) =>
    setForm((current) => ({ ...current, [field]: value }))

  const setLine = (key: number, changes: Partial<IngredientLine>) =>
    set(
      'lines',
      form.lines.map((line) => (line.key === key ? { ...line, ...changes } : line)),
    )

  const onSubmit = (event: FormEvent) => {
    event.preventDefault()
    const result = formToPayload(form)
    if (!result.ok) {
      setErrors(result.errors)
      return
    }
    setErrors([])
    const onSuccess = (saved: Recipe) => navigate(`/recipes/${saved.id}`)
    if (recipe) updateRecipe.mutate({ id: recipe.id, body: result.payload }, { onSuccess })
    else createRecipe.mutate(result.payload, { onSuccess })
  }

  return (
    <form onSubmit={onSubmit} className="form" noValidate>
      <h1>{recipe ? `Modifier « ${recipe.name} »` : 'Nouvelle recette'}</h1>

      <label>
        Nom
        <input value={form.name} onChange={(e) => set('name', e.target.value)} required />
      </label>
      <label>
        Description
        <textarea
          value={form.description}
          onChange={(e) => set('description', e.target.value)}
          rows={2}
        />
      </label>
      <div className="row">
        <label>
          Portions
          <input
            type="number"
            min={1}
            max={100}
            value={form.servings}
            onChange={(e) => set('servings', e.target.value)}
          />
        </label>
        <label>
          Visibilité
          <select
            value={form.visibility}
            onChange={(e) => set('visibility', e.target.value as RecipeFormState['visibility'])}
          >
            {options(VISIBILITY_LABELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </label>
        <label className="grow">
          Tags (séparés par des virgules)
          <input
            value={form.tags}
            onChange={(e) => set('tags', e.target.value)}
            placeholder="rapide, végétarien"
          />
        </label>
      </div>

      <fieldset>
        <legend>Ingrédients</legend>
        {catalog.length === 0 && (
          <p className="muted">
            Le catalogue est vide : <Link to="/ingredients">ajoutez d'abord des ingrédients</Link>.
          </p>
        )}
        {form.lines.map((line, index) => {
          const selected = catalog.find((i) => i.id === line.ingredientId)
          return (
            <div key={line.key} className="row ingredient-line">
              <select
                aria-label={`Ingrédient n° ${index + 1}`}
                value={line.ingredientId}
                onChange={(e) => setLine(line.key, { ingredientId: e.target.value })}
              >
                <option value="">— Ingrédient —</option>
                {catalog.map((ingredient) => (
                  <option key={ingredient.id} value={ingredient.id}>
                    {ingredient.name}
                  </option>
                ))}
              </select>
              <input
                aria-label={`Quantité n° ${index + 1}`}
                inputMode="decimal"
                placeholder="Quantité"
                value={line.quantity}
                onChange={(e) => setLine(line.key, { quantity: e.target.value })}
              />
              <select
                aria-label={`Unité n° ${index + 1}`}
                value={line.unit}
                onChange={(e) => setLine(line.key, { unit: e.target.value as IngredientLine['unit'] })}
              >
                <option value="">
                  {selected ? `${UNIT_LABELS[selected.default_unit]} (par défaut)` : 'Unité par défaut'}
                </option>
                {options(INPUT_UNIT_LABELS).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
              <button
                type="button"
                className="icon"
                aria-label={`Retirer l'ingrédient n° ${index + 1}`}
                onClick={() =>
                  set(
                    'lines',
                    form.lines.filter((l) => l.key !== line.key),
                  )
                }
              >
                ✕
              </button>
            </div>
          )
        })}
        <button type="button" onClick={() => set('lines', [...form.lines, emptyLine()])}>
          + Ajouter un ingrédient
        </button>
      </fieldset>

      <label>
        Préparation
        <textarea
          value={form.instructions}
          onChange={(e) => set('instructions', e.target.value)}
          rows={8}
        />
      </label>

      <ErrorList errors={errors} />
      <ErrorMessage error={mutation.error} />

      <div className="actions">
        <button type="submit" className="primary" disabled={mutation.isPending}>
          {recipe ? 'Enregistrer' : 'Créer la recette'}
        </button>
        <Link to={recipe ? `/recipes/${recipe.id}` : '/recipes'} className="button">
          Annuler
        </Link>
      </div>
    </form>
  )
}
