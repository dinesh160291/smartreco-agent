"""AI Provider Gateway — the single AI boundary (Law 3; docs/core/15/20, Decision #034).

Configured entirely from environment; the codebase names no provider. Every
call is pure text completion or embeddings — no tools, no function-calling.
Bounds per POL-GATE-001 (timeout, capped retries); exhaustion raises
GatewayUnavailable so orchestration fallbacks can engage (fail loud — Core 21).
"""

import os

from openai import OpenAI

from smartreco.policies import PolicyCatalog


class GatewayUnavailable(RuntimeError):
    """Raised when the gateway cannot serve within POL-GATE-001 bounds."""


class AIGateway:
    def __init__(self, policies: PolicyCatalog):
        base_url = os.environ.get("AI_GATEWAY_BASE_URL")
        api_key = os.environ.get("AI_GATEWAY_API_KEY")
        if not base_url or not api_key:
            raise GatewayUnavailable("AI gateway not configured (AI_GATEWAY_BASE_URL/_API_KEY)")
        self.model = os.environ.get("AI_GATEWAY_MODEL", "")
        self.embed_model = os.environ.get("AI_GATEWAY_EMBED_MODEL", "")
        timeout = policies.param("POL-GATE-001", "timeout_seconds")
        retries = policies.param("POL-GATE-001", "max_retries")
        self._client = OpenAI(base_url=base_url, api_key=api_key,
                              timeout=timeout, max_retries=retries)

    def complete(self, prompt: str, max_tokens: int = 1024) -> str:
        """Pure text completion — no tools (Law 2)."""
        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
            )
        except Exception as exc:
            raise GatewayUnavailable(f"chat completion failed: {type(exc).__name__}") from exc
        return response.choices[0].message.content or ""

    def embed(self, texts: list[str]) -> list[list[float]]:
        try:
            response = self._client.embeddings.create(model=self.embed_model, input=texts)
        except Exception as exc:
            raise GatewayUnavailable(f"embeddings failed: {type(exc).__name__}") from exc
        return [item.embedding for item in response.data]
