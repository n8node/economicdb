from app.ai.facts import FactsJSON, KPIFact, _numbers_from_text
from app.ai.validator import DigestValidator


def test_validator_accepts_numbers_from_facts():
    facts = FactsJSON(
        period_start=__import__("datetime").date(2026, 6, 15),
        period_end=__import__("datetime").date(2026, 6, 21),
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
            )
        ],
    )
    facts.citation_keys["cbr_key_rate"] = __import__("app.ai.facts", fromlist=["CitationFact"]).CitationFact(
        key="cbr_key_rate",
        indicator_id="cbr_key_rate",
        label="Ключевая ставка ЦБ",
        value="21,00%",
        change="+1,00 п.п.",
        source="Банк России",
        country="ru",
    )

    draft = {
        "headline": "Ставка ЦБ на уровне 21,00%",
        "executive_summary": "Ключевая ставка составляет 21,00%.",
        "sections": {
            "russia": {
                "headline": "Россия",
                "bullets": ["Ставка 21,00%"],
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


def test_validator_rejects_unknown_number():
    facts = FactsJSON(
        period_start=__import__("datetime").date(2026, 6, 15),
        period_end=__import__("datetime").date(2026, 6, 21),
        period_label="15–21 июня 2026",
    )
    draft = {
        "headline": "Инфляция 99,9%",
        "executive_summary": "",
        "sections": {},
        "citation_keys": [],
    }
    result = DigestValidator().validate(draft, facts)
    assert result.ok is False


def test_numbers_from_text_parses_russian_decimal():
    values = _numbers_from_text("Ставка 21,00% и изменение +1,00 п.п.")
    assert 21.0 in values
    assert 1.0 in values
