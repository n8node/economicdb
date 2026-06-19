# Макроаналитика (economicdb.com)

B2B SaaS макроэкономической аналитики. Стек: WordPress + Next.js + FastAPI + PostgreSQL.

## Репозиторий

https://github.com/n8node/economicdb

## Production server

| Параметр | Значение |
|----------|----------|
| OS | Ubuntu 26 |
| IP | `194.67.120.118` |
| Домен | `economicdb.com` |
| Путь | `/opt/economicdb` |
| SSH | `ssh root@194.67.120.118` |

**Предусловие:** DNS A-записи `economicdb.com` и `www.economicdb.com` → `194.67.120.118`.

### Первый деплой (на сервере)

```bash
ssh root@194.67.120.118
```

```bash
apt-get update && apt-get install -y git curl
cd /opt
git clone https://github.com/n8node/economicdb.git
cd economicdb
chmod +x scripts/*.sh
./scripts/setup-server.sh
export ADMIN_INITIAL_PASSWORD='YOUR_PASSWORD_HERE'
./scripts/first-deploy.sh
```

Проверка:

```bash
curl -sf http://127.0.0.1/health
curl -sfk https://127.0.0.1/health -H "Host: economicdb.com"
```

Открыть в браузере: https://economicdb.com/health , https://economicdb.com/adminus/

### Firewall (если включён UFW)

```bash
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
```

### Обновление с локальной машины

```bash
DEPLOY_SERVER=root@194.67.120.118 ./scripts/deploy.sh main
```

## Первый деплой (общая инструкция)

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
