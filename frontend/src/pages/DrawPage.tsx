import { type FormEvent, useState } from 'react'
import { useNavigate } from 'react-router'

import type { Meal } from '../api/types'
import { useDrawPlan } from '../api/queries'
import { ErrorList, ErrorMessage } from '../components/Feedback'
import { isMonday, parseTags, upcomingMonday } from '../lib/format'
import { MEAL_LABELS, options } from '../lib/labels'

const DAYS_PER_WEEK = 7

export function DrawPage() {
  const navigate = useNavigate()
  const drawPlan = useDrawPlan()
  const [weekStart, setWeekStart] = useState(upcomingMonday)
  const [mealCount, setMealCount] = useState('7')
  const [meals, setMeals] = useState<Meal[]>(['dinner'])
  const [excludeTags, setExcludeTags] = useState('')
  const [mineOnly, setMineOnly] = useState(false)
  const [errors, setErrors] = useState<string[]>([])

  const maxMeals = DAYS_PER_WEEK * meals.length

  const toggleMeal = (meal: Meal, checked: boolean) =>
    setMeals((current) => (checked ? [...current, meal] : current.filter((m) => m !== meal)))

  const onSubmit = (event: FormEvent) => {
    event.preventDefault()
    const count = Number(mealCount)
    const problems: string[] = []
    if (!isMonday(weekStart)) problems.push('La semaine doit commencer un lundi.')
    if (meals.length === 0) problems.push('Choisissez au moins un repas par jour.')
    else if (!Number.isInteger(count) || count < 1 || count > maxMeals) {
      problems.push(`Le nombre de repas doit être compris entre 1 et ${maxMeals}.`)
    }
    setErrors(problems)
    if (problems.length > 0) return

    drawPlan.mutate(
      {
        week_start: weekStart,
        meal_count: count,
        meals,
        exclude_tags: parseTags(excludeTags),
        mine_only: mineOnly,
      },
      { onSuccess: (plan) => navigate(`/plans/${plan.id}`) },
    )
  }

  return (
    <form onSubmit={onSubmit} className="form" noValidate>
      <h1>Tirage au sort</h1>
      <p className="muted">
        Les recettes sont tirées sans doublon et placées dans l'ordre de la semaine, à partir du
        lundi.
      </p>

      <div className="row">
        <label>
          Semaine du (lundi)
          <input type="date" value={weekStart} onChange={(e) => setWeekStart(e.target.value)} />
        </label>
        <label>
          Nombre de repas
          <input
            type="number"
            min={1}
            max={maxMeals || 1}
            value={mealCount}
            onChange={(e) => setMealCount(e.target.value)}
          />
        </label>
      </div>

      <fieldset>
        <legend>Repas à planifier chaque jour</legend>
        {options(MEAL_LABELS).map(([meal, label]) => (
          <label key={meal} className="checkbox">
            <input
              type="checkbox"
              checked={meals.includes(meal)}
              onChange={(e) => toggleMeal(meal, e.target.checked)}
            />
            {label}
          </label>
        ))}
      </fieldset>

      <label>
        Tags à exclure (séparés par des virgules)
        <input
          value={excludeTags}
          onChange={(e) => setExcludeTags(e.target.value)}
          placeholder="long, viande"
        />
      </label>
      <label className="checkbox">
        <input type="checkbox" checked={mineOnly} onChange={(e) => setMineOnly(e.target.checked)} />
        Uniquement mes recettes (sinon : aussi les recettes publiques des autres)
      </label>

      <ErrorList errors={errors} />
      <ErrorMessage error={drawPlan.error} />

      <div className="actions">
        <button type="submit" className="primary" disabled={drawPlan.isPending}>
          🎲 Tirer au sort
        </button>
      </div>
    </form>
  )
}
