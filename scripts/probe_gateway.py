"""Gateway smoke probe — Phase 0 (plan.md Gate G0).

Verifies the AI Provider Gateway from .env with two bounded calls:
  1. chat completion (Tier 1 path) — must succeed for the platform to run with real AI
  2. embeddings (gateway backend candidate) — decides EMBEDDINGS_BACKEND

Pure text completion only (no tools, per platform law). Single attempt per
endpoint with a 30s timeout (POL-GATE-001 bound); a probe is diagnostic, so
failures print and fall through — they never retry forever.

Run:  .venv\\Scripts\\python scripts\\probe_gateway.py
"""

import os
import sys

from dotenv import load_dotenv
from openai import OpenAI

TIMEOUT_SECONDS = 30  # POL-GATE-001 per-call timeout


def main() -> int:
    load_dotenv()
    base_url = os.environ.get("AI_GATEWAY_BASE_URL")
    api_key = os.environ.get("AI_GATEWAY_API_KEY")
    model = os.environ.get("AI_GATEWAY_MODEL")
    embed_model = os.environ.get("AI_GATEWAY_EMBED_MODEL")

    missing = [
        name
        for name, value in [
            ("AI_GATEWAY_BASE_URL", base_url),
            ("AI_GATEWAY_API_KEY", api_key),
            ("AI_GATEWAY_MODEL", model),
        ]
        if not value
    ]
    if missing:
        print(f"FAIL: missing environment variables: {', '.join(missing)} (fill in .env)")
        return 2

    client = OpenAI(base_url=base_url, api_key=api_key, timeout=TIMEOUT_SECONDS, max_retries=0)

    print(f"Probing gateway at {base_url}")

    chat_ok = False
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Reply with the single word: ok"}],
            max_tokens=5,
        )
        text = (response.choices[0].message.content or "").strip()
        print(f"chat        OK   model={model} reply={text!r}")
        chat_ok = True
    except Exception as exc:  # diagnostic probe: report every failure mode, never retry
        print(f"chat        FAIL {type(exc).__name__}: {exc}")

    embeddings_ok = False
    dimensions = None
    if embed_model:
        try:
            response = client.embeddings.create(model=embed_model, input=["probe"])
            dimensions = len(response.data[0].embedding)
            print(f"embeddings  OK   model={embed_model} dimensions={dimensions}")
            embeddings_ok = True
        except Exception as exc:
            print(f"embeddings  FAIL {type(exc).__name__}: {exc}")
    else:
        print("embeddings  SKIP AI_GATEWAY_EMBED_MODEL not set")

    print()
    if embeddings_ok:
        print("Result: set EMBEDDINGS_BACKEND=gateway")
    else:
        print("Result: set EMBEDDINGS_BACKEND=local (Chroma built-in embedding function)")

    return 0 if chat_ok else 1


if __name__ == "__main__":
    sys.exit(main())
