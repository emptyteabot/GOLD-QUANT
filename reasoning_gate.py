from __future__ import annotations

from typing import Any, Dict

import config
from deepseek_client import deepseek_reason_verbose
from openai_compat_client import call_openai_responses


def run_reasoning_gate(
    *,
    system_prompt: str,
    user_prompt: str,
    timeout: int | None = None,
) -> Dict[str, Any]:
    provider = getattr(config, "FINAL_REASONER_PROVIDER", "openai_compat")
    effective_timeout = timeout or getattr(config, "FINAL_REASONER_TIMEOUT_SEC", 45)

    if provider in {"openai", "openai_compat"}:
        result = call_openai_responses(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            timeout=effective_timeout,
        )
        if isinstance(result, dict):
            payload = dict(result)
            payload["_meta"] = {
                "provider": "openai_compat",
                "fallback_used": False,
            }
            return payload
        return {
            "_meta": {
                "provider": "none",
                "fallback_used": False,
                "error": "openai_compat_unavailable",
            }
        }

    deepseek = deepseek_reason_verbose(system_prompt, user_prompt, effective_timeout)
    if deepseek.get("ok") and isinstance(deepseek.get("result"), dict):
        result = dict(deepseek["result"])
        result["_meta"] = {
            "provider": "deepseek",
            "fallback_used": False,
            "deepseek_status_code": deepseek.get("status_code"),
        }
        return result

    fallback = call_openai_responses(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        timeout=effective_timeout,
    )
    if isinstance(fallback, dict):
        result = dict(fallback)
        result["_meta"] = {
            "provider": "openai_compat",
            "fallback_used": True,
            "deepseek_status_code": deepseek.get("status_code"),
            "deepseek_error": deepseek.get("error"),
        }
        return result

    return {
        "_meta": {
            "provider": "none",
            "fallback_used": True,
            "deepseek_status_code": deepseek.get("status_code"),
            "deepseek_error": deepseek.get("error"),
            "error": "all_reasoners_unavailable",
        }
    }
