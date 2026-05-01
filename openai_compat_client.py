from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

import requests

import config


def _read_auth_json_key() -> str:
    auth_path = Path.home() / ".codex" / "auth.json"
    if not auth_path.exists():
        return ""
    try:
        data = json.loads(auth_path.read_text(encoding="utf-8"))
        return str(data.get("OPENAI_API_KEY", "")).strip()
    except Exception:
        return ""


def get_openai_api_key() -> str:
    for candidate in (
        getattr(config, "OPENAI_API_KEY", ""),
        os.getenv("OPENAI_API_KEY", ""),
        _read_auth_json_key(),
    ):
        if candidate:
            return candidate
    return ""


def _extract_text(payload: Dict[str, Any]) -> str:
    if isinstance(payload.get("output_text"), str) and payload["output_text"].strip():
        return payload["output_text"].strip()

    output = payload.get("output", [])
    chunks: list[str] = []
    for item in output:
        for content in item.get("content", []):
            if content.get("type") in {"output_text", "text"} and content.get("text"):
                chunks.append(content["text"])
    return "\n".join(chunks).strip()


def _extract_json_object(text: str) -> Optional[Dict[str, Any]]:
    text = text.strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except Exception:
        pass

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    try:
        return json.loads(text[start : end + 1])
    except Exception:
        return None


def call_openai_responses(
    *,
    system_prompt: str,
    user_prompt: str,
    timeout: int = 30,
) -> Optional[Dict[str, Any]]:
    api_key = get_openai_api_key()
    base_url = (getattr(config, "OPENAI_BASE_URL", "") or "").rstrip("/")
    model = getattr(config, "OPENAI_MODEL", "") or "gpt-5.4"
    if not api_key or not base_url or not model:
        return None

    url = f"{base_url}/v1/responses"
    payload = {
        "model": model,
        "input": [
            {
                "role": "system",
                "content": [{"type": "input_text", "text": system_prompt}],
            },
            {
                "role": "user",
                "content": [{"type": "input_text", "text": user_prompt}],
            },
        ],
        "text": {"format": {"type": "json_object"}},
        "reasoning": {"effort": getattr(config, "OPENAI_REASONING_EFFORT", "medium")},
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        resp = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=timeout,
            proxies={"http": config.HTTP_PROXY, "https": config.HTTPS_PROXY},
        )
        if resp.status_code != 200:
            return None
        data = resp.json()
        text = _extract_text(data)
        return _extract_json_object(text)
    except Exception:
        return None
