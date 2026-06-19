.PHONY: dev prod down migrate logs logs-prod status deploy first-deploy setup-server backup-db backup-wp psql wp-cli lint test setup

dev:
	docker compose up --build -d

down:
	docker compose down

logs:
	docker compose logs -f

prod:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml up --build -d

logs-prod:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f

status:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml ps

migrate:
	docker compose exec backend alembic upgrade head

deploy:
	./scripts/deploy.sh main

first-deploy:
	./scripts/first-deploy.sh

setup-server:
	sudo ./scripts/setup-server.sh

setup:
	./scripts/setup.sh

ssl-init:
	./scripts/ssl-init.sh

backup-db:
	docker compose exec -T postgres pg_dump -U $(POSTGRES_USER) $(POSTGRES_DB) \
		| gzip > backups/pg_$(shell date +%Y%m%d_%H%M%S).sql.gz

backup-wp:
	docker compose exec -T mysql mysqldump -u $(WP_DB_USER) -p$(WP_DB_PASSWORD) $(WP_DB_NAME) \
		| gzip > backups/wp_$(shell date +%Y%m%d_%H%M%S).sql.gz

psql:
	docker compose exec postgres psql -U $(POSTGRES_USER) -d $(POSTGRES_DB)

lint:
	cd backend && ruff check .

test:
	cd backend && pytest -v
