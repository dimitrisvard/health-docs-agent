.RECIPEPREFIX = >
.PHONY: up down seed test eval lint

up:
> docker compose up --build

down:
> docker compose down

seed:
> docker compose exec mcp python -m ingest.seed data/

test:
> (cd services/agent && PYTHONPATH=. pytest -q)
> (cd services/mcp && PYTHONPATH=. pytest -q)
> PYTHONPATH=. pytest evals -q
> cd apps/web && npm test --silent --if-present

eval:
> docker compose exec agent python -m evals.run

lint:
> (cd services/agent && ruff check . && PYTHONPATH=. mypy app) || true
> (cd services/mcp && ruff check .) || true
> cd apps/web && npm run lint --if-present
