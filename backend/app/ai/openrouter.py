from __future__ import annotations

from typing import Any

import httpx

DEFAULT_HEADERS = {
    "HTTP-Referer": "https://economicdb.com",
    "X-Title": "EconomicDB",
}


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
