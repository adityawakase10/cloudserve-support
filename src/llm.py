# Drafted with Claude (Anthropic), reviewed and modified by Aditya Wakase
"""Model provider client (Groq, OpenAI-compatible API).

Built for a free tier that throttles (A11):
- caches every response on disk: re-runs cost zero tokens and are reproducible
- paces itself to stay under the tokens-per-minute limit
- retries 429 / 5xx / timeouts with exponential backoff, honouring Retry-After
- circuit breaker: after repeated failures it stops calling for a while, so an
  outage turns into fast escalations instead of a run that hangs for hours
"""
import hashlib
import json
import time
from collections import deque

import requests


class ProviderError(Exception):
    """The model provider could not give us an answer."""


class LLMClient:
    def __init__(self, settings):
        self.s = settings
        self.cache_dir = settings.storage_dir / "llm_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._window = deque()            # (timestamp, tokens) for the last 60 seconds
        self._consecutive_failures = 0
        self._circuit_open_until = 0.0
        self.extra_params = {"reasoning_effort": "low"}   # gpt-oss: spend fewer tokens thinking

    # ---------------------------------------------------------------- cache
    def _key(self, messages) -> str:
        raw = json.dumps({"model": self.s.model_name, "messages": messages}, sort_keys=True)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def _cache_get(self, key):
        f = self.cache_dir / f"{key}.json"
        return json.loads(f.read_text(encoding="utf-8")) if f.exists() else None

    def _cache_put(self, key, value):
        (self.cache_dir / f"{key}.json").write_text(json.dumps(value), encoding="utf-8")

    # --------------------------------------------------------- rate pacing
    def _tokens_last_minute(self) -> int:
        now = time.time()
        while self._window and now - self._window[0][0] > 60:
            self._window.popleft()
        return sum(t for _, t in self._window)

    def _pace(self, expected_tokens: int):
        budget = int(self.s.llm_tokens_per_minute * 0.9)
        while self._window and self._tokens_last_minute() + expected_tokens > budget:
            wait = 60 - (time.time() - self._window[0][0]) + 0.5
            time.sleep(max(0.5, min(wait, 60)))

    # ---------------------------------------------------------------- call
    def complete(self, messages, expected_tokens: int = 2000) -> dict:
        """Returns {"content": str, "tokens": int, "cached": bool}. Raises ProviderError."""
        key = self._key(messages)
        cached = self._cache_get(key) if self.s.llm_cache_enabled else None
        if cached:
            return {**cached, "cached": True, "tokens": 0}

        if time.time() < self._circuit_open_until:
            raise ProviderError("provider marked unavailable (circuit breaker open)")
        if not self.s.groq_api_key:
            raise ProviderError("GROQ_API_KEY is not set")

        last_error = "unknown error"
        for attempt in range(self.s.llm_max_retries + 1):
            self._pace(expected_tokens)
            try:
                payload = {"model": self.s.model_name, "messages": messages,
                           "temperature": 0, **self.extra_params}
                r = requests.post(self.s.llm_base_url, json=payload, timeout=self.s.llm_timeout_s,
                                  headers={"Authorization": f"Bearer {self.s.groq_api_key}"})
                if r.status_code == 400 and self.extra_params:
                    self.extra_params = {}            # model may not support the extra option
                    last_error = f"400: {r.text[:200]}"
                    continue
                if r.status_code == 429 or r.status_code >= 500:
                    retry_after = float(r.headers.get("retry-after", 0) or 0)
                    last_error = f"{r.status_code}: {r.text[:200]}"
                    time.sleep(max(retry_after, min(2 ** attempt, 30)))
                    continue
                if r.status_code != 200:
                    raise ProviderError(f"{r.status_code}: {r.text[:300]}")
                data = r.json()
                content = data["choices"][0]["message"].get("content") or ""
                tokens = int(data.get("usage", {}).get("total_tokens", expected_tokens))
                self._window.append((time.time(), tokens))
                self._consecutive_failures = 0
                result = {"content": content, "tokens": tokens}
                self._cache_put(key, result)
                return {**result, "cached": False}
            except (requests.Timeout, requests.ConnectionError) as exc:
                last_error = f"{type(exc).__name__}: {exc}"
                time.sleep(min(2 ** attempt, 30))

        self._consecutive_failures += 1
        if self._consecutive_failures >= 3:
            self._circuit_open_until = time.time() + 120      # stop hammering a dead provider
        raise ProviderError(f"gave up after retries: {last_error}")
