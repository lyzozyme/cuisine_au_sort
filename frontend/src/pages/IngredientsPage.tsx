import { type FormEvent, useState } from 'react'

import type { Aisle, Ingredient, Unit } from '../api/types'
import {
  useCreateIngredient,
  useDeleteIngredient,
  useIngredients,
  useUpdateIngredient,
} from '../api/queries'
import { ErrorMessage, Loading } from '../components/Feedback'
import { AISLE_LABELS, UNIT_LABELS, options } from '../lib/labels'
import { useDebouncedValue } from '../lib/useDebouncedValue'

type Draft = { name: string; default_unit: Unit; aisle: Aisle }

const EMPTY_DRAFT: Draft = { name: '', default_unit: 'g', aisle: 'other' }

export function IngredientsPage() {
  const [search, setSearch] = useState('')
  const debouncedSearch = useDebouncedValue(search.trim())
  const ingredients = useIngredients({ q: debouncedSearch || undefined, limit: 200 })
  const deleteIngredient = useDeleteIngredient()
  const [editingId, setEditingId] = useState<string | null>(null)

  const onDelete = (ingredient: Ingredient) => {
    if (!window.confirm(`Supprimer l'ingrédient « ${ingredient.name} » ?`)) return
    deleteIngredient.mutate(ingredient.id)
  }

  return (
    <section>
      <h1>Ingrédients</h1>
      <p className="muted">Catalogue partagé, utilisé par toutes les recettes.</p>

      <CreateIngredientForm />

      <div className="filters">
        <input
          type="search"
          placeholder="Rechercher"
          aria-label="Rechercher un ingrédient"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
        />
      </div>

      <ErrorMessage error={ingredients.error ?? deleteIngredient.error} />
      {ingredients.isPending ? (
        <Loading />
      ) : ingredients.data?.length === 0 ? (
        <p className="muted">Aucun ingrédient.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Nom</th>
              <th>Unité par défaut</th>
              <th>Rayon</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {ingredients.data?.map((ingredient) =>
              editingId === ingredient.id ? (
                <EditIngredientRow
                  key={ingredient.id}
                  ingredient={ingredient}
                  onDone={() => setEditingId(null)}
                />
              ) : (
                <tr key={ingredient.id}>
                  <td>{ingredient.name}</td>
                  <td>{UNIT_LABELS[ingredient.default_unit]}</td>
                  <td>{AISLE_LABELS[ingredient.aisle]}</td>
                  <td className="actions">
                    <button type="button" onClick={() => setEditingId(ingredient.id)}>
                      Modifier
                    </button>
                    <button type="button" className="danger" onClick={() => onDelete(ingredient)}>
                      Supprimer
                    </button>
                  </td>
                </tr>
              ),
            )}
          </tbody>
        </table>
      )}
    </section>
  )
}

function DraftFields({ draft, onChange }: { draft: Draft; onChange: (draft: Draft) => void }) {
  return (
    <>
      <input
        aria-label="Nom de l'ingrédient"
        placeholder="Nom"
        value={draft.name}
        onChange={(e) => onChange({ ...draft, name: e.target.value })}
        required
      />
      <select
        aria-label="Unité par défaut"
        value={draft.default_unit}
        onChange={(e) => onChange({ ...draft, default_unit: e.target.value as Unit })}
      >
        {options(UNIT_LABELS).map(([value, label]) => (
          <option key={value} value={value}>
            {label}
          </option>
        ))}
      </select>
      <select
        aria-label="Rayon"
        value={draft.aisle}
        onChange={(e) => onChange({ ...draft, aisle: e.target.value as Aisle })}
      >
        {options(AISLE_LABELS).map(([value, label]) => (
          <option key={value} value={value}>
            {label}
          </option>
        ))}
      </select>
    </>
  )
}

function CreateIngredientForm() {
  const createIngredient = useCreateIngredient()
  const [draft, setDraft] = useState<Draft>(EMPTY_DRAFT)

  const onSubmit = (event: FormEvent) => {
    event.preventDefault()
    // On garde unité et rayon : pratique pour saisir plusieurs ingrédients d'un même rayon
    createIngredient.mutate(draft, { onSuccess: () => setDraft((current) => ({ ...current, name: '' })) })
  }

  return (
    <form onSubmit={onSubmit} className="inline-form">
      <DraftFields draft={draft} onChange={setDraft} />
      <button type="submit" className="primary" disabled={createIngredient.isPending}>
        Ajouter
      </button>
      <ErrorMessage error={createIngredient.error} />
    </form>
  )
}

function EditIngredientRow({ ingredient, onDone }: { ingredient: Ingredient; onDone: () => void }) {
  const updateIngredient = useUpdateIngredient()
  const [draft, setDraft] = useState<Draft>({
    name: ingredient.name,
    default_unit: ingredient.default_unit,
    aisle: ingredient.aisle,
  })

  const onSave = () => updateIngredient.mutate({ id: ingredient.id, body: draft }, { onSuccess: onDone })

  return (
    <tr>
      <td colSpan={3}>
        <div className="inline-form">
          <DraftFields draft={draft} onChange={setDraft} />
        </div>
        <ErrorMessage error={updateIngredient.error} />
      </td>
      <td className="actions">
        <button type="button" className="primary" onClick={onSave} disabled={updateIngredient.isPending}>
          Enregistrer
        </button>
        <button type="button" onClick={onDone}>
          Annuler
        </button>
      </td>
    </tr>
  )
}
