"use client";

import { AppLink as Link } from "@/components/AppLink";
import { useEffect, useState } from "react";
import { MiniSparkline } from "@/components/indicators/MiniSparkline";
import { fetchIndicatorSeries } from "@/lib/indicators";
import { SECTION_TITLES, fetchSummary, type SummaryDetail } from "@/lib/summaries";

type ParsedSection = {
  key: string;
  title: string;
  lead: string;
  bullets: string[];
};

type Citation = SummaryDetail["citations"][string];

const SECTION_ORDER = ["intro", "ru", "us", "eu", "fx", "next_week", "risks"];

const SECTION_META: Record<string, { icon: string; tone: string; label: string }> = {
  intro: { icon: "ti-sparkles", tone: "teal", label: "Главная мысль" },
  ru: { icon: "ti-building-bank", tone: "blue", label: "Россия" },
  us: { icon: "ti-chart-candle", tone: "violet", label: "США" },
  eu: { icon: "ti-building-community", tone: "green", label: "Еврозона" },
  fx: { icon: "ti-currency-dollar", tone: "amber", label: "Рынки" },
  next_week: { icon: "ti-calendar-event", tone: "blue", label: "Календарь" },
  risks: { icon: "ti-alert-triangle", tone: "red", label: "Риски" },
};

export function SummaryDetailView({ id }: { id: string }) {
  const [data, setData] = useState<SummaryDetail | null>(null);
  const [seriesMap, setSeriesMap] = useState<Record<string, number[]>>({});

  useEffect(() => {
    let cancelled = false;

    async function loadSummary() {
      try {
        const summary = await fetchSummary(id);
        if (cancelled) return;
        setData(summary);

        const indicatorIds = Array.from(
          new Set(
            Object.values(summary.citations)
              .map((citation) => citation.indicator_id)
              .filter((indicatorId): indicatorId is string => Boolean(indicatorId)),
          ),
        ).slice(0, 8);

        const pairs = await Promise.all(
          indicatorIds.map(async (indicatorId) => {
            try {
              const series = await fetchIndicatorSeries(indicatorId);
              return [
                indicatorId,
                series?.points.slice(-28).map((point) => point.value).filter(Number.isFinite) ?? [],
              ] as const;
            } catch {
              return [indicatorId, []] as const;
            }
          }),
        );

        if (!cancelled) {
          setSeriesMap(Object.fromEntries(pairs));
        }
      } catch {
        if (!cancelled) setData(null);
      }
    }

    setData(null);
    setSeriesMap({});
    loadSummary();

    return () => {
      cancelled = true;
    };
  }, [id]);

  if (!data) {
    return (
      <div className="content summaries-page">
        <div className="card card-pad"><p className="meta">Загрузка…</p></div>
      </div>
    );
  }

  const sections = buildSections(data).filter((section) => section.key !== "intro");
  const insightSections = sections.slice(0, 4);
  const metrics = buildMetricCards(data.citations);

  return (
    <div className="content summaries-page summary-detail-page">
      <Link href="/app/summaries" target="_top" className="btn ghost summary-back">
        ← Архив
      </Link>

      <section className="summary-hero">
        <div className="summary-hero-copy">
          <span className="summary-kicker">
            <i className="ti ti-sparkles" />
            AI-сводка недели
          </span>
          <p className="summary-period">{data.period_label} · {data.reading_minutes} мин чтения</p>
          <h1>{data.headline}</h1>
          <div className="summary-hero-actions">
            <Link href="/app/indicators" target="_top" className="btn primary">
              <i className="ti ti-chart-line" />
              Смотреть показатели
            </Link>
            <Link href="/app/calendar" target="_top" className="btn">
              <i className="ti ti-calendar-event" />
              Календарь событий
            </Link>
          </div>
        </div>
      </section>

      {insightSections.length > 0 && (
        <section className="summary-insights" aria-label="Главные мысли">
          {insightSections.map((section) => {
            const meta = getSectionMeta(section.key);
            return (
              <article key={section.key} className={`summary-insight tone-${meta.tone}`}>
                <span className="insight-icon"><i className={`ti ${meta.icon}`} /></span>
                <p className="insight-label">{meta.label}</p>
                <h2>{section.lead || section.title}</h2>
                {section.bullets[0] ? <p>{section.bullets[0]}</p> : null}
              </article>
            );
          })}
        </section>
      )}

      {metrics.length > 0 && (
        <section className="summary-metrics">
          <div className="summary-section-head">
            <p className="section-eyebrow">Показатели выпуска</p>
            <h2>Цифры, на которых построена сводка</h2>
          </div>
          <div className="summary-metric-grid">
            {metrics.map(({ key, citation }) => {
              const values = citation.indicator_id ? seriesMap[citation.indicator_id] || [] : [];
              const trend = getTrend(values);
              return (
                <article key={key} className={`summary-metric-card trend-${trend}`}>
                  <div className="metric-card-top">
                    <span className={`source-tag ${normalizeSource(citation.source)}`}>{citation.source}</span>
                    <span className={`metric-trend trend-${trend}`}>{trendLabel(trend)}</span>
                  </div>
                  <h3>{citation.label}</h3>
                  <p className="metric-value">{citation.value}</p>
                  <div className="metric-spark">
                    <MiniSparkline values={values} width={220} height={52} filled responsive />
                  </div>
                </article>
              );
            })}
          </div>
        </section>
      )}

      <div className="summary-story-layout">
        <main className="summary-story-main">
          {sections.map((section) => {
            const meta = getSectionMeta(section.key);
            return (
              <section id={`summary-${section.key}`} key={section.key} className={`summary-story-card tone-${meta.tone}`}>
                <div className="story-card-head">
                  <span className="story-card-icon"><i className={`ti ${meta.icon}`} /></span>
                  <div>
                    <p className="section-eyebrow">{meta.label}</p>
                    <h2>{section.title}</h2>
                  </div>
                </div>
                {section.lead ? <p className="story-lead">{section.lead}</p> : null}
                {section.bullets.length > 0 ? (
                  <ul className="summary-bullets">
                    {section.bullets.map((bullet) => (
                      <li key={bullet}>{bullet}</li>
                    ))}
                  </ul>
                ) : null}
              </section>
            );
          })}
        </main>

        <aside className="summary-sidebar">
          <div className="summary-sidebar-card">
            <p className="section-eyebrow">Навигация</p>
            <h2>В выпуске</h2>
            <div className="summary-nav-list">
              {sections.map((section) => {
                const meta = getSectionMeta(section.key);
                return (
                  <a key={section.key} href={`#summary-${section.key}`}>
                    <i className={`ti ${meta.icon}`} />
                    {section.title}
                  </a>
                );
              })}
            </div>
          </div>

          {Object.keys(data.citations).length > 0 && (
            <details className="summary-sidebar-card summary-sources" open>
              <summary>Источники</summary>
              <div className="source-list">
                {Object.entries(data.citations).map(([key, citation]) => (
                  <div key={key} className="source-row">
                    <span className={`source-tag ${normalizeSource(citation.source)}`}>{citation.source}</span>
                    <div>
                      <p>{citation.label}</p>
                      <span>{citation.value}</span>
                    </div>
                  </div>
                ))}
              </div>
            </details>
          )}
        </aside>
      </div>

      <p className="ai-disclaimer summary-disclaimer">
        Сгенерировано AI на основе официальных данных. Не является инвестиционной рекомендацией.
      </p>
    </div>
  );
}

function buildSections(data: SummaryDetail): ParsedSection[] {
  const entries = Object.entries(data.sections).sort(([left], [right]) => {
    const leftIndex = SECTION_ORDER.indexOf(left);
    const rightIndex = SECTION_ORDER.indexOf(right);
    return (leftIndex === -1 ? 99 : leftIndex) - (rightIndex === -1 ? 99 : rightIndex);
  });

  return entries.map(([key, text]) => {
    const parts = text
      .split(/\n{1,}|\s+•\s+/)
      .map((part) => part.replace(/^•\s*/, "").trim())
      .filter(Boolean);
    const hasBulletMarker = /(^|\s)•\s+/.test(text);
    const lead = parts[0] || "";
    const bullets = hasBulletMarker ? parts.slice(1) : splitIntoBullets(parts.slice(1).join(" ") || lead);

    return {
      key,
      title: SECTION_TITLES[key] || key,
      lead,
      bullets: bullets.filter((bullet) => bullet !== lead).slice(0, 5),
    };
  });
}

function splitIntoBullets(text: string): string[] {
  return text
    .split(/(?<=[.!?])\s+/)
    .map((part) => part.trim())
    .filter((part) => part.length > 18)
    .slice(0, 4);
}

function buildMetricCards(citations: SummaryDetail["citations"]): Array<{ key: string; citation: Citation }> {
  return Object.entries(citations)
    .filter(([, citation]) => citation.label && citation.value)
    .slice(0, 8)
    .map(([key, citation]) => ({ key, citation }));
}

function getSectionMeta(key: string) {
  return SECTION_META[key] || { icon: "ti-file-text", tone: "teal", label: SECTION_TITLES[key] || key };
}

function getTrend(values: number[]): "up" | "down" | "flat" {
  if (values.length < 2) return "flat";
  const delta = values[values.length - 1] - values[0];
  if (Math.abs(delta) < Number.EPSILON) return "flat";
  return delta > 0 ? "up" : "down";
}

function trendLabel(trend: "up" | "down" | "flat") {
  if (trend === "up") return "рост";
  if (trend === "down") return "снижение";
  return "без тренда";
}

function normalizeSource(source: string) {
  return source.toLowerCase().replace(/[^a-z0-9]+/g, "_");
}
