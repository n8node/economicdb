from __future__ import annotations

SECTION_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "headline": {"type": "string"},
        "bullets": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 1,
            "maxItems": 4,
        },
        "citation_keys": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
    "required": ["headline", "bullets", "citation_keys"],
}

DIGEST_JSON_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "headline": {"type": "string"},
        "executive_summary": {"type": "string"},
        "sections": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "russia": SECTION_SCHEMA,
                "usa": SECTION_SCHEMA,
                "eurozone": SECTION_SCHEMA,
                "markets_fx": SECTION_SCHEMA,
                "next_week": SECTION_SCHEMA,
                "risks": SECTION_SCHEMA,
            },
            "required": ["russia", "usa", "eurozone", "markets_fx", "next_week", "risks"],
        },
        "citation_keys": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
    "required": ["headline", "executive_summary", "sections", "citation_keys"],
}

SECTION_STORAGE_KEYS = {
    "russia": "ru",
    "usa": "us",
    "eurozone": "eu",
    "markets_fx": "fx",
    "next_week": "next_week",
    "risks": "risks",
}

DEFAULT_SYSTEM_PROMPT = """Ты — редактор макроэкономической аналитики EconomicDB.
Пиши только на русском языке.
Используй ТОЛЬКО числа и факты из переданного Facts JSON.
Не выдумывай показатели, прогнозы и события.
Каждая секция — краткий аналитический обзор недели.
В citation_keys указывай только ключи из facts.citation_keys.
Не упоминай OpenRouter, Anthropic, OpenAI или других провайдеров LLM."""
