# FutureF1 Backend (FastAPI)

Proyecto reorganizado para backend FastAPI + PostgreSQL en Docker.

## Arquitectura de ejecución
- Contenedor `backend` (FastAPI)
- Contenedor `db` (PostgreSQL)
- Red virtual compartida `futuref1_net`
- El frontend se puede levantar en otro repo/equipo y unirse a la misma red Docker.

## Levantar entorno local
1. Copia `.env.example` a `.env`.
2. Ejecuta:
   `docker compose up --build`
3. API:
   - http://localhost:8000/api/v1/health
   - Docs: http://localhost:8000/docs

## Tests de endpoints
- Local (sin Docker):
  `pip install -r backend/requirements-dev.txt`
  `pytest backend/tests -q`
- Docker:
  `docker compose run --rm backend pytest tests -q`

## Endpoints (módulos creados)
- `auth`, `seasons`, `race-events`, `testing-events`
- `countries`, `circuits`, `contexts`, `bets`
- `results`, `ranking`, `rules`, `powerups`, `roster`, `stream`

Se ha dejado una base de respuesta mock para acelerar integración con frontend y permitir TDD desde ya.
