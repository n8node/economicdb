# DATA_CATALOG — каталог показателей Макроаналитики

Источник правды для ETL shortlist: **~150 макро-показателей** (целевой объём 150–200, расширяем до 200 во W5).

**Не включено:** EconDB, Trading Economics, consensus/forecast (Tier C — editorial или «—» в UI).

---

## Легенда

| Колонка | Значение |
|---------|----------|
| **ETL** | `done` — в продукте; `next` — следующая волна; `backlog` — shortlist |
| **country** | ISO-подобный код в БД: `ru`, `us`, `eu`, `cn`, `jp`, `gb`, `de`, `world`… |
| **freq** | `D` daily, `M` monthly, `Q` quarterly, `A` annual |
| **5y** | Можно ли стабильно загрузить **≥5 лет** истории через API (см. раздел ниже) |

---

## Ответы на продуктовые вопросы

### Будет ли разбивка по странам?

**Да.** Каждый показатель в PostgreSQL — отдельная строка `indicators` с полем `country` (см. `backend/app/models/indicators.py`).

| Уровень | Как работает |
|---------|----------------|
| **Карточка показателя** | Одна страна (`ru`, `us`, `eu`…) + один источник |
| **Каталог / фильтры** | Facet `countries` + `categories` + `source` |
| **Compare presets** | Сравнение **разных** показателей (не обязательно одной метрики по странам) |
| **IMF / World Bank** | Один код показателя × **N стран** = N записей в каталоге (`cn_gdp_yoy`, `ru_gdp_yoy_wb`, `de_gdp_yoy_wb`…) |

**Не делаем:** один показатель с multi-country dimension внутри одной series (как в Excel pivot). Для SaaS-паттерна «карточка + sparkline» — **1 indicator id = 1 country**.

**Региональные агрегаты:** `eu` (Euro area / EA20), `world` (глобальные ряды: Brent, некоторые WB/IMF).

### Можем ли взять историю за 5 лет?

**Да, для подавляющего большинства shortlist — без проблем.** Исключения помечены в таблицах.

| Источник | 5 лет | Типичная глубина | Оговорки |
|----------|-------|------------------|----------|
| **ЦБ** | ✅ | 10–30+ лет (курсы с 1990-х) | Ставка — с ~2013 |
| **Росстат / fedstat** | ✅ | 5–25 лет | Пром. произв. OKVED2 — с **2015**; нужен POST с фильтрами по **годам** |
| **FRED** | ✅ | 30–100+ лет | API key; ToS на redistribution |
| **OECD** | ✅ | 10–30 лет | SDMX narrow keys |
| **IMF** | ✅ | 10–40 лет (WEO) | 132 фикс. показателя |
| **ECB / Eurostat** | ✅ | 10–25 лет | HICP — не запрашивать будущие месяцы |
| **World Bank** | ✅ | 10–65 лет | Зависит от страны; RU GDP с ~1989 |
| **MOEX** | ✅ | 5–20+ лет | IMOEX — с 1990-х; default ETL с 2020 → расширяем `from_date` |

**Правило ETL:** `DEFAULT_FROM_DATE` для sync = `today - 5 years` (или `2000-01-01` где глубже нужна для Compare «5Y»). Fedstat — обязательно multi-year filter, иначе API отдаёт только один год.

---

## Уже в ETL (`done`) — 15 показателей

| id | name_ru | country | cat | freq | source | external_id |
|----|---------|---------|-----|------|--------|-------------|
| cbr_key_rate | Ключевая ставка ЦБ | ru | rates | M | cbr | KeyRate |
| usd_rub | USD / RUB | ru | fx | D | cbr | R01235 |
| ru_cpi_yoy | ИПЦ России, г/г | ru | inflation | M | rosstat | fedstat:31074 |
| ru_industrial_yoy | Пром. производство, г/г | ru | industrial | M | rosstat | fedstat:57806 |
| eu_hicp_yoy | HICP EU, г/г | eu | inflation | M | oecd | EA20.M.HICP.CPI.PA._T.N.GY |
| eu_hicp_yoy_eurostat | HICP EU, г/г (Eurostat) | eu | inflation | M | eurostat | PRC_HICP_MANR/M.RCH_A.CP00.EA20 |
| ecb_deposit_rate | ECB Deposit Facility Rate | eu | rates | M | ecb | FM/D.U2.EUR.4F.KR.DFR.LEV |
| fed_funds | Fed Funds Rate | us | rates | M | fred | FEDFUNDS |
| us_cpi_yoy | US CPI, г/г | us | inflation | M | fred | CPIAUCSL |
| us_nfp | Nonfarm Payrolls | us | labor | M | fred | PAYEMS |
| us_gdp_yoy | ВВП США, г/г | us | gdp | Q | fred | A191RL1Q225SBEA |
| cn_gdp_yoy | ВВП Китая, real YoY | cn | gdp | A | imf | NGDP_RPCH/CHN |
| ru_gdp_yoy_wb | ВВП России, рост | ru | gdp | A | world_bank | NY.GDP.MKTP.KD.ZG/RU |
| imoex | Индекс MOEX | ru | equities | D | moex | stock/index/IMOEX/CLOSE |
| oil_brent | Нефть Brent | world | commodities | D | fred | DCOILBRENTEU |

---

## Shortlist — Россия (`ru`) — 28 показателей

| id | name_ru | cat | freq | source | external_id | ETL | 5y |
|----|---------|-----|------|--------|-------------|-----|-----|
| cbr_key_rate | Ключевая ставка ЦБ | rates | M | cbr | KeyRate | done | ✅ |
| usd_rub | USD / RUB | fx | D | cbr | R01235 | done | ✅ |
| eur_rub | EUR / RUB | fx | D | cbr | R01239 | next | ✅ |
| cny_rub | CNY / RUB | fx | D | cbr | R01375 | next | ✅ |
| gbp_rub | GBP / RUB | fx | D | cbr | R01035 | backlog | ✅ |
| ru_cpi_yoy | ИПЦ, г/г | inflation | M | rosstat | fedstat:31074 | done | ✅ |
| ru_cpi_mom | ИПЦ, м/м | inflation | M | rosstat | fedstat:31074/mom | backlog | ✅ |
| ru_core_cpi_yoy | ИПЦ базовый, г/г | inflation | M | rosstat | fedstat:TBD | backlog | ✅ |
| ru_industrial_yoy | Пром. производство, г/г | industrial | M | rosstat | fedstat:57806 | done | ✅* |
| ru_retail_yoy | Розничная торговля, г/г | consumption | M | rosstat | fedstat:42934 | next | ✅ |
| ru_unemployment | Безработица | labor | M | rosstat | fedstat:57614 | next | ✅ |
| ru_gdp_q_yoy | ВВП, г/г | gdp | Q | rosstat | fedstat:57746 | next | ✅ |
| ru_wages_yoy | Реальные доходы / зарплаты | labor | M | rosstat | fedstat:58548 | backlog | ✅ |
| ru_gdp_yoy_wb | ВВП, рост (WB) | gdp | A | world_bank | NY.GDP.MKTP.KD.ZG/RU | done | ✅ |
| ru_gdp_yoy_imf | ВВП, real growth (IMF) | gdp | A | imf | NGDP_RPCH/RUS | backlog | ✅ |
| imoex | Индекс MOEX | equities | D | moex | stock/index/IMOEX/CLOSE | done | ✅ |
| moex_rtsi | Индекс RTS | equities | D | moex | stock/index/RTSI/CLOSE | next | ✅ |
| moex_rgbi | Индекс гособлигаций RGBI | rates | D | moex | stock/index/RGBI/CLOSE | next | ✅ |
| moex_mcftr | MOEX Total Return | equities | D | moex | stock/index/MCFTR/CLOSE | backlog | ✅ |
| moex_bluechip | MOEX Blue Chip | equities | D | moex | stock/index/MOEXBC/CLOSE | backlog | ✅ |
| moex_usd_tom | USD/RUB TOM (MOEX) | fx | D | moex | currency/selt/USD000UTSTOM | backlog | ✅ |
| moex_eur_tom | EUR/RUB TOM (MOEX) | fx | D | moex | currency/selt/EUR_RUB__TOM | backlog | ✅ |
| ru_cpi_wb | Инфляция (WB) | inflation | A | world_bank | FP.CPI.TOTL.ZG/RU | backlog | ✅ |
| ru_unemp_wb | Безработица (WB) | labor | A | world_bank | SL.UEM.TOTL.ZS/RU | backlog | ✅ |
| ru_ca_wb | Current account % GDP (WB) | external | A | world_bank | BN.CAB.XOKA.GD.ZS/RU | backlog | ✅ |
| ru_debt_wb | Govt debt % GDP (WB) | fiscal | A | world_bank | GC.DOD.TOTL.GD.ZS/RU | backlog | ✅ |
| ru_fx_reserves | Международные резервы | external | M | cbr | SOAP:InternationalReserves | backlog | ✅ |
| ru_m2 | Денежная масса M2 | rates | M | cbr | SOAP:MoneySupply/M2 | backlog | ✅ |

\*Пром. производство OKVED2: история API с **2015**, но 5 лет с 2021 — ✅.

---

## Shortlist — США (`us`) — 32 показателя

| id | name_ru | cat | freq | source | external_id | ETL | 5y |
|----|---------|-----|------|--------|-------------|-----|-----|
| fed_funds | Fed Funds Rate | rates | M | fred | FEDFUNDS | done | ✅ |
| us_cpi_yoy | CPI, г/г | inflation | M | fred | CPIAUCSL | done | ✅ |
| us_core_cpi_yoy | Core CPI, г/г | inflation | M | fred | CPILFESL | next | ✅ |
| us_pce_yoy | PCE, г/г | inflation | M | fred | PCEPI | next | ✅ |
| us_core_pce_yoy | Core PCE, г/г | inflation | M | fred | PCEPILFE | next | ✅ |
| us_ppi_yoy | PPI, г/г | inflation | M | fred | PPIFIS | backlog | ✅ |
| us_nfp | Nonfarm Payrolls | labor | M | fred | PAYEMS | done | ✅ |
| us_unemployment | Unemployment rate | labor | M | fred | UNRATE | next | ✅ |
| us_u6 | U-6 unemployment | labor | M | fred | U6RATE | backlog | ✅ |
| us_jobless_claims | Initial jobless claims | labor | W | fred | ICSA | backlog | ✅ |
| us_avg_hourly_earnings | Avg hourly earnings YoY | labor | M | fred | AHETPI | backlog | ✅ |
| us_gdp_yoy | Real GDP, г/г | gdp | Q | fred | A191RL1Q225SBEA | done | ✅ |
| us_gdp_level | Real GDP index | gdp | Q | fred | GDPC1 | backlog | ✅ |
| us_indpro_yoy | Industrial production | industrial | M | fred | INDPRO | next | ✅ |
| us_retail_sales | Retail sales | consumption | M | fred | RSXFS | next | ✅ |
| us_durable_goods | Durable goods orders | industrial | M | fred | DGORDER | backlog | ✅ |
| us_housing_starts | Housing starts | construction | M | fred | HOUST | backlog | ✅ |
| us_consumer_sentiment | Consumer sentiment | sentiment | M | fred | UMCSENT | backlog | ✅ |
| us_10y_yield | 10Y Treasury yield | rates | D | fred | DGS10 | next | ✅ |
| us_2y_yield | 2Y Treasury yield | rates | D | fred | DGS2 | next | ✅ |
| us_yield_curve | 10Y–2Y spread | rates | D | fred | T10Y2Y | backlog | ✅ |
| us_mortgage_30y | Mortgage 30Y | rates | W | fred | MORTGAGE30US | backlog | ✅ |
| us_m2 | M2 money supply | rates | M | fred | M2SL | backlog | ✅ |
| us_fed_balance | Fed balance sheet | rates | W | fred | WALCL | backlog | ✅ |
| us_trade_balance | Trade balance | external | M | fred | BOPGSTB | backlog | ✅ |
| us_gdp_wb | GDP growth (WB) | gdp | A | world_bank | NY.GDP.MKTP.KD.ZG/US | backlog | ✅ |
| us_cpi_wb | Inflation (WB) | inflation | A | world_bank | FP.CPI.TOTL.ZG/US | backlog | ✅ |
| us_gdp_imf | GDP growth (IMF) | gdp | A | imf | NGDP_RPCH/USA | backlog | ✅ |
| us_ca_imf | Current account % GDP | external | A | imf | BCA_NGDPD/USA | backlog | ✅ |
| sp500 | S&P 500 | equities | D | fred | SP500 | next | ✅ |
| us_vix | VIX | equities | D | fred | VIXCLS | backlog | ✅ |
| oil_wti | WTI crude | commodities | D | fred | DCOILWTICO | backlog | ✅ |

---

## Shortlist — Еврозона / EU (`eu`) — 24 показателя

| id | name_ru | cat | freq | source | external_id | ETL | 5y |
|----|---------|-----|------|--------|-------------|-----|-----|
| eu_hicp_yoy | HICP EU, г/г | inflation | M | oecd | EA20.M.HICP.CPI.PA._T.N.GY | done | ✅ |
| eu_hicp_yoy_eurostat | HICP EU (Eurostat) | inflation | M | eurostat | PRC_HICP_MANR/M.RCH_A.CP00.EA20 | done | ✅ |
| ecb_deposit_rate | ECB Deposit Facility | rates | M | ecb | FM/D.U2.EUR.4F.KR.DFR.LEV | done | ✅ |
| ecb_mro_rate | ECB Main Refinancing Rate | rates | M | ecb | FM/D.U2.EUR.4F.KR.MRR_FR.LEV | next | ✅ |
| ecb_mlf_rate | ECB Marginal Lending | rates | M | ecb | FM/D.U2.EUR.4F.KR.MLFR.LEV | next | ✅ |
| ecb_estr | €STR | rates | D | ecb | EST.B.EU000A2X2A25.WT | backlog | ✅ |
| euribor_3m | Euribor 3M | rates | M | ecb | FM/M.U2.EUR.RT.MM.EURIBOR3MD_.HSTA | backlog | ✅ |
| eu_unemployment | Unemployment rate | labor | M | eurostat | ei_lmhr_m/EA20/UR | next | ✅ |
| eu_gdp_q_yoy | GDP, г/г | gdp | Q | eurostat | namq_10_gdp/EA20/B1GQ | next | ✅ |
| eu_industrial_prod | Industrial production | industrial | M | eurostat | sts_inpr_m/EA20/PROD | backlog | ✅ |
| eu_retail_trade | Retail trade | consumption | M | eurostat | sts_trtu_m/EA20/RT | backlog | ✅ |
| eu_trade_balance | Trade balance | external | M | eurostat | teina010/EA20 | backlog | ✅ |
| eu_10y_yield | Long-term gov bond yield | rates | M | eurostat | irt_lt_mcby_m/EA20/M_GBB | backlog | ✅ |
| ecb_eurusd | EUR/USD (ECB ref) | fx | D | ecb | EXR/D.USD.EUR.SP00.A | next | ✅ |
| eu_hicp_core_yoy | HICP ex energy & food | inflation | M | eurostat | PRC_HICP_MANR/M.RCH_A.XEG.N | backlog | ✅ |
| eu_hicp_energy_yoy | HICP energy | inflation | M | eurostat | PRC_HICP_MANR/M.RCH_A.NRG | backlog | ✅ |
| eu_gdp_wb | GDP growth (WB) | gdp | A | world_bank | NY.GDP.MKTP.KD.ZG/EMU | backlog | ✅ |
| eu_gdp_imf | GDP growth (IMF) | gdp | A | imf | NGDP_RPCH/EA019 | backlog | ✅ |
| eu_ca_imf | Current account % GDP | external | A | imf | BCA_NGDPD/EA019 | backlog | ✅ |
| eu_debt_imf | Govt gross debt % GDP | fiscal | A | imf | GGXWDG_NGDP/EA019 | backlog | ✅ |
| oecd_cli_eu | OECD CLI (EA) | leading | M | oecd | EA20.M.LI... | backlog | ✅ |
| de_hicp_yoy | HICP Germany, г/г | inflation | M | eurostat | PRC_HICP_MANR/M.RCH_A.CP00.DE | backlog | ✅ |
| fr_hicp_yoy | HICP France, г/г | inflation | M | eurostat | PRC_HICP_MANR/M.RCH_A.CP00.FR | backlog | ✅ |
| it_hicp_yoy | HICP Italy, г/г | inflation | M | eurostat | PRC_HICP_MANR/M.RCH_A.CP00.IT | backlog | ✅ |

---

## Shortlist — Китай (`cn`) — 12 показателей

| id | name_ru | cat | freq | source | external_id | ETL | 5y |
|----|---------|-----|------|--------|-------------|-----|-----|
| cn_gdp_yoy | ВВП, real YoY | gdp | A | imf | NGDP_RPCH/CHN | done | ✅ |
| cn_gdp_wb | GDP growth (WB) | gdp | A | world_bank | NY.GDP.MKTP.KD.ZG/CN | next | ✅ |
| cn_cpi_imf | Inflation (IMF) | inflation | A | imf | PCPIPCH/CHN | next | ✅ |
| cn_cpi_wb | Inflation (WB) | inflation | A | world_bank | FP.CPI.TOTL.ZG/CN | backlog | ✅ |
| cn_unemp_wb | Unemployment (WB) | labor | A | world_bank | SL.UEM.TOTL.ZS/CN | backlog | ✅ |
| cn_ca_imf | Current account % GDP | external | A | imf | BCA_NGDPD/CHN | backlog | ✅ |
| cn_exports_imf | Export volume growth | external | A | imf | TX_RPCH/CHN | backlog | ✅ |
| cn_imports_imf | Import volume growth | external | A | imf | TM_RPCH/CHN | backlog | ✅ |
| cn_fx_reserves_imf | Reserves months imports | external | A | imf | Reserves_M/CHN | backlog | ✅ |
| cn_debt_imf | Govt gross debt % GDP | fiscal | A | imf | GGXWDG_NGDP/CHN | backlog | ✅ |
| cn_indpro_wb | Industrial production index | industrial | A | world_bank | NV.IND.TOTL.ZS/CN | backlog | ⚠️ annual |
| cn_fdi_wb | FDI net inflows | external | A | world_bank | BX.KLT.DINV.WD.GD.ZS/CN | backlog | ✅ |

---

## Shortlist — другие страны G20+ — 24 показателя

По **4 ключевым метрикам** на страну: GDP growth, inflation, unemployment, current account.

| country | id prefix | GDP (WB) | CPI (WB) | Unemp (WB) | CA (IMF) | ETL |
|---------|-----------|----------|----------|------------|----------|-----|
| GB | `gb_` | NY.GDP.MKTP.KD.ZG/GB | FP.CPI.TOTL.ZG/GB | SL.UEM.TOTL.ZS/GB | BCA_NGDPD/GBR | backlog |
| DE | `de_` | …/DE | …/DE | …/DE | BCA_NGDPD/DEU | backlog |
| JP | `jp_` | …/JP | …/JP | …/JP | BCA_NGDPD/JPN | backlog |
| IN | `in_` | …/IN | …/IN | …/IN | BCA_NGDPD/IND | backlog |
| BR | `br_` | …/BR | …/BR | …/BR | BCA_NGDPD/BRA | backlog |
| TR | `tr_` | …/TR | …/TR | …/TR | BCA_NGDPD/TUR | backlog |

**6 стран × 4 метрики = 24 id** (например `jp_gdp_yoy_wb`, `jp_cpi_wb`, `jp_unemp_wb`, `jp_ca_imf`).

---

## Shortlist — глобальные / `world` — 18 показателей

| id | name_ru | cat | freq | source | external_id | ETL | 5y |
|----|---------|-----|------|--------|-------------|-----|-----|
| oil_brent | Brent crude | commodities | D | fred | DCOILBRENTEU | done | ✅ |
| oil_wti | WTI crude | commodities | D | fred | DCOILWTICO | backlog | ✅ |
| gold_spot | Gold (London fix) | commodities | D | fred | GOLDAMGBD228NLBM | backlog | ✅ |
| copper_price | Global copper price | commodities | M | wb | PCOPP/TBD | backlog | ⚠️ |
| usd_index_dxy | USD broad index | fx | D | fred | DTWEXBGS | next | ✅ |
| eurusd | EUR/USD | fx | D | fred | DEXUSEUS | next | ✅ |
| usdjpy | USD/JPY | fx | D | fred | DEXJPUS | backlog | ✅ |
| usdcny | USD/CNY | fx | D | fred | DEXCHUS | backlog | ✅ |
| global_gdp_imf | World GDP growth | gdp | A | imf | NGDP_RPCH/WEO/WLD | backlog | ✅ |
| global_cpi_imf | World inflation | inflation | A | imf | PCPIPCH/WEO/WLD | backlog | ✅ |
| oecd_cli_us | OECD CLI USA | leading | M | oecd | USA.M.LI... | backlog | ✅ |
| oecd_cli_cn | OECD CLI China | leading | M | oecd | CHN.M.LI... | backlog | ✅ |
| imf_oil_terms | Terms of trade | external | A | imf | TTT/* | backlog | ✅ |
| wb_global_trade | World trade volume | external | A | wb | NE.RSB.GNFS.KD | backlog | ⚠️ |
| moex_brent_fut | Brent futures (MOEX) | commodities | D | moex | TBD | backlog | ⚠️ |
| sp500 | S&P 500 | equities | D | fred | SP500 | next | ✅ |
| nasdaq | NASDAQ Composite | equities | D | fred | NASDAQCOM | backlog | ✅ |
| vix | VIX volatility | equities | D | fred | VIXCLS | backlog | ✅ |

---

## Shortlist — IMF fiscal / external (multicountry шаблон) — 12 показателей

Шаблон `{metric}_{country}_imf` — для RU, US, CN, DE, EU уже в секциях выше; здесь **доп. метрики**:

| id template | name_ru | cat | freq | imf code |
|-------------|---------|-----|------|----------|
| `{cc}_debt_imf` | Govt gross debt % GDP | fiscal | A | GGXWDG_NGDP |
| `{cc}_fiscal_balance_imf` | Fiscal balance % GDP | fiscal | A | GGXCNL_NGDP |
| `{cc}_reserves_imf` | Reserves / ARA metric | external | A | Reserves_ARA |
| `{cc}_eer_imf` | Real effective exchange rate | fx | A | EREER |

**Рекомендуемые country codes IMF:** RUS, USA, CHN, DEU, EA019, GBR, JPN, IND, BRA, TUR (10 × 4 = 40, частично пересекается с блоками выше — при имплементации dedupe).

---

## Сводка shortlist

| Блок | Кол-во |
|------|--------|
| done | 15 |
| RU backlog | 28 − 6 done = **22** |
| US backlog | 32 − 4 done = **28** |
| EU backlog | 24 − 4 done = **20** |
| CN backlog | 12 − 1 done = **11** |
| G20 other | **24** |
| World | 18 − 1 done = **17** |
| IMF fiscal template | **12** (unique additions) |
| **Итого planned (backlog)** | **~134** |
| **Итого с done** | **~149** (+ резерв до 200 во W5) |

---

## Приоритет волн ETL

| Волна | Фокус | ~N |
|-------|-------|-----|
| **W1** (next) | RU retail/unemp/GDP fedstat; MOEX RGBI/RTSI; ECB MRO; US core CPI, 10Y | ~15 |
| **W2** | EUR unemployment, GDP, industrial; US labor block; CN WB/IMF inflation | ~25 |
| **W3** | G20×4 WB/IMF; EU country HICP; MOEX FX TOM | ~40 |
| **W4** | World commodities/FX; OECD CLI; IMF fiscal/reserves | ~35 |
| **W5** | Остальной backlog + fedstat wages, CBR M2/reserves | ~45 |

---

## Технические заметки для имплементации

1. **fedstat:** один показатель = `indicator_id` + `series_key` (dimensions) + multi-year POST.
2. **Eurostat:** только narrow SDMX keys; не тянуть unfiltered dataset.
3. **FRED:** transforms в `fred/transforms.py` (`yoy_percent`, `mom_diff`, `direct`).
4. **IMF / WB:** `{code}/{ISO3}`; annual → `observed_at = YYYY-01-01`.
5. **MOEX:** pagination `start=0,100,200…`; history с `from=YYYY-MM-DD`.
6. **Compare presets:** обновлять `compare_presets.py` при добавлении flagship rows.

---

## Связанные документы

- `docs/PROJECT_CONTEXT.md` — продукт и источники
- `BACKLOG.md` — engineering gaps
- `backend/app/bootstrap/indicator_seed.py` — seed реальных показателей

**Обновлять этот файл** при закрытии ETL-пункта: `ETL: done`, дата, commit.
