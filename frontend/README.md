# Frontend CuisineAuSort

React 19 + Vite + TypeScript. Pas de bibliothèque de composants : CSS simple (`src/index.css`).

- **React Router** : navigation (`src/App.tsx`)
- **TanStack Query** : appels API, cache et invalidation (`src/api/queries.ts`)
- **openapi-typescript** + **openapi-fetch** : client API typé, généré depuis l'OpenAPI du backend
- **Vitest** + Testing Library : tests ; **oxlint** : lint

## Démarrage

Le backend doit tourner sur `http://127.0.0.1:8000` (voir [backend/README.md](../backend/README.md)).

```bash
npm install
npm run dev        # http://localhost:5173
```

En développement, Vite relaie `/api/*` vers le backend (`vite.config.ts`) : pas de configuration
CORS nécessaire. Pour viser une autre API (build de production), définir `VITE_API_BASE_URL`
(ex. `VITE_API_BASE_URL=https://api.example.com npm run build`).

## Client API généré

`openapi.json` (schéma exporté du backend) et `src/api/schema.d.ts` (types générés) sont versionnés,
pour que le frontend compile sans backend. **Après toute modification de l'API** :

```bash
npm run api:generate   # = api:openapi (export via uv, sans lancer le serveur) + api:types
```

Les erreurs de typage signalent alors le code frontend à adapter. Les alias de types utilisés dans
l'application sont dans `src/api/types.ts`.

## Qualité

```bash
npm run typecheck
npm run lint
npm test
npm run build
```

## Organisation

```
src/
├── api/          # client généré, alias de types, hooks TanStack Query
├── components/   # mise en page, messages de chargement/erreur
├── lib/          # logique pure et testée : libellés, formatage, formulaire de recette
├── pages/        # une page par route
└── test/         # configuration Vitest, faux backend (mockApi) et rendu (renderPage)
```

## Remarque : version de TypeScript

Le projet utilise TypeScript **5.9** (et non 7, proposé par le gabarit Vite) : `openapi-typescript`
ne prend pas encore en charge TypeScript 7. Le mode `strict` est activé explicitement dans les
`tsconfig` (il ne l'est par défaut qu'à partir de TypeScript 7).
