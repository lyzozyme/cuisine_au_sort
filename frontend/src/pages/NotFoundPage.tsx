import { Link } from 'react-router'

export function NotFoundPage() {
  return (
    <section>
      <h1>Page introuvable</h1>
      <p>
        <Link to="/recipes">Retour aux recettes</Link>
      </p>
    </section>
  )
}
