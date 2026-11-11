import { describe, expect, it, vi } from 'vitest'

import { ApiError, api, errorMessage, unwrap } from './client'

describe('errorMessage', () => {
  it('reprend une erreur métier', () => {
    expect(errorMessage({ detail: 'Recette introuvable' }, 404)).toBe('Recette introuvable')
  })

  it('liste les erreurs de validation avec le champ concerné', () => {
    const body = {
      detail: [
        { loc: ['body', 'ingredients', 0, 'quantity'], msg: 'Input should be greater than 0' },
        { loc: ['body'], msg: 'Invalid JSON' },
      ],
    }
    expect(errorMessage(body, 422)).toBe(
      'ingredients.0.quantity : Input should be greater than 0\nInvalid JSON',
    )
  })

  it('a un message par défaut', () => {
    expect(errorMessage(undefined, 418)).toBe('Erreur inattendue (HTTP 418)')
    expect(errorMessage('', 500)).toMatch(/backend est-il lancé/)
  })
})

describe('unwrap', () => {
  it('renvoie les données ou lève une ApiError', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => Response.json({ detail: 'Planning introuvable' }, { status: 404 })),
    )

    const error = await unwrap(api.GET('/plans')).catch((e: unknown) => e)

    expect(error).toBeInstanceOf(ApiError)
    expect(error).toMatchObject({ status: 404, message: 'Planning introuvable' })
  })

  it("signale un backend injoignable", async () => {
    vi.stubGlobal('fetch', vi.fn(async () => Promise.reject(new TypeError('Failed to fetch'))))

    await expect(unwrap(api.GET('/plans'))).rejects.toMatchObject({ status: 0 })
  })
})
