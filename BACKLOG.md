# Backlog — Макроаналитика

## Scaffold (текущий этап)

- [x] Docker Compose + Nginx + WordPress + PostgreSQL + Redis
- [x] FastAPI health + Alembic + seed super_admin
- [x] Next.js placeholder `/app`, `/adminus`
- [x] First-deploy scripts (Docker install, SSL, .env generation)
- [x] Admin auth UI + JWT login
- [x] Dashboard «Обзор» на реальных рядах FRED/ЦБ без demo fallback
- [x] ETL schema + providers admin + FRED/ЦБ sync
- [x] DATA_CATALOG multisource-пакет: +97 показателей, hidden until ETL verification
- [x] Calendar ETL: FRED/CBR/ECB/FOMC/Rosstat release ingestion + enricher + admin sync UI
- [ ] Перенос остальных mockups → React (indicators, compare, summaries)
- [x] OpenRouter admin settings UI (`/adminus/settings`: key, test, models, model for digest)
- [x] OpenRouter weekly digest worker + facts builder + validator
- [ ] Robokassa billing
- [ ] Admin settings UI (SMTP, Robokassa)

## Design gaps

- [x] Карточка показателя MVP: `/app/indicators/[id]`, stats/related/events API, uPlot chart (tooltip, zoom, brush)
- [ ] Настройки
- [x] Избранное — localStorage + дашборд `/app` (без аккаунта/синхронизации)

## Mock/demo gaps (не баги)

- [x] Реальные calendar events подключены к провайдерам (FRED, CBR, ECB, FOMC, Росстат)
- Calendar forecast «—»
- AI archive filters в demo
