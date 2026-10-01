"""Model layer: one OpenAI-compatible chat call, constrained to the catalog.

Defaults point at a local Ollama server. Any OpenAI-compatible endpoint works by
setting LS_LLM_BASE_URL, LS_LLM_MODEL and (if needed) LS_LLM_API_KEY, so the
self-hosted and the commercial model sit behind the same interface.
"""

import json
import os
import urllib.request

from .catalog import BY_ID, CATALOG, UNKNOWN

BASE_URL = os.environ.get("LS_LLM_BASE_URL", "http://localhost:11434/v1")
MODEL = os.environ.get("LS_LLM_MODEL", "qwen2.5:3b")
API_KEY = os.environ.get("LS_LLM_API_KEY", "ollama")

_CATALOG_TEXT = "\n".join(f"{p.id}: {p.vendor} {p.name}" for p in CATALOG)

SYSTEM = f"""You map one line from a software reseller invoice to a product in a fixed catalog.

Catalog (id: vendor product):
{_CATALOG_TEXT}

Rules:
- Answer with the id of the product the line is a license for.
- Office 365 and Microsoft 365 are different products. So are editions (E1/E3/E5, Standard/Premium/Pro, LT).
- Add-ons, hardware, services, shipping and products not in the catalog are {UNKNOWN}.
- If you are not sure, answer {UNKNOWN}. A wrong id is worse than {UNKNOWN}.
"""

SCHEMA = {
    "type": "object",
    "properties": {"product_id": {"type": "string", "enum": [*BY_ID, UNKNOWN]}},
    "required": ["product_id"],
}


def _post(payload: dict) -> dict:
    req = urllib.request.Request(
        f"{BASE_URL}/chat/completions",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"},
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.load(resp)


def parse(content: str) -> str:
    """Validate the model's answer. Anything outside the catalog becomes UNKNOWN."""
    try:
        pid = json.loads(content).get("product_id")
    except (json.JSONDecodeError, AttributeError):
        return UNKNOWN
    return pid if pid in BY_ID else UNKNOWN


def classify(description: str) -> str:
    body = _post({
        "model": MODEL,
        "temperature": 0,
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": description},
        ],
        "response_format": {
            "type": "json_schema",
            "json_schema": {"name": "product", "schema": SCHEMA},
        },
    })
    return parse(body["choices"][0]["message"]["content"])
