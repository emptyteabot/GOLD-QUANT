from __future__ import annotations

import json
from typing import Any, Dict, Optional

import requests

import config


def _extract_json(content: str) -> Optional[Dict[str, Any]]:
    text = (content or "").strip()
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


def deepseek_reason_verbose(system_prompt: str, user_prompt: str, timeout: int | None = None) -> Dict[str, Any]:
    api_key = config.DEEPSEEK_API_KEY
    base_url = (config.DEEPSEEK_BASE_URL or "").rstrip("/")
    model = config.DEEPSEEK_MODEL or "deepseek-reasoner"
    if not api_key or not base_url or not model:
        return {
            "ok": False,
            "provider": "deepseek",
            "result": None,
            "status_code": None,
            "error": "deepseek_not_configured",
        }

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.0,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    try:
        resp = requests.post(
            f"{base_url}/chat/completions",
            json=payload,
            headers=headers,
            timeout=timeout or config.DEEPSEEK_TIMEOUT_SEC,
            proxies={"http": config.HTTP_PROXY, "https": config.HTTPS_PROXY},
        )
        if resp.status_code != 200:
            error_message = ""
            try:
                data = resp.json()
                error_payload = data.get("error", {}) if isinstance(data, dict) else {}
                error_message = str(error_payload.get("message") or error_payload.get("code") or "").strip()
            except Exception:
                error_message = resp.text[:400]
            return {
                "ok": False,
                "provider": "deepseek",
                "result": None,
                "status_code": resp.status_code,
                "error": error_message or "deepseek_http_error",
            }
        data = resp.json()
        choices = data.get("choices", [])
        if not choices:
            return {
                "ok": False,
                "provider": "deepseek",
                "result": None,
                "status_code": resp.status_code,
                "error": "deepseek_no_choices",
            }
        content = choices[0].get("message", {}).get("content", "")
        parsed = _extract_json(content)
        if parsed is None:
            return {
                "ok": False,
                "provider": "deepseek",
                "result": None,
                "status_code": resp.status_code,
                "error": "deepseek_invalid_json_response",
            }
        return {
            "ok": True,
            "provider": "deepseek",
            "result": parsed,
            "status_code": resp.status_code,
            "error": None,
        }
    except Exception as exc:
        return {
            "ok": False,
            "provider": "deepseek",
            "result": None,
            "status_code": None,
            "error": f"{type(exc).__name__}: {exc}",
        }


def deepseek_reason(system_prompt: str, user_prompt: str, timeout: int | None = None) -> Optional[Dict[str, Any]]:
    result = deepseek_reason_verbose(system_prompt, user_prompt, timeout)
    return result["result"] if result.get("ok") else None
