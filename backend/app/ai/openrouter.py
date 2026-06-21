from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import httpx

from app.ai.digest_schema import DEFAULT_SYSTEM_PROMPT, DIGEST_JSON_SCHEMA
from app.ai.facts import FactsJSON

DEFAULT_HEADERS = {
    "HTTP-Referer": "https://economicdb.com",
    "X-Title": "EconomicDB",
}


@dataclass
class OpenRouterCompletion:
    model: str
    content: dict[str, Any]
    prompt_tokens: int
    completion_tokens: int
    raw: dict[str, Any]


async def fetch_openrouter_models(api_key: str, base_url: str) -> list[dict[str, Any]]:
    url = f"{base_url.rstrip('/')}/models"
    headers = {
        **DEFAULT_HEADERS,
        "Authorization": f"Bearer {api_key}",
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        payload = response.json()

    data = payload.get("data")
    if not isinstance(data, list):
        raise ValueError("invalid_models_response")

    models: list[dict[str, Any]] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        model_id = item.get("id")
        if not isinstance(model_id, str) or not model_id.strip():
            continue
        models.append(
            {
                "id": model_id,
                "name": item.get("name") if isinstance(item.get("name"), str) else model_id,
            }
        )
    models.sort(key=lambda row: row["id"])
    return models


async def test_openrouter_connection(api_key: str, base_url: str) -> dict[str, Any]:
    try:
        models = await fetch_openrouter_models(api_key, base_url)
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code in {401, 403}:
            return {
                "ok": False,
                "error": "invalid_api_key",
                "message": "Неверный API key или доступ запрещён",
            }
        return {
            "ok": False,
            "error": "http_error",
            "message": f"OpenRouter вернул HTTP {exc.response.status_code}",
        }
    except httpx.RequestError:
        return {
            "ok": False,
            "error": "network_error",
            "message": "Не удалось подключиться к OpenRouter",
        }
    except ValueError:
        return {
            "ok": False,
            "error": "invalid_response",
            "message": "Некорректный ответ OpenRouter",
        }

    return {
        "ok": True,
        "message": f"Подключение успешно, доступно моделей: {len(models)}",
        "models_count": len(models),
    }


async def generate_weekly_digest(
    *,
    api_key: str,
    base_url: str,
    model: str,
    facts: FactsJSON,
    system_prompt: str | None = None,
) -> OpenRouterCompletion:
    url = f"{base_url.rstrip('/')}/chat/completions"
    headers = {
        **DEFAULT_HEADERS,
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "temperature": 0.3,
        "messages": [
            {"role": "system", "content": system_prompt or DEFAULT_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    "Подготовь еженедельную AI-сводку по Facts JSON. "
                    "Верни JSON по схеме.\n\n"
                    f"{json.dumps(facts.to_prompt_dict(), ensure_ascii=False, indent=2)}"
                ),
            },
        ],
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "weekly_digest",
                "strict": True,
                "schema": DIGEST_JSON_SCHEMA,
            },
        },
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()

    choice = (data.get("choices") or [{}])[0]
    message = choice.get("message") or {}
    content_raw = message.get("content")
    if not isinstance(content_raw, str):
        raise ValueError("empty_completion")

    content = json.loads(content_raw)
    if not isinstance(content, dict):
        raise ValueError("invalid_completion_json")

    usage = data.get("usage") or {}
    return OpenRouterCompletion(
        model=str(data.get("model") or model),
        content=content,
        prompt_tokens=int(usage.get("prompt_tokens") or 0),
        completion_tokens=int(usage.get("completion_tokens") or 0),
        raw=data,
    )
