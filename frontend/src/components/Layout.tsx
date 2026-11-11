import { NavLink, Outlet } from 'react-router'

const LINKS = [
  { to: '/recipes', label: 'Recettes' },
  { to: '/ingredients', label: 'Ingrédients' },
  { to: '/draw', label: 'Tirage au sort' },
  { to: '/plans', label: 'Plannings' },
]

export function Layout() {
  return (
    <>
      <header className="app-header">
        <NavLink to="/" className="brand">
          🎲 CuisineAuSort
        </NavLink>
        <nav>
          {LINKS.map(({ to, label }) => (
            <NavLink key={to} to={to}>
              {label}
            </NavLink>
          ))}
        </nav>
      </header>
      <main className="app-main">
        <Outlet />
      </main>
    </>
  )
}
