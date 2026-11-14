"""Provider selection must never forward a hosted key to local inference."""

import unittest

from packages.discovery.model_config import ModelConfig


class ModelConfigTests(unittest.TestCase):
    def test_local_provider_needs_no_hosted_credential(self):
        config = ModelConfig.from_environment({"LLM_PROVIDER": "ollama", "LLM_MODEL": "qwen2.5:7b"})
        self.assertEqual(config.api, "chat")
        self.assertEqual(config.client_options()["base_url"], "http://127.0.0.1:11434/v1")
        self.assertEqual(config.client_options()["api_key"], "ollama")

    def test_local_provider_discards_hosted_credential_and_endpoint_override(self):
        config = ModelConfig.from_environment(
            {
                "LLM_PROVIDER": "ollama",
                "LLM_MODEL": "local-model",
                "OPENAI_API_KEY": "private-test-value",  # pragma: allowlist secret
                "OPENAI_BASE_URL": "https://example.com",
            }
        )
        self.assertNotIn("private-test-value", repr(config))
        self.assertEqual(config.client_options()["api_key"], "ollama")
        self.assertEqual(config.client_options()["base_url"], "http://127.0.0.1:11434/v1")

    def test_openai_provider_requires_credentials_and_uses_hosted_responses(self):
        with self.assertRaisesRegex(ValueError, "OPENAI_API_KEY and LLM_MODEL"):
            ModelConfig.from_environment({"LLM_MODEL": "gpt-4.1-mini"})
        config = ModelConfig.from_environment(
            {
                "LLM_MODEL": "gpt-4.1-mini",
                "OPENAI_API_KEY": "private-test-value",  # pragma: allowlist secret
            }  # pragma: allowlist secret
        )
        self.assertEqual(config.provider, "openai")
        self.assertEqual(config.api, "responses")
        self.assertEqual(config.client_options()["base_url"], "https://api.openai.com/v1")
        self.assertEqual(config.client_options()["api_key"], "private-test-value")
        self.assertNotIn("private-test-value", repr(config))

    def test_invalid_provider_or_missing_local_model_is_rejected(self):
        for values in ({"LLM_PROVIDER": "unknown"}, {"LLM_PROVIDER": "ollama"}):
            with self.subTest(values=values), self.assertRaises(ValueError):
                ModelConfig.from_environment(values)
