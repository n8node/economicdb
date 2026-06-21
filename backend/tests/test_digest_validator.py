from datetime import date

from app.ai.facts import CitationFact, FactsJSON, KPIFact
from app.ai.fallback_digest import build_fallback_digest
from app.ai.numeric_utils import matches_allowed_number, numbers_from_text
from app.ai.validator import DigestValidator


def test_validator_accepts_numbers_from_facts():
    facts = FactsJSON(
        period_start=date(2026, 6, 15),
        period_end=date(2026, 6, 21),
        period_label="15–21 июня 2026",
        kpis=[
            KPIFact(
                indicator_id="cbr_key_rate",
                label="Ключевая ставка ЦБ",
                country="ru",
                category="rates",
                value="21,00%",
                change="+1,00 п.п.",
                source="Банк России",
                updated_at=None,
                citation_key="cbr_key_rate",
                raw_value=21.0,
                raw_change=1.0,
            )
        ],
    )
    facts.citation_keys["cbr_key_rate"] = CitationFact(
        key="cbr_key_rate",
        indicator_id="cbr_key_rate",
        label="Ключевая ставка ЦБ",
        value="21,00%",
        change="+1,00 п.п.",
        source="Банк России",
        country="ru",
    )

    draft = {
        "headline": "Ставка ЦБ на уровне 21%",
        "executive_summary": "Ключевая ставка составляет 21%.",
        "sections": {
            "russia": {
                "headline": "Россия",
                "bullets": ["Ставка 21%"],
                "citation_keys": ["cbr_key_rate"],
            },
            "usa": {"headline": "США", "bullets": ["Без изменений"], "citation_keys": []},
            "eurozone": {"headline": "EU", "bullets": ["Без изменений"], "citation_keys": []},
            "markets_fx": {"headline": "FX", "bullets": ["Без изменений"], "citation_keys": []},
            "next_week": {"headline": "Далее", "bullets": ["Календарь"], "citation_keys": []},
            "risks": {"headline": "Риски", "bullets": ["Геополитика"], "citation_keys": []},
        },
        "citation_keys": ["cbr_key_rate"],
    }

    result = DigestValidator().validate(draft, facts)
    assert result.ok is True


def test_validator_allows_period_day_numbers():
    facts = FactsJSON(
        period_start=date(2026, 6, 15),
        period_end=date(2026, 6, 21),
        period_label="15–21 июня 2026",
    )
    draft = {
        "headline": "Обзор за 15–21 июня 2026",
        "executive_summary": "",
        "sections": {},
        "citation_keys": [],
    }
    result = DigestValidator().validate(draft, facts)
    assert result.ok is True


def test_validator_rejects_unknown_citation():
    facts = FactsJSON(
        period_start=date(2026, 6, 15),
        period_end=date(2026, 6, 21),
        period_label="15–21 июня 2026",
    )
    draft = {
        "headline": "Обзор",
        "executive_summary": "",
        "sections": {
            "russia": {
                "headline": "RU",
                "bullets": ["Ставка"],
                "citation_keys": ["missing_indicator"],
            }
        },
        "citation_keys": ["missing_indicator"],
    }
    result = DigestValidator().validate(draft, facts)
    assert result.ok is False


def test_validator_warns_but_accepts_distant_number():
    facts = FactsJSON(
        period_start=date(2026, 6, 15),
        period_end=date(2026, 6, 21),
        period_label="15–21 июня 2026",
    )
    draft = {
        "headline": "Инфляция 99,9%",
        "executive_summary": "",
        "sections": {},
        "citation_keys": [],
    }
    result = DigestValidator().validate(draft, facts)
    assert result.ok is True
    assert result.warnings


def test_numbers_from_text_parses_russian_decimal():
    values = numbers_from_text("Ставка 21,00% и изменение +1,00 п.п.")
    assert 21.0 in values
    assert 1.0 in values


def test_matches_allowed_with_raw_variants():
    allowed = {21.0, 4.28, 86.45}
    assert matches_allowed_number(21.0, allowed)
    assert matches_allowed_number(4.3, allowed)


def test_fallback_digest_passes_validation():
    facts = FactsJSON(
        period_start=date(2026, 6, 15),
        period_end=date(2026, 6, 21),
        period_label="15–21 июня 2026",
        kpis=[
            KPIFact(
                indicator_id="cbr_key_rate",
                label="Ключевая ставка ЦБ",
                country="ru",
                category="rates",
                value="21,00%",
                change="+1,00 п.п.",
                source="Банк России",
                updated_at=None,
                citation_key="cbr_key_rate",
                raw_value=21.0,
                raw_change=1.0,
            )
        ],
    )
    facts.citation_keys["cbr_key_rate"] = CitationFact(
        key="cbr_key_rate",
        indicator_id="cbr_key_rate",
        label="Ключевая ставка ЦБ",
        value="21,00%",
        change="+1,00 п.п.",
        source="Банк России",
        country="ru",
    )
    draft = build_fallback_digest(facts)
    result = DigestValidator().validate(draft, facts)
    assert result.ok is True
