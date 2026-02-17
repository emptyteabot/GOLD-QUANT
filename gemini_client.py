import json
from pathlib import Path
import requests
import config


def _alt_base_urls(base: str) -> list:
    base = base.rstrip('/')
    urls = []
    if base.endswith('/v1beta'):
        urls.append(base)
        urls.append(base[:-6] + '/v1')
    elif base.endswith('/v1'):
        urls.append(base)
        urls.append(base[:-3] + '/v1beta')
    else:
        urls.append(base)
        urls.append(base + '/v1beta')
    return list(dict.fromkeys(urls))


def _normalize_model(model: str) -> str:
    if not model:
        return ''
    if model.startswith('models/'):
        return model
    return f"models/{model}"


def _log_error(status: int, text: str):
    try:
        path = Path(__file__).resolve().parent / '_tmp' / 'gemini_error.log'
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('a', encoding='utf-8') as f:
            f.write(f"status={status}\n")
            f.write(text[:4000] + "\n\n")
    except Exception:
        pass


def gemini_generate(text: str, timeout: int = 30) -> str | None:
    api_key = config.GEMINI_API_KEY
    base_url = config.GEMINI_BASE_URL or ''
    model = _normalize_model(config.GEMINI_MODEL or '')

    if not api_key or not base_url or not model:
        return None

    payload = {
        "systemInstruction": {
            "parts": [
                {"text": "严格按用户格式输出，不要额外解释，不要英文。"}
            ]
        },
        "contents": [
            {"role": "user", "parts": [{"text": text}]}
        ],
        "generationConfig": {
            "maxOutputTokens": 256,
            "temperature": 0.0,
            "topP": 0.2,
            "responseMimeType": "text/plain",
            "candidateCount": 1
        },
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ]
    }

    for base in _alt_base_urls(base_url):
        url = f"{base.rstrip('/')}/{model}:generateContent?key={api_key}"
        try:
            resp = requests.post(url, json=payload, timeout=timeout)
            if resp.status_code != 200:
                _log_error(resp.status_code, resp.text)
                continue
            data = resp.json()
            candidates = data.get('candidates', [])
            if not candidates:
                _log_error(200, resp.text)
                return None
            parts = candidates[0].get('content', {}).get('parts', [])
            if not parts:
                _log_error(200, resp.text)
                return None
            return parts[0].get('text')
        except Exception as e:
            _log_error(0, str(e))
            continue

    return None
