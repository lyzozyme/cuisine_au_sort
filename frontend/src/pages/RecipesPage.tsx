import { useState } from 'react'
import { Link } from 'react-router'

import { useRecipes } from '../api/queries'
import { ErrorMessage, Loading } from '../components/Feedback'
import { VISIBILITY_LABELS } from '../lib/labels'

export function RecipesPage() {
  const [search, setSearch] = useState('')
  const [tag, setTag] = useState('')
  const [mine, setMine] = useState(false)
  const recipes = useRecipes({
    q: search.trim() || undefined,
    tag: tag.trim() || undefined,
    mine: mine || undefined,
    limit: 200,
  })

  return (
    <section>
      <div className="page-title">
        <h1>Recettes</h1>
        <Link to="/recipes/new" className="button primary">
          Nouvelle recette
        </Link>
      </div>

      <div className="filters">
        <input
          type="search"
          placeholder="Rechercher par nom"
          aria-label="Rechercher par nom"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
        />
        <input
          type="search"
          placeholder="Filtrer par tag"
          aria-label="Filtrer par tag"
          value={tag}
          onChange={(event) => setTag(event.target.value)}
        />
        <label className="checkbox">
          <input type="checkbox" checked={mine} onChange={(event) => setMine(event.target.checked)} />
          Mes recettes uniquement
        </label>
      </div>

      <ErrorMessage error={recipes.error} />
      {recipes.isPending ? (
        <Loading />
      ) : recipes.data?.length === 0 ? (
        <p className="muted">Aucune recette.</p>
      ) : (
        <ul className="cards">
          {recipes.data?.map((recipe) => (
            <li key={recipe.id} className="card">
              <Link to={`/recipes/${recipe.id}`} className="card-title">
                {recipe.name}
              </Link>
              <p className="muted">
                {recipe.servings} pers. · {recipe.ingredients.length} ingrédient(s)
                {recipe.visibility !== 'private' && ` · ${VISIBILITY_LABELS[recipe.visibility]}`}
              </p>
              {recipe.tags.length > 0 && (
                <p className="tags">
                  {recipe.tags.map((t) => (
                    <span key={t} className="tag">
                      {t}
                    </span>
                  ))}
                </p>
              )}
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
