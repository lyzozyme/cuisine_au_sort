import createClient from 'openapi-fetch'

import type { paths } from './schema'

/**
 * Client HTTP typé, généré depuis l'OpenAPI du backend (`npm run api:generate`).
 * Par défaut, les requêtes passent par /api (proxy Vite en développement).
 */
export const api = createClient<paths>({
  baseUrl: import.meta.env.VITE_API_BASE_URL ?? `${window.location.origin}/api`,
  // Résolu à chaque appel (et non mémorisé à la création) : permet de le simuler dans les tests
  fetch: (request) => globalThis.fetch(request),
})

export class ApiError extends Error {
  readonly status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

type ValidationIssue = { loc: (string | number)[]; msg: string }

/** Message lisible à partir d'une réponse d'erreur de l'API (erreur métier ou de validation). */
export function errorMessage(body: unknown, status: number): string {
  const detail = (body as { detail?: unknown } | undefined)?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail) && detail.length > 0) {
    return (detail as ValidationIssue[])
      .map(({ loc, msg }) => {
        const field = loc.filter((part) => part !== 'body' && part !== 'query').join('.')
        return field ? `${field} : ${msg}` : msg
      })
      .join('\n')
  }
  return `Erreur inattendue (HTTP ${status})`
}

type FetchResult<T> = { data?: T; error?: unknown; response: Response }

/** Renvoie les données d'une requête openapi-fetch, ou lève une ApiError. */
export async function unwrap<T>(request: Promise<FetchResult<T>>): Promise<T> {
  let result: FetchResult<T>
  try {
    result = await request
  } catch {
    throw new ApiError(0, "Impossible de joindre l'API : le backend est-il lancé ?")
  }
  const { data, error, response } = result
  if (!response.ok) throw new ApiError(response.status, errorMessage(error, response.status))
  return data as T
}
