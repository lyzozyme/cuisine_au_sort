import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router'

import { useDeletePlan, usePlan, useShoppingList } from '../api/queries'
import { ErrorMessage, Loading } from '../components/Feedback'
import { formatDayDate, formatQuantity, formatWeek } from '../lib/format'
import { AISLE_LABELS, MEAL_LABELS } from '../lib/labels'

export function PlanDetailPage() {
  const { id = '' } = useParams()
  const navigate = useNavigate()
  const plan = usePlan(id)
  const deletePlan = useDeletePlan()

  if (plan.isPending) return <Loading />
  if (plan.error) return <ErrorMessage error={plan.error} />

  const { data } = plan
  const onDelete = () => {
    if (!window.confirm('Supprimer ce planning ?')) return
    deletePlan.mutate(data.id, { onSuccess: () => navigate('/plans') })
  }

  return (
    <article>
      <div className="page-title">
        <h1>{formatWeek(data.week_start)}</h1>
        <div className="actions">
          <Link to="/draw" className="button">
            Nouveau tirage
          </Link>
          <button type="button" className="danger" onClick={onDelete} disabled={deletePlan.isPending}>
            Supprimer
          </button>
        </div>
      </div>
      <ErrorMessage error={deletePlan.error} />

      <table>
        <thead>
          <tr>
            <th>Jour</th>
            <th>Repas</th>
            <th>Recette</th>
          </tr>
        </thead>
        <tbody>
          {data.entries.map((entry) => (
            <tr key={entry.id}>
              <td className="capitalize">{formatDayDate(entry.date)}</td>
              <td>{MEAL_LABELS[entry.meal]}</td>
              <td>
                <Link to={`/recipes/${entry.recipe.id}`}>{entry.recipe.name}</Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <ShoppingList planId={data.id} />
    </article>
  )
}

function ShoppingList({ planId }: { planId: string }) {
  const [servingsText, setServingsText] = useState('')
  const servings = Number(servingsText)
  const validServings = Number.isInteger(servings) && servings >= 1 && servings <= 100
  const list = useShoppingList(planId, validServings ? servings : undefined)
  // Articles cochés (déjà dans le panier) : état local, non enregistré
  const [checked, setChecked] = useState<Set<string>>(new Set())

  const toggle = (key: string) =>
    setChecked((current) => {
      const next = new Set(current)
      if (next.has(key)) next.delete(key)
      else next.add(key)
      return next
    })

  return (
    <section>
      <h2>Liste de courses</h2>
      <label className="inline">
        Pour
        <input
          type="number"
          min={1}
          max={100}
          placeholder="—"
          value={servingsText}
          onChange={(e) => setServingsText(e.target.value)}
          aria-label="Nombre de personnes"
        />
        personne(s) <span className="muted">(vide : quantités des recettes)</span>
      </label>

      <ErrorMessage error={list.error} />
      {list.isPending ? (
        <Loading />
      ) : list.data?.aisles.length === 0 ? (
        <p className="muted">Aucun ingrédient dans les recettes de ce planning.</p>
      ) : (
        list.data?.aisles.map((aisle) => (
          <div key={aisle.aisle} className="aisle">
            <h3>{AISLE_LABELS[aisle.aisle]}</h3>
            <ul className="checklist">
              {aisle.items.map((item) => {
                const key = `${item.ingredient.id}:${item.unit}`
                return (
                  <li key={key} className={checked.has(key) ? 'done' : undefined}>
                    <label className="checkbox">
                      <input type="checkbox" checked={checked.has(key)} onChange={() => toggle(key)} />
                      {item.ingredient.name} — {formatQuantity(item.quantity, item.unit)}
                    </label>
                  </li>
                )
              })}
            </ul>
          </div>
        ))
      )}
    </section>
  )
}
