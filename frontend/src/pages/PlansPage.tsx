import { Link } from 'react-router'

import type { Plan } from '../api/types'
import { useDeletePlan, usePlans } from '../api/queries'
import { ErrorMessage, Loading } from '../components/Feedback'
import { formatWeek } from '../lib/format'

export function PlansPage() {
  const plans = usePlans()
  const deletePlan = useDeletePlan()

  const onDelete = (plan: Plan) => {
    if (!window.confirm(`Supprimer le planning « ${formatWeek(plan.week_start)} » ?`)) return
    deletePlan.mutate(plan.id)
  }

  return (
    <section>
      <div className="page-title">
        <h1>Plannings</h1>
        <Link to="/draw" className="button primary">
          Nouveau tirage
        </Link>
      </div>

      <ErrorMessage error={plans.error ?? deletePlan.error} />
      {plans.isPending ? (
        <Loading />
      ) : plans.data?.length === 0 ? (
        <p className="muted">
          Aucun planning. <Link to="/draw">Lancez un tirage au sort</Link>.
        </p>
      ) : (
        <ul className="cards">
          {plans.data?.map((plan) => (
            <li key={plan.id} className="card">
              <Link to={`/plans/${plan.id}`} className="card-title">
                {formatWeek(plan.week_start)}
              </Link>
              <p className="muted">{plan.entries.length} repas</p>
              <button type="button" className="danger" onClick={() => onDelete(plan)}>
                Supprimer
              </button>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
