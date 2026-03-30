# ORM y Migraciones

## Instalar dependencias
pip install -r requirements-dev.txt

## Crear nueva migraciones
docker compose run --rm backend alembic revision --autogenerate -m "..."

## Aplicar migraciones
docker compose run --rm backend alembic upgrade head

## Ver en qué versión estas
docker compose run --rm backend alembic current

## Ver historial
docker compose run --rm backend alembic history --verbose

## Ver SQL que se aplicaría(sin ejecutar)
docker compose run --rm backend alembic upgrade head --sql

## Comprobar en Postgres que existen tablas/schemas
docker compose exec db psql -U postgres -d futuref1 -c "\dn"
docker compose exec db psql -U postgres -d futuref1 -c "\dt auth.*"
docker compose exec db psql -U postgres -d futuref1 -c "\dt competition.*"

## build
docker compose build backend