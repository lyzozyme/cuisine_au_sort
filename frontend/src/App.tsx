import { Navigate, Route, Routes } from 'react-router'

import { Layout } from './components/Layout'
import { DrawPage } from './pages/DrawPage'
import { IngredientsPage } from './pages/IngredientsPage'
import { NotFoundPage } from './pages/NotFoundPage'
import { PlanDetailPage } from './pages/PlanDetailPage'
import { PlansPage } from './pages/PlansPage'
import { RecipeDetailPage } from './pages/RecipeDetailPage'
import { RecipeFormPage } from './pages/RecipeFormPage'
import { RecipesPage } from './pages/RecipesPage'

export function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Navigate to="/recipes" replace />} />
        <Route path="recipes" element={<RecipesPage />} />
        <Route path="recipes/new" element={<RecipeFormPage />} />
        <Route path="recipes/:id" element={<RecipeDetailPage />} />
        <Route path="recipes/:id/edit" element={<RecipeFormPage />} />
        <Route path="ingredients" element={<IngredientsPage />} />
        <Route path="draw" element={<DrawPage />} />
        <Route path="plans" element={<PlansPage />} />
        <Route path="plans/:id" element={<PlanDetailPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  )
}
