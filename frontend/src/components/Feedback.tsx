import { ApiError } from '../api/client'

export function Loading() {
  return <p className="muted">Chargement…</p>
}

/** Affiche une erreur (API ou autre) ; rien si `error` est vide. */
export function ErrorMessage({ error }: { error: unknown }) {
  if (!error) return null
  const message =
    error instanceof ApiError || error instanceof Error ? error.message : String(error)
  return (
    <p className="error" role="alert">
      {message}
    </p>
  )
}

/** Liste d'erreurs de validation côté client. */
export function ErrorList({ errors }: { errors: string[] }) {
  if (errors.length === 0) return null
  return (
    <ul className="error" role="alert">
      {errors.map((error) => (
        <li key={error}>{error}</li>
      ))}
    </ul>
  )
}
