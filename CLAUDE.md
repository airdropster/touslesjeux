# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TousLesJeux is a board game data enrichment web application. It collects board game information from the web (via Google Custom Search), enriches metadata using OpenAI (GPT-4o-mini) for theme, mechanics, complexity, player count, and more, then stores structured results in PostgreSQL. A React frontend provides a dashboard for browsing, editing, and managing game collections.

## Stack

- **Backend:** FastAPI (Python 3.12) + SQLAlchemy (async) + Alembic migrations
- **Frontend:** React 19 + TypeScript + Vite + Shadcn/ui + Tailwind CSS
- **Database:** PostgreSQL 16
- **Infrastructure:** Docker + Docker Compose

## Development Setup

```bash
# Start dev database
docker compose -f docker-compose.dev.yml up -d

# Install backend dependencies
cd backend && pip install -e ".[dev]"

# Run database migrations
cd backend && alembic upgrade head

# Start backend dev server
cd backend && uvicorn app.main:app --reload

# Start frontend dev server (separate terminal)
cd frontend && npm install && npm run dev
```

The frontend dev server runs on `http://localhost:5173` and proxies API calls to the backend on `http://localhost:8000`.

## Testing

```bash
cd backend && python -m pytest tests/ -v
```

## Production

```bash
docker compose up --build
```

This builds the frontend, copies static assets into the backend image, and runs behind a security-hardened container configuration (read-only filesystem, no-new-privileges, memory limits).

## Project Structure

```
backend/
  app/
    main.py            # FastAPI app with lifespan, CORS, static file serving
    config.py          # Pydantic settings (env vars)
    database.py        # Async SQLAlchemy session
    models.py          # SQLAlchemy ORM models (Game, Job, etc.)
    schemas.py         # Pydantic request/response schemas
    auth.py            # API key authentication
    worker.py          # Background worker for collection jobs
    routers/
      health.py        # Health check endpoint
      games.py         # CRUD endpoints for games
      collections.py   # Collection orchestration with SSE streaming
    services/
      collector.py     # Orchestrator: scrape -> enrich -> store pipeline
      scraper.py       # Google CSE integration with allowlist and HTML sanitization
      enricher.py      # OpenAI integration with prompt templates and validation
      dedup.py         # Deduplication service
  alembic/             # Database migration scripts
  tests/               # Pytest test suite
  pyproject.toml       # Python package config and dependencies

frontend/
  src/
    App.tsx            # Router and layout
    main.tsx           # Entry point
    pages/
      Dashboard.tsx    # Overview with stats
      GameList.tsx     # Paginated game list with filters
      GameDetail.tsx   # Single game view
      GameEdit.tsx     # Game edit form
      Collect.tsx      # Launch collection jobs
      CollectionDetail.tsx  # Live collection progress via SSE
    components/
      GameTable.tsx    # Sortable game data table
      GameFilters.tsx  # Filter controls
      GameForm.tsx     # Edit form fields
      GameDetail.tsx   # Detail display component
      StatsCards.tsx   # Dashboard statistics cards
      CategorySelector.tsx  # Category picker
      CollectionProgress.tsx  # SSE-driven progress display
      ui/              # Shadcn/ui primitives
    hooks/
      useGames.ts      # Game data fetching hooks
      useCollections.ts  # Collection management hooks
      useSSE.ts        # Server-Sent Events hook
    lib/
      api.ts           # API client (fetch wrapper with auth)
      types.ts         # TypeScript type definitions
      utils.ts         # Utility functions

docker-compose.yml      # Production setup (backend + postgres)
docker-compose.dev.yml  # Dev database only
.env.example            # Environment variable template
```

## Environment Variables

See `.env.example` for the full list:

| Variable | Purpose |
|---|---|
| `OPENAI_API_KEY` | OpenAI API key for game enrichment |
| `GOOGLE_CSE_API_KEY` | Google Custom Search Engine API key |
| `GOOGLE_CSE_CX` | Google Custom Search Engine ID |
| `DB_USER` | PostgreSQL username |
| `DB_PASSWORD` | PostgreSQL password |
| `DATABASE_URL` | Full async database connection string |
| `APP_API_KEY` | API key for backend authentication |
| `CORS_ORIGINS` | Allowed CORS origins (comma-separated) |

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `GET` | `/api/games` | List games (paginated, filterable) |
| `GET` | `/api/games/{id}` | Get single game |
| `PUT` | `/api/games/{id}` | Update game |
| `DELETE` | `/api/games/{id}` | Delete game |
| `POST` | `/api/collections` | Launch a collection job |
| `GET` | `/api/collections/{id}` | Get collection job status |
| `GET` | `/api/collections/{id}/stream` | SSE stream for live progress |
| `POST` | `/api/collections/{id}/cancel` | Cancel a running job |

## Data Schema

Each enriched game includes: `id`, `title`, `year`, `designer`, player counts, duration, `complexity_score_1_to_10`, `summary`, `regles_detaillees` (cleaned full rules text), `theme[]`, `mechanics[]`, `components[]`, `core_mechanics[]`, `public[]`, `niveau_interaction`, `famille_materiel[]`, `tags[]`, `editeur`, `type_jeu_famille[]`, `lien_bgg`.
