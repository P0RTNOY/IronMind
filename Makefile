.PHONY: test-api test-api-ci

test-api:
	docker exec -e ENV=test api-api-1 python -m pytest tests/ -v

test-api-ci:
	docker compose -f apps/api/docker-compose.yml build api
	docker compose -f apps/api/docker-compose.yml run -e ENV=test api python -m pytest tests/ -v
