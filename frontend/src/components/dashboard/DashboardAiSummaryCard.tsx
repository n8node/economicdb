"use client";

import { AppLink as Link } from "@/components/AppLink";
import type { DashboardOverview } from "@/lib/dashboard";

function normalizeBullets(items: string[]): string[] {
  return items
    .flatMap((item) =>
      item
        .split(/\n+|\s+•\s+/)
        .map((part) => part.replace(/^•\s*/, "").trim())
        .filter(Boolean),
    )
    .filter((item, index, all) => all.indexOf(item) === index)
    .slice(0, 3);
}

function highlightFacts(text: string) {
  const pattern = /(\d+[,.]\d+\s*%|USD\s*\/\s*RUB\s*\d+[,.]\d+|\d+[,.]\d+)/gi;
  const parts = text.split(pattern);
  return parts.map((part, index) => {
    if (!part) return null;
    const isFact =
      /^\d+[,.]\d+\s*%$/i.test(part) ||
      /^USD\s*\/\s*RUB\s*\d+[,.]\d+$/i.test(part) ||
      /^\d+[,.]\d+$/i.test(part);
    return isFact ? (
      <span key={`${index}-${part}`} className="ai-fact">
        {part}
      </span>
    ) : (
      part
    );
  });
}

export function DashboardAiSummaryCard({
  summary,
  previous,
}: {
  summary: DashboardOverview["ai_summary"];
  previous: DashboardOverview["previous_ai_summary"];
}) {
  const bullets = normalizeBullets(summary.bullets);
  const summaryHref = summary.summary_id ? `/app/summaries/${summary.summary_id}` : "/app/summaries";
  const previousHref = previous?.summary_id ? `/app/summaries/${previous.summary_id}` : "/app/summaries";

  return (
    <div className="card ai-card card-pad dashboard-ai-card">
      <div className="dashboard-card-head">
        <span className="ai-badge ai-badge-solid">
          <i className="ti ti-sparkles" />
          AI-сводка
        </span>
        <Link href="/app/summaries" target="_top" className="dashboard-card-link">
          Архив сводок <i className="ti ti-chevron-right" />
        </Link>
      </div>

      <div className="ai-digest-meta">
        <span className="ai-digest-label">Еженедельный дайджест</span>
        <span className="ai-period-pill">{summary.period}</span>
      </div>

      <h3 className="ai-headline">{summary.headline}</h3>

      <ol className="ai-bullets ai-bullets-numbered">
        {bullets.map((item) => (
          <li key={item}>{highlightFacts(item)}</li>
        ))}
      </ol>

      <div className="ai-card-footer">
        <Link href={summaryHref} target="_top" className="btn primary ai-read-btn">
          Читать полностью <i className="ti ti-chevron-right" />
        </Link>
        <p className="ai-disclaimer">
          <i className="ti ti-info-circle" />
          Сгенерировано AI · не инвестиционная рекомендация
        </p>
      </div>

      {previous ? (
        <div className="ai-previous-section">
          <div className="ai-previous-block">
            <div className="ai-previous-head">
              <span className="ai-previous-label">Предыдущий период</span>
              <span className="ai-previous-period">{previous.period}</span>
            </div>
            <p className="ai-previous-headline">{previous.headline}</p>
            {previous.bullets[0] ? <p className="ai-previous-teaser">{previous.bullets[0]}</p> : null}
          </div>
          <Link href={previousHref} target="_top" className="btn ai-read-btn ai-read-btn-ghost">
            Читать полностью <i className="ti ti-chevron-right" />
          </Link>
        </div>
      ) : null}
    </div>
  );
}
