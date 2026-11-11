import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render } from '@testing-library/react'
import type { ReactElement } from 'react'
import { MemoryRouter, Route, Routes } from 'react-router'
import { vi } from 'vitest'

/** Réponse simulée : `[méthode, chemin]` -> corps JSON (ou fonction recevant le corps envoyé). */
export type MockRoutes = Record<string, unknown | ((body: unknown) => unknown)>

/**
 * Remplace `fetch` par un faux backend. Clé : « GET /recipes » (chemin sans /api ni paramètres).
 * Renvoie la liste des requêtes reçues, pour vérifier ce que l'interface a envoyé.
 */
export function mockApi(routes: MockRoutes) {
  const calls: { method: string; path: string; body: unknown }[] = []
  vi.stubGlobal(
    'fetch',
    vi.fn(async (request: Request) => {
      const url = new URL(request.url)
      const path = url.pathname.replace(/^\/api/, '')
      const text = await request.text()
      const body = text ? JSON.parse(text) : undefined
      calls.push({ method: request.method, path, body })
      const key = `${request.method} ${path}`
      if (!(key in routes)) return Response.json({ detail: `Non simulé : ${key}` }, { status: 404 })
      const route = routes[key]
      const data = typeof route === 'function' ? route(body) : route
      return Response.json(data, { status: request.method === 'POST' ? 201 : 200 })
    }),
  )
  return calls
}

/** Rend une page dans ses providers (React Query, routeur), à l'URL donnée. */
export function renderPage(page: ReactElement, { path, url }: { path: string; url: string }) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[url]}>
        <Routes>
          <Route path={path} element={page} />
          <Route path="*" element={<p>Page : {'redirigé'}</p>} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}
