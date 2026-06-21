from __future__ import annotations

import structlog
from datetime import date
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.digest_schema import SECTION_STORAGE_KEYS
from app.ai.facts import FactsJSON, build_summary_id, build_weekly_facts, resolve_digest_period
from app.ai.openrouter import generate_weekly_digest
from app.ai.validator import DigestValidator
from app.models.ai_usage import AiUsageLog
from app.models.summaries import WeeklySummary
from app.services.settings_service import (
    OPENROUTER_MODEL_DIGEST,
    OPENROUTER_MODEL_FALLBACK,
    get_openrouter_api_key,
    get_openrouter_base_url,
    get_setting,
)

logger = structlog.get_logger()
validator = DigestValidator()


async def _log_usage(
    session: AsyncSession,
    *,
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
) -> None:
    session.add(
        AiUsageLog(
            feature="weekly_digest",
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost_kopecks=None,
        )
    )


def _flatten_section(section: dict) -> str:
    headline = section.get("headline")
    bullets = section.get("bullets") or []
    parts: list[str] = []
    if isinstance(headline, str) and headline.strip():
        parts.append(headline.strip())
    if isinstance(bullets, list):
        for bullet in bullets:
            if isinstance(bullet, str) and bullet.strip():
                parts.append(f"• {bullet.strip()}")
    return "\n\n".join(parts)


def _draft_to_storage(draft: dict, facts: FactsJSON) -> tuple[str, dict[str, str], dict[str, dict], list[str], int]:
    sections_raw = draft.get("sections")
    if not isinstance(sections_raw, dict):
        raise ValueError("invalid_sections")

    sections: dict[str, str] = {}
    for source_key, storage_key in SECTION_STORAGE_KEYS.items():
        section = sections_raw.get(source_key)
        if isinstance(section, dict):
            text = _flatten_section(section)
            if text:
                sections[storage_key] = text

    citations = {
        key: {
            "label": item.label,
            "value": item.value,
            "source": item.source,
            "indicator_id": item.indicator_id,
        }
        for key, item in facts.citation_keys.items()
    }

    headline = str(draft.get("headline") or "").strip()
    if not headline:
        raise ValueError("missing_headline")

    word_count = len(" ".join([headline, *sections.values()]).split())
    tags = sorted({kpi.country for kpi in facts.kpis if kpi.country in {"ru", "us", "eu"}})
    return headline, sections, citations, tags, word_count


async def generate_and_store_weekly_digest(
    session: AsyncSession,
    *,
    period_start: date | None = None,
    period_end: date | None = None,
    force: bool = False,
) -> dict:
    api_key = await get_openrouter_api_key(session)
    if not api_key:
        return {"ok": False, "error": "missing_api_key", "message": "OpenRouter API key не настроен"}

    model_digest = await get_setting(session, OPENROUTER_MODEL_DIGEST)
    if not model_digest:
        return {"ok": False, "error": "missing_model", "message": "Модель для сводки не выбрана в админке"}

    base_url = await get_openrouter_base_url(session)
    model_fallback = await get_setting(session, OPENROUTER_MODEL_FALLBACK)

    if period_start is None or period_end is None:
        period_start, period_end, period_label = resolve_digest_period()
    else:
        from app.ai.facts import _format_period_label

        period_label = _format_period_label(period_start, period_end)

    summary_id = build_summary_id(period_end)
    existing = await session.get(WeeklySummary, summary_id)
    if existing and existing.status == "published" and not force:
        return {
            "ok": True,
            "skipped": True,
            "summary_id": summary_id,
            "message": "Сводка за период уже опубликована",
        }

    facts = await build_weekly_facts(session, period_start=period_start, period_end=period_end)
    if len(facts.kpis) < 3:
        return {
            "ok": False,
            "error": "insufficient_data",
            "message": "Недостаточно показателей в БД для генерации сводки",
        }

    models_to_try = [model_digest]
    if model_fallback and model_fallback != model_digest:
        models_to_try.append(model_fallback)

    last_error = "validation_failed"
    for attempt, model in enumerate(models_to_try, start=1):
        try:
            completion = await generate_weekly_digest(
                api_key=api_key,
                base_url=base_url,
                model=model,
                facts=facts,
            )
        except Exception as exc:
            logger.exception("digest_generation_failed", model=model, attempt=attempt)
            last_error = str(exc)
            continue

        await _log_usage(
            session,
            model=completion.model,
            prompt_tokens=completion.prompt_tokens,
            completion_tokens=completion.completion_tokens,
        )

        validation = validator.validate(completion.content, facts)
        if not validation.ok:
            logger.warning(
                "digest_validation_failed",
                model=model,
                attempt=attempt,
                message=validation.message,
            )
            last_error = validation.message or "validation_failed"
            continue

        headline, sections, citations, tags, word_count = _draft_to_storage(completion.content, facts)
        executive = completion.content.get("executive_summary")
        if isinstance(executive, str) and executive.strip():
            sections = {"intro": executive.strip(), **sections}
        source_count = len({kpi.source for kpi in facts.kpis})

        if existing is None:
            existing = WeeklySummary(
                id=summary_id,
                period_start=period_start,
                period_end=period_end,
                period_label=period_label,
                headline=headline,
                sections=sections,
                citations=citations,
                tags=tags,
                word_count=word_count,
                source_count=source_count,
                status="published",
            )
            session.add(existing)
        else:
            existing.period_start = period_start
            existing.period_end = period_end
            existing.period_label = period_label
            existing.headline = headline
            existing.sections = sections
            existing.citations = citations
            existing.tags = tags
            existing.word_count = word_count
            existing.source_count = source_count
            existing.status = "published"

        await session.commit()
        logger.info("digest_published", summary_id=summary_id, model=completion.model, kpis=len(facts.kpis))
        return {
            "ok": True,
            "summary_id": summary_id,
            "model": completion.model,
            "message": f"Сводка опубликована: {period_label}",
            "word_count": word_count,
        }

    return {"ok": False, "error": "generation_failed", "message": last_error}


async def has_published_summaries(session: AsyncSession) -> bool:
    count = await session.scalar(
        select(func.count()).select_from(WeeklySummary).where(WeeklySummary.status == "published")
    )
    return int(count or 0) > 0
