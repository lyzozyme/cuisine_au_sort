import { Link, useNavigate, useParams } from 'react-router'

import { useDeleteRecipe, useMe, useRecipe } from '../api/queries'
import { ErrorMessage, Loading } from '../components/Feedback'
import { formatQuantity } from '../lib/format'
import { AISLE_LABELS, VISIBILITY_LABELS } from '../lib/labels'

export function RecipeDetailPage() {
  const { id = '' } = useParams()
  const navigate = useNavigate()
  const recipe = useRecipe(id)
  const me = useMe()
  const deleteRecipe = useDeleteRecipe()

  if (recipe.isPending) return <Loading />
  if (recipe.error) return <ErrorMessage error={recipe.error} />

  const { data } = recipe
  const isOwner = me.data?.id === data.owner_id

  const onDelete = () => {
    if (!window.confirm(`Supprimer la recette « ${data.name} » ?`)) return
    deleteRecipe.mutate(data.id, { onSuccess: () => navigate('/recipes') })
  }

  return (
    <article>
      <div className="page-title">
        <h1>{data.name}</h1>
        {isOwner && (
          <div className="actions">
            <Link to={`/recipes/${data.id}/edit`} className="button">
              Modifier
            </Link>
            <button type="button" className="danger" onClick={onDelete} disabled={deleteRecipe.isPending}>
              Supprimer
            </button>
          </div>
        )}
      </div>
      <ErrorMessage error={deleteRecipe.error} />

      <p className="muted">
        {data.servings} personne(s) · {VISIBILITY_LABELS[data.visibility]}
      </p>
      {data.tags.length > 0 && (
        <p className="tags">
          {data.tags.map((tag) => (
            <span key={tag} className="tag">
              {tag}
            </span>
          ))}
        </p>
      )}
      {data.description && <p>{data.description}</p>}

      <h2>Ingrédients</h2>
      {data.ingredients.length === 0 ? (
        <p className="muted">Aucun ingrédient.</p>
      ) : (
        <ul>
          {data.ingredients.map((line) => (
            <li key={line.ingredient.id}>
              {formatQuantity(line.quantity, line.unit)} · {line.ingredient.name}{' '}
              <span className="muted">({AISLE_LABELS[line.ingredient.aisle]})</span>
            </li>
          ))}
        </ul>
      )}

      <h2>Préparation</h2>
      {data.instructions ? (
        <p className="instructions">{data.instructions}</p>
      ) : (
        <p className="muted">Pas d'instructions.</p>
      )}

      <p>
        <Link to="/recipes">← Toutes les recettes</Link>
      </p>
    </article>
  )
}
