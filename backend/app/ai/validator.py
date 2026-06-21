from __future__ import annotations

from dataclasses import dataclass, field

from app.ai.facts import FactsJSON
from app.ai.numeric_utils import matches_allowed_number, numbers_from_text


@dataclass
class ValidationResult:
    ok: bool
    invalid_numbers: set[float] = field(default_factory=set)
    missing_citations: set[str] = field(default_factory=set)
    warnings: list[str] = field(default_factory=list)
    message: str | None = None


class DigestValidator:
    """Relaxed facts-first validation.

    Hard-fail only on unknown citation keys.
    Numbers use expanded facts variants, calendar whitelist and fuzzy matching.
    Residual unknown numbers become warnings, not blockers.
    """

    def validate(self, draft: dict, facts: FactsJSON) -> ValidationResult:
        allowed = facts.all_numeric_values()
        text = _collect_text(draft)
        found = numbers_from_text(text)
        invalid = {value for value in found if not matches_allowed_number(value, allowed)}

        draft_keys = set(_collect_citation_keys(draft))
        missing = {key for key in draft_keys if key not in facts.citation_keys}
        if missing:
            return ValidationResult(
                ok=False,
                missing_citations=missing,
                invalid_numbers=invalid,
                message=f"Неизвестные citation_keys: {sorted(missing)[:5]}",
            )

        warnings: list[str] = []
        if invalid:
            warnings.append(
                f"Числа без точного совпадения в facts: {sorted(invalid)[:8]}"
            )

        return ValidationResult(
            ok=True,
            invalid_numbers=invalid,
            warnings=warnings,
            message=None if not warnings else warnings[0],
        )


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
