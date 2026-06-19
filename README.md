# Макроаналитика (economicdb.com)

B2B SaaS макроэкономической аналитики. Стек: WordPress + Next.js + FastAPI + PostgreSQL.

## Репозиторий

https://github.com/n8node/economicdb

## Первый деплой на сервер

**Предусловие:** DNS `economicdb.com` → IP сервера.

```bash
sudo apt-get update && sudo apt-get install -y git
cd /opt
sudo git clone https://github.com/n8node/economicdb.git
cd economicdb
chmod +x scripts/*.sh
sudo ./scripts/setup-server.sh
export ADMIN_INITIAL_PASSWORD='your-secure-password'
./scripts/first-deploy.sh
```

После деплоя:

| URL | Назначение |
|-----|------------|
| https://economicdb.com/ | WordPress (лендинг) |
| https://economicdb.com/app/ | Продукт |
| https://economicdb.com/adminus/ | Админка |
| https://economicdb.com/health | Health check |

Admin email по умолчанию: `erman.ai@yandex.ru`

## Обновление (production)

```bash
cd /opt/economicdb
git pull origin main
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

## Локальная разработка

```bash
cp .env.example .env
# заполнить пароли
make dev
```

Открыть: http://localhost/app , http://localhost/adminus , http://localhost/health

## Документация

- `docs/PROJECT_CONTEXT.md` — продукт и архитектура
- `.cursor/rules/` — правила для Cursor
- `design/mockups/` — UI baseline
