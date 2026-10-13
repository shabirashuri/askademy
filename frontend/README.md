# Frontend

React and TypeScript client for Smart Item Bank, built with Vite.

## Requirements

- Node.js 20.19+ or 22.13+
- npm
- The FastAPI backend running locally at `http://localhost:8000` (see [backend setup](../backend/README.md))

## Install and run

From the repository root:

```bash
cd frontend
npm ci
npm run dev
```

Open `http://localhost:5173` in a browser. The development server binds to all interfaces.

Keep this frontend terminal running while you use the app. Use `Ctrl+C` to stop Vite.

By default, the frontend calls `http://localhost:8000/api/v1`. To use another backend URL, create `frontend/.env` (or set the variable in your shell) with:

```dotenv
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

Restart the Vite server after changing environment variables.

## Available commands

Run these commands from `frontend/`:

```bash
npm run dev
npm run lint
npm run build
```

`npm run build` type-checks the TypeScript application and creates the production bundle in `dist/`.
