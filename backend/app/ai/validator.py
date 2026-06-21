from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.ai.facts import FactsJSON, _numbers_from_text

NUMBER_PATTERN = re.compile(r"-?\d+[,.]?\d*")


@dataclass
class ValidationResult:
    ok: bool
    invalid_numbers: set[float] = field(default_factory=set)
    missing_citations: set[str] = field(default_factory=set)
    message: str | None = None


class DigestValidator:
    def validate(self, draft: dict, facts: FactsJSON) -> ValidationResult:
        allowed = facts.all_numeric_values()
        text = _collect_text(draft)
        found = _numbers_from_text(text)
        invalid = {value for value in found if not _matches_allowed(value, allowed)}
        if invalid:
            return ValidationResult(
                ok=False,
                invalid_numbers=invalid,
                message=f"Числа вне facts: {sorted(invalid)[:5]}",
            )

        draft_keys = set(_collect_citation_keys(draft))
        missing = {key for key in draft_keys if key not in facts.citation_keys}
        if missing:
            return ValidationResult(
                ok=False,
                missing_citations=missing,
                message=f"Неизвестные citation_keys: {sorted(missing)[:5]}",
            )

        return ValidationResult(ok=True)


def _collect_text(draft: dict) -> str:
    parts: list[str] = []
    for key in ("headline", "executive_summary"):
        value = draft.get(key)
        if isinstance(value, str):
            parts.append(value)
    sections = draft.get("sections")
    if isinstance(sections, dict):
        for section in sections.values():
            if isinstance(section, dict):
                headline = section.get("headline")
                if isinstance(headline, str):
                    parts.append(headline)
                bullets = section.get("bullets")
                if isinstance(bullets, list):
                    parts.extend(str(item) for item in bullets if isinstance(item, str))
    return "\n".join(parts)


def _collect_citation_keys(draft: dict) -> list[str]:
    keys: list[str] = []
    top = draft.get("citation_keys")
    if isinstance(top, list):
        keys.extend(str(item) for item in top if isinstance(item, str))
    sections = draft.get("sections")
    if isinstance(sections, dict):
        for section in sections.values():
            if isinstance(section, dict):
                section_keys = section.get("citation_keys")
                if isinstance(section_keys, list):
                    keys.extend(str(item) for item in section_keys if isinstance(item, str))
    return keys


def _matches_allowed(value: float, allowed: set[float]) -> bool:
    if value in allowed:
        return True
    for candidate in allowed:
        if abs(candidate - value) <= 0.05:
            return True
        if abs(round(candidate) - value) <= 0.01:
            return True
    return False
