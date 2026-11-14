"""Explicit provider selection shared by CLI and graph discovery."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ModelConfig:
    provider: str
    model: str
    api_key: str = field(repr=False)

    @classmethod
    def from_environment(cls, environment: Mapping[str, str] | None = None) -> ModelConfig:
        values = os.environ if environment is None else environment
        provider = values.get("LLM_PROVIDER", "openai")
        if provider not in {"openai", "ollama"}:
            raise ValueError("LLM_PROVIDER must be openai or ollama")
        model = values.get("LLM_MODEL", "").strip()
        key = values.get("OPENAI_API_KEY", "").strip()
        if provider == "openai" and (not model or not key):
            raise ValueError("--strategy llm requires exported OPENAI_API_KEY and LLM_MODEL")
        if not model:
            raise ValueError("--strategy llm with ollama requires LLM_MODEL")
        return cls(provider, model, "ollama" if provider == "ollama" else key)

    @property
    def api(self) -> str:
        return "chat" if self.provider == "ollama" else "responses"

    def client_options(self) -> dict[str, Any]:
        if self.provider == "ollama":
            return {
                "base_url": "http://127.0.0.1:11434/v1",
                "api_key": self.api_key,
                "timeout": 30,
                "max_retries": 0,
            }
        return {
            "base_url": "https://api.openai.com/v1",
            "api_key": self.api_key,
            "timeout": 10,
            "max_retries": 0,
        }
