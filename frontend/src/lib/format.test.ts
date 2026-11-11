import { describe, expect, it } from 'vitest'

import { formatDayDate, formatQuantity, formatWeek, isMonday, parseTags, upcomingMonday } from './format'

describe('formatQuantity', () => {
  it.each([
    [250, 'g', '250 g'],
    [1500, 'g', '1,5 kg'],
    [1000, 'ml', '1 l'],
    [275, 'ml', '275 ml'],
    [1, 'piece', '1 pièce'],
    [2.75, 'piece', '2,75 pièces'],
    [0.667, 'piece', '0,667 pièce'],
    [2, 'tbsp', '2 c. à soupe'],
    [1, 'tsp', '1 c. à café'],
    [2, 'pinch', '2 pincées'],
  ] as const)('%s %s -> %s', (quantity, unit, expected) => {
    expect(formatQuantity(quantity, unit)).toBe(expected)
  })
})

describe('dates', () => {
  it('formate une date ISO sans décalage de fuseau', () => {
    expect(formatDayDate('2026-11-16')).toBe('lundi 16 novembre')
    expect(formatWeek('2026-11-16')).toBe('Semaine du 16 novembre 2026')
  })

  it.each([
    [new Date(2026, 10, 16), '2026-11-16'], // lundi : la semaine en cours
    [new Date(2026, 10, 11), '2026-11-16'], // mercredi
    [new Date(2026, 10, 15), '2026-11-16'], // dimanche
    [new Date(2026, 11, 29), '2027-01-04'], // changement d'année
  ])('upcomingMonday(%s) = %s', (today, expected) => {
    expect(upcomingMonday(today)).toBe(expected)
  })

  it('reconnaît un lundi', () => {
    expect(isMonday('2026-11-16')).toBe(true)
    expect(isMonday('2026-11-17')).toBe(false)
  })
})

describe('parseTags', () => {
  it('nettoie, met en minuscules et dédoublonne', () => {
    expect(parseTags(' Dessert, rapide,, dessert ,')).toEqual(['dessert', 'rapide'])
    expect(parseTags('')).toEqual([])
  })
})
