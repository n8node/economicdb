# Макроаналитика — контекст проекта

Документ фиксирует решения из проектирования продукта (июнь 2026). Использовать как единый источник контекста для новых чатов и разработки в workspace `Macro`.

---

## 1. Продукт

**Название:** Макроаналитика  
**Тип:** B2B / B2Pro SaaS  
**Рынок:** пользователи из России  
**Язык UI и контента:** только русский  

**Ценность:** единое место для работы с макроэкономическими данными РФ и зарубежных рынков — просмотр, фильтрация, сравнение, календарь релизов, AI-еженедельные сводки на русском.

**Целевая аудитория:**
- аналитик / экономист / PM в компании;
- продвинутый частный инвестор;
- пользователь, которому нужны **цифры + контекст**, а не сырой API.

**Не делать:**
- aesthetic биржевого терминала (TradingView-style overload);
- chat-bot на весь экран вместо structured digest;
- парсинг Trading Economics (запрещено ToS, bot protection);
- английские labels в UI.

---

## 2. Домен, роутинг и платформа

**Домен:** `economicdb.com` — **только подпапки, без поддоменов.**

| Путь | Сервис |
|------|--------|
| `economicdb.com/` | WordPress (лендинг, блог, pricing, legal) |
| `economicdb.com/wp-admin/` | WordPress admin |
| `economicdb.com/app/` | Next.js — продукт «Макроаналитика» |
| `economicdb.com/adminus/` | Next.js — административная панель (скрытый URL) |
| `economicdb.com/api/v1/...` | Python FastAPI backend |
| `economicdb.com/health` | FastAPI health |

**Платформа:** только **web**. Mobile app, Telegram Mini App — не в scope.

**Cursor rules:** `.cursor/rules/` — стек, деплой, админка, AI pipeline.

### Стек (зафиксирован)

| Слой | Технология |
|------|------------|
| Frontend | Next.js 15+, App Router, Tailwind, shadcn/ui |
| Backend API | Python 3.12+, FastAPI, SQLAlchemy 2.0, Alembic |
| Analytics / ETL | pandas, httpx; workers (ARQ/APScheduler) + Redis |
| БД | PostgreSQL 16, pg_trgm |
| Лендинг | WordPress (Docker) |
| Proxy | Nginx (Docker) |
| Deploy | Docker Compose, `/opt/economicdb` |

### Секреты и интеграции — политика «ключи в админке»

**В `.env` — только bootstrap инфраструктуры:**
- `DATABASE_URL`, `POSTGRES_*`, `WP_*`
- `JWT_SECRET`, `SETTINGS_ENCRYPTION_KEY`
- `DOMAIN`, `ENVIRONMENT`, `REDIS_URL`

**В админке (`/adminus`) — всё остальное, зашифровано at rest (AES-256-GCM):**

| Группа | Где хранится | Примеры ключей |
|--------|--------------|----------------|
| OpenRouter | `system_settings` | `openrouter.api_key`, `openrouter.model_digest` |
| Robokassa | `system_settings` | `robokassa.merchant_login`, `password1`, `password2` |
| SMTP Яндекс | `system_settings` | `smtp.host`, `smtp.login`, `smtp.password`, `from_email` |
| Провайдеры данных | `data_providers` | FRED API key, EconDB key, base_url per provider |

Админка: CRUD провайдеров, «Проверить подключение», «Sync сейчас», test email, audit log на каждую мутацию.

### Первый деплой и super_admin

На чистом сервере один скрипт поднимает всё:

```bash
sudo ./scripts/setup-server.sh          # Docker + Certbot
export ADMIN_INITIAL_PASSWORD='...'    # только на сервере, не в git!
./scripts/first-deploy.sh               # compose + SSL + seed admin
```

| Параметр | Значение |
|----------|----------|
| URL админки | `https://economicdb.com/adminus/` |
| Email по умолчанию | `erman.ai@yandex.ru` (`ADMIN_INITIAL_EMAIL` в `.env`) |
| Пароль | `ADMIN_INITIAL_PASSWORD` в `.env` на сервере |
| Seed | Backend создаёт `super_admin` если `admin_users` пуста |

### Платежи и email

- **Robokassa** — единственный провайдер оплаты тарифов (Free / Pro / Business).
- **SMTP Яндекс** — digest-подписка, алерты, transactional mail; настраивается в админке.

---

## 3. Техническая архитектура (целевая)

```
ETL (ЦБ, Росстат, FRED, IMF, OECD, ECB…) → PostgreSQL
         ↓
Analytics Engine (Python/pandas) — WoW/MoM, min/max, surprise vs forecast
         ↓
Weekly Facts JSON (только проверенные числа + metadata)
         ↓
OpenRouter API (LLM) — narrative на русском, structured output
         ↓
Validator (цифры в тексте ⊆ facts)
         ↓
UI / Email / PDF
```

**Принцип facts-first:** модель **не достаёт и не считает** данные — только интерпретирует подготовленный fact-пакет. Иначе галлюцинации.

**OpenBB Platform (ODP):**
- Open-source инфраструктура агрегации фин/макро данных.
- Лицензия **AGPL v3** — для публичного SaaS нужна полная AGPL-compliance (раскрытие исходников) **или** коммерческая лицензия OpenBB.
- Можно использовать как backend-слой ingestion/API, но учитывать legal при SaaS.

**AI (OpenRouter):**
- Один API, много моделей, structured JSON, fallback.
- API key и модели — **из админки** (`system_settings`), не из `.env`.
- Генерировать сводку **сразу на русском** (1 вызов LLM), не EN → перевод.
- Статические метки показателей/стран — словарь в коде/БД, не через LLM.
- Structured output (JSON schema) для секций, bullets, citation keys.

---

## 4. Источники данных

### Доступны из РФ (официальные, бесплатные)

| Источник | Что даёт | API |
|----------|----------|-----|
| **Банк России** | ставка, курсы, часть статистики | REST JSON |
| **Росстат** | ИПЦ, промпроизводство, ВВП и др. | EMISS/SDMX; парсеры (mini-kep) |
| **FRED** | US macro, часть RU series | REST (нужен API key) |
| **IMF** | глобальная макро | SDMX API |
| **World Bank** | индикаторы по странам | REST JSON |
| **OECD** | HICP, composite indicators | SDMX REST |
| **ECB / Eurostat** | EU macro | SDMX REST |
| **MOEX ISS** | рыночные данные (не календарь macro) | REST |
| **EconDB** | глобальная macro API | REST (free tier) |

### Ограничения и риски

| Источник | Проблема |
|----------|----------|
| **FRED** | ToS ограничивает commercial redistribution; Russia CPI на FRED может быть устаревшим |
| **Trading Economics** | API недоступен из РФ (санкции); scraping запрещён ToS + Cloudflare/bot detection |
| **Cbonds** | платный API, macro для РФ — опционально позже |
| **Consensus / forecast** | **нет универсального бесплатного** источника; в MVP — «—», editorial tier или платный провайдер |

### MVP-стратегия по данным

1. **Tier A:** ставки ЦБ, FOMC, ECB — расписания с официальных сайтов.
2. **Tier B:** ИПЦ, промпроизводство, GDP — даты релизов Росстат + FRED release calendar.
3. **Tier C:** прогноз/consensus — часто недоступен бесплатно; UI должен переживать placeholder «прогноз недоступен».

**Badges источников в UI:** Банк России, Росстат, FRED, IMF, OECD, ECB/Eurostat (muted colors).

---

## 5. Design system (согласовано в макетах)

**Visual language:** профессиональный финтех, desktop-first, light + dark mode.

| Token | Значение |
|-------|----------|
| Шрифт UI | Inter |
| Шрифт цифр | JetBrains Mono |
| Primary | teal `#1B7561` / `#2F9C84` |
| Фон страницы | `#F7F8FA` |
| Карточки | white, border `#E4E7EC`, radius 14px |
| Sidebar | 248px |

**Навигация (sidebar):**
1. Обзор (Dashboard)
2. Показатели (каталог)
3. Сравнение
4. Календарь
5. AI-сводки
6. Избранное
7. Настройки

**Topbar:** глобальный поиск, light/dark toggle.

**UX-принципы:**
1. На каждом виджете — источник + дата обновления.
2. AI-текст визуально отделён от сырых данных (tinted `--primary-50`, badge «AI-сводка»).
3. Цифры в AI-сводках — inline citations → popover → карточка показателя.
4. Disclaimer: «Сгенерировано AI · не инвестиционная рекомендация».

**Макеты (design baseline):** см. `design/mockups/` — все экраны ниже reviewed и approved (~90–96% match с промптами).

---

## 6. Экраны UI (статус проектирования)

| # | Экран | Файл макета | Статус | Match |
|---|-------|-------------|--------|-------|
| 1 | Обзор (Dashboard) | `dashboard.html` | ✅ baseline | ~85–90% |
| 2 | Каталог показателей | `indicators.html` | ✅ baseline | ~90% |
| 3 | Сравнение | `compare.html` | ✅ baseline | ~92–95% |
| 4 | Календарь | `calendar.html` | ✅ baseline | ~93–95% |
| 5 | AI-сводки | `ai-summaries.html` | ✅ baseline | ~94–96% |
| 6 | Карточка показателя | — | 🔲 не макетирован | — |
| 7 | Избранное | — | 🔲 не макетирован | — |
| 8 | Настройки | — | 🔲 не макетирован | — |

### 6.1 Dashboard «Обзор»

- KPI-лента: ставка ЦБ, инфляция РФ, USD/RUB, US CPI, Fed Funds (+ delta + sparkline).
- AI weekly summary card (headline, 3 bullets, CTA «Читать полностью»).
- События недели (мини-календарь).
- Избранные показатели.
- Sample data согласовано с другими экранами.

### 6.2 Каталог показателей

- Sticky filter panel: регион, категория, частота, источник, давность обновления.
- Таблица / карточки, sort, pagination, bulk actions.
- Active filter chips, empty/loading states.

### 6.3 Сравнение

- До 6 серий на графике, presets (Ставки, Инфляция, FX, ВВП).
- Режимы: абсолютные / индекс (100) / изменение %.
- Warning при разных единицах, сводная таблица min/max/avg/Δ.

### 6.4 Календарь

- Views: список / неделя / месяц.
- Фильтры: страна, важность, категория, статус (предстоящие/прошедшие).
- Past events: actual / forecast / previous + surprise badge.
- Event drawer справа, ICS export, напоминания, timezone МСК.
- **Forecast** — главная data gap; UI с disclaimer и «—» где нет данных.

### 6.5 AI-сводки

**Архив:**
- Pinned «Последняя сводка» (контент = teaser на Dashboard).
- Grid карточек прошлых недель, фильтры период/регион.
- Sidebar: подписка на digest, блок «Как формируется сводка».

**Деталь (long-read):**
- Executive summary, секции: Россия / США / Еврозона / Рынки и FX / На следующей неделе / Риски.
- Inline citations → popover (value, delta, source, date, «Открыть показатель»).
- Sticky TOC (scroll spy), PDF/Email/Share placeholders.
- Sources accordion, disclaimer block.

**Citation data (demo, все из бесплатных источников):**

| Key | Показатель | Значение | Источник |
|-----|------------|----------|----------|
| cbr-rate | Ключевая ставка ЦБ | 21,00% | Банк России |
| ru-cpi | ИПЦ РФ, г/г | 9,52% | Росстат |
| usdrub | USD/RUB | 92,40 | Банк России |
| us-cpi | US CPI, г/г | 3,2% | FRED |
| fed-rate | Fed Funds | 5,25–5,50% | FRED |
| eu-hicp | HICP EU, г/г | 2,1% | OECD |
| ecb-rate | ECB rate | 3,75% | ECB |
| us-cpi-forecast | CPI consensus | 3,4% | ⚠️ editorial tier |

---

## 7. Sample data (единый набор для прототипов)

| Показатель | Значение | Δ |
|------------|----------|---|
| Ключевая ставка ЦБ | 21,00% | 0 |
| ИПЦ РФ, г/г | 9,52% | +0,64 п.п. |
| USD/RUB | 92,40 | +1,2% |
| US CPI, г/г | 3,2% | −0,1 п.п. |
| Fed Funds | 5,25–5,50% | 0 |
| HICP EU, г/г | 2,1% | −0,1 п.п. |

**AI-сводка (teaser):** «ЦБ удержал ставку, инфляция в США замедлилась сильнее ожиданий» — период 16–22 июня 2026.

**Календарь (ближайшие):** ECB 23.06, промпроизводство РФ 24.06, US PCE 26.06.

---

## 8. Backend — ключевые сущности (черновик)

### `indicators`
Каталог рядов: id, name_ru, country, category, frequency, source, external_id, last_value, last_change, updated_at.

### `economic_events`
Календарь: id, title_ru, country, category, importance (high/med/low), scheduled_at_msk, actual, forecast, previous, surprise, linked_indicator_id, source, tier (A/B/C).

### `weekly_summaries`
AI-сводки: id, period_start, period_end, headline, sections (JSON), citations (JSON map key → indicator_id + value), generated_at, word_count, source_count, tags[].

### `user_favorites`, `user_settings`
Избранное, digest subscription, default markets.

### `system_settings`, `data_providers`, `admin_users`, `admin_audit_log`
Секреты (OpenRouter, Robokassa, SMTP), провайдеры данных, админка.

---

## 9. AI pipeline (weekly digest)

1. **Cron** (понедельник ~08:00 МСК после закрытия недели).
2. **Analytics engine** собирает facts: изменения KPI, surprises из календаря, ключевые события следующей недели.
3. **Facts JSON** → prompt → **OpenRouter** (structured output, русский narrative).
4. **Validator:** каждое число в тексте должно быть в facts; иначе reject/retry.
5. Сохранение в `weekly_summaries`, push на Dashboard pinned card + email (optional).

**Prompt constraints:**
- Писать только на русском.
- Не выдумывать цифры — только из facts.
- Секции фиксированы (schema).
- Citation keys для привязки к `indicators`.

**Не в MVP:** произвольный chat «спроси AI», confidence score, EN→RU перевод.

---

## 10. Known gaps / polish из review макетов

| Экран | Gap | Приоритет |
|-------|-----|-----------|
| Compare | Presets FX/ВВП не переключают данные в JS demo | low (prototype) |
| Calendar | Forecast/consensus часто «—» | expected (data) |
| Calendar | Drawer статичен в demo | low |
| AI-summaries | Фильтры не скрывают карточки в demo | low |
| AI-summaries | Все карточки архива → одна деталь | low (prototype) |
| All | Mobile bottom nav не везде | medium |
| Indicator detail | Экран не спроектирован | **next design** |
| Favorites / Alerts | Не спроектированы | next design |

---

## 11. Legal / compliance checklist

- [ ] OpenBB AGPL — решение: commercial license vs open-source compliance.
- [ ] FRED ToS — не redistributing raw API responses без ограничений; кеширование по policy.
- [ ] AI disclaimer на каждом AI-блоке.
- [ ] Не scraping TE и других commercial aggregators.
- [ ] Персональные данные (email digest) — политика при рассылке.

---

## 12. Следующие шаги (backlog)

**Design:**
- [ ] Промпт + макет «Карточка показателя»
- [ ] Промпт + макет «Избранное»
- [ ] Промпт + макет «Настройки»

**Engineering:**
- [ ] Scaffold: Docker + Nginx + WordPress + FastAPI + Next.js + PostgreSQL + Redis
- [ ] Admin: `system_settings`, `data_providers`, SMTP/OpenRouter/Robokassa UI
- [ ] ETL: ЦБ + FRED + OECD (первые 3 провайдера)
- [ ] Schema `indicators`, `economic_events`, `weekly_summaries`
- [ ] OpenRouter digest + facts validator
- [ ] Robokassa billing + plan gating
- [ ] Перенос HTML mockups → React components + design tokens

**Data:**
- [ ] Схема tier A/B/C для календаря
- [ ] Mapping citation keys ↔ indicator IDs
- [ ] Release calendar ingestion (CBR, Rosstat, FRED)

---

## 13. Как использовать этот документ в Cursor

```
@docs/PROJECT_CONTEXT.md @design/mockups/ @.cursor/rules/
Продолжаем разработку «Макроаналитика» согласно контексту.
```

При значимых решениях — **обновлять этот файл**, а не полагаться на историю чата.

---

*Последнее обновление: 19.06.2026*
