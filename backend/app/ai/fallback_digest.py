from __future__ import annotations

from app.ai.facts import FactsJSON


def _section_for_country(facts: FactsJSON, countries: set[str]) -> dict:
    bullets: list[str] = []
    keys: list[str] = []
    for kpi in facts.kpis:
        if kpi.country not in countries:
            continue
        line = f"{kpi.label}: {kpi.value}"
        if kpi.change:
            line = f"{line} ({kpi.change})"
        bullets.append(line)
        keys.append(kpi.citation_key)
        if len(bullets) >= 3:
            break
    if not bullets:
        bullets = ["За период нет обновлённых показателей в подключённых источниках."]
    return {
        "headline": bullets[0].split(":")[0] if ":" in bullets[0] else "Обзор",
        "bullets": bullets,
        "citation_keys": keys,
    }


def build_fallback_digest(facts: FactsJSON) -> dict:
    ru = _section_for_country(facts, {"ru"})
    us = _section_for_country(facts, {"us"})
    eu = _section_for_country(facts, {"eu", "world"})
    markets = _section_for_country(facts, {"ru", "world"})

    next_week_bullets = [
        f"{event.scheduled_at}: {event.title} ({event.country.upper()})"
        for event in facts.next_week_events[:4]
    ] or ["Календарь на следующую неделю пока без ключевых событий tier A/B."]

    surprise_bullets = [
        f"{item.title}: факт {item.actual or '—'}, сюрприз {item.surprise or '—'}"
        for item in facts.calendar_surprises[:3]
    ]

    headline_parts = [kpi.label for kpi in facts.kpis[:2]]
    headline = f"Макрообзор {facts.period_label}: {', '.join(headline_parts)}" if headline_parts else f"Макрообзор {facts.period_label}"

    executive = (
        f"Сводка собрана автоматически из официальных рядов за {facts.period_label}. "
        f"В базе {len(facts.kpis)} показателей и {len(facts.calendar_surprises)} событий с surprise."
    )

    all_keys = sorted(facts.citation_keys.keys())

    return {
        "headline": headline[:240],
        "executive_summary": executive,
        "sections": {
            "russia": {
                "headline": "Россия",
                "bullets": ru["bullets"],
                "citation_keys": ru["citation_keys"],
            },
            "usa": {
                "headline": "США",
                "bullets": us["bullets"],
                "citation_keys": us["citation_keys"],
            },
            "eurozone": {
                "headline": "Еврозона",
                "bullets": eu["bullets"],
                "citation_keys": eu["citation_keys"],
            },
            "markets_fx": {
                "headline": "Рынки и FX",
                "bullets": markets["bullets"],
                "citation_keys": markets["citation_keys"],
            },
            "next_week": {
                "headline": "На следующей неделе",
                "bullets": next_week_bullets,
                "citation_keys": [],
            },
            "risks": {
                "headline": "Риски",
                "bullets": surprise_bullets
                or ["Риски оцениваются по волатильности ключевых показателей и календарю релизов."],
                "citation_keys": [],
            },
        },
        "citation_keys": all_keys[:12],
    }
