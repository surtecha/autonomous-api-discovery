import json
import unittest
from importlib.util import find_spec
from types import SimpleNamespace

from packages.discovery.engine import initialize
from packages.discovery.model import rank


@unittest.skipUnless(find_spec("pydantic"), "Pydantic is required for model-output validation")
class ModelSelectionTests(unittest.TestCase):
    def test_model_receives_no_response_content(self):
        calls = []

        def parse(**kwargs):
            calls.append(kwargs)
            return SimpleNamespace(
                output_parsed=SimpleNamespace(index=0), usage=SimpleNamespace(total_tokens=20)
            )

        client = SimpleNamespace(responses=SimpleNamespace(parse=parse))
        state = initialize("test")
        self.assertEqual(rank(state, "configured-model", client), 0)
        self.assertNotIn("http", str(calls[0]["input"]))
        self.assertNotIn("Authorization", str(calls[0]["input"]))
        self.assertEqual(state.model_usage["tokens"], 20)
        self.assertEqual(state.model_usage["budget_tokens"], 2048)

    def test_local_chat_parses_and_records_token_breakdown(self):
        calls = []

        def parse(**kwargs):
            calls.append(kwargs)
            return SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(parsed=SimpleNamespace(index=0)))],
                usage=SimpleNamespace(total_tokens=25, prompt_tokens=20, completion_tokens=5),
            )

        client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(parse=parse)))
        state = initialize("local-test")
        self.assertEqual(rank(state, "local-model", client, api="chat"), 0)
        self.assertEqual(state.model_usage["input_tokens"], 20)
        self.assertEqual(state.model_usage["output_tokens"], 5)
        self.assertEqual(state.model_usage["parsed_selections"], 1)
        self.assertEqual(state.model_usage["unmeasured_calls"], 0)
        self.assertEqual(calls[0]["temperature"], 0)
        self.assertEqual(calls[0]["max_tokens"], 128)
        self.assertEqual(
            calls[0]["response_format"].model_json_schema()["properties"]["index"]["maximum"], 0
        )
        self.assertNotIn("http", str(calls[0]["messages"]))

    def test_invalid_index_falls_back(self):
        client = SimpleNamespace(
            responses=SimpleNamespace(
                parse=lambda **kwargs: SimpleNamespace(
                    output_parsed=SimpleNamespace(index=19), usage=None
                )
            )
        )
        state = initialize("test")
        self.assertIsNone(rank(state, "configured-model", client))
        self.assertEqual(state.model_usage["failures"], 1)
        self.assertEqual(state.model_usage["failure_categories"], {"invalid_selection": 1})

    def test_timeout_reservation_is_not_refunded(self):
        checkpoints = []

        def parse(**kwargs):
            raise TimeoutError("sensitive provider detail")

        client = SimpleNamespace(responses=SimpleNamespace(parse=parse))
        state = initialize("test")
        for _ in range(10):
            self.assertIsNone(
                rank(
                    state,
                    "configured-model",
                    client,
                    checkpoint=lambda: checkpoints.append(state.model_usage["calls"]),
                )
            )
        self.assertEqual(state.model_usage["calls"], 3)
        self.assertEqual(state.model_usage["budget_tokens"], 6144)
        self.assertEqual(state.model_usage["tokens"], 0)
        self.assertEqual(checkpoints[0], 1)
        self.assertEqual(state.model_usage["unmeasured_calls"], 3)
        self.assertEqual(state.model_usage["failure_categories"], {"timeout": 3})
        self.assertNotIn("sensitive provider detail", json.dumps(state.to_dict()))

    def test_provider_failure_categories_redact_payloads(self):
        import httpx
        from openai import AuthenticationError, BadRequestError, RateLimitError

        for error_type, status, code, category in (
            (AuthenticationError, 401, "invalid_api_key", "authentication_error"),
            (RateLimitError, 429, "insufficient_quota", "insufficient_quota"),
            (RateLimitError, 429, "rate_limit_exceeded", "rate_limit"),
            (BadRequestError, 400, "invalid_json_schema", "invalid_request"),
        ):
            with self.subTest(category=category):
                response = httpx.Response(
                    status, request=httpx.Request("POST", "https://example.com")
                )
                error = error_type(
                    "sensitive provider detail",
                    response=response,
                    body={"code": code, "message": "sensitive provider detail"},
                )

                def parse(error=error, **kwargs):
                    raise error

                state = initialize("test")
                client = SimpleNamespace(responses=SimpleNamespace(parse=parse))
                self.assertIsNone(rank(state, "configured-model", client))
                self.assertEqual(state.model_usage["failure_categories"], {category: 1})
                self.assertNotIn("sensitive provider detail", json.dumps(state.to_dict()))

    def test_quota_in_provider_type_is_classified(self):
        import httpx
        from openai import RateLimitError

        from packages.discovery.model import failure_category

        for body in (
            {"type": "insufficient_quota", "code": None},
            {"error": {"type": "insufficient_quota", "code": None}},
        ):
            response = httpx.Response(429, request=httpx.Request("POST", "https://example.com"))
            error = RateLimitError("private detail", response=response, body=body)
            self.assertEqual(failure_category(error), "insufficient_quota")

    def test_random_seed_survives_checkpoint_and_changes_selection(self):
        from packages.discovery.engine import choose
        from packages.discovery.models import Experiment, Knowledge

        def selections(seed):
            state = initialize("seed-test", strategy="random")
            state.pending = [Experiment("GET", f"/{i}") for i in range(20)]
            state.random_seed = seed
            state = Knowledge.from_dict(state.to_dict())
            self.assertEqual(state.random_seed, seed)
            return [choose(state).path for _ in range(10)]

        self.assertEqual(selections(42), selections(42))
        self.assertNotEqual(selections(42), selections(43))


class LlmConfigurationTests(unittest.TestCase):
    def test_cli_rejects_missing_credentials_and_core_runner(self):
        import contextlib
        import io
        from unittest.mock import patch

        from scripts.discover import main

        for environment, runner, expected in (  # pragma: allowlist secret
            ({}, "graph", "requires exported OPENAI_API_KEY and LLM_MODEL"),
            (
                {"OPENAI_API_KEY": "test", "LLM_MODEL": "test"},  # pragma: allowlist secret
                "core",
                "requires --runner graph",
            ),  # pragma: allowlist secret
        ):
            with self.subTest(runner=runner):
                stderr = io.StringIO()
                arguments = [
                    "discover",
                    "--config",
                    "unused.json",
                    "--output",
                    "unused",
                    "--strategy",
                    "llm",
                    "--runner",
                    runner,
                ]
                with (
                    patch.dict("os.environ", environment, clear=True),
                    patch("sys.argv", arguments),
                    contextlib.redirect_stderr(stderr),
                    self.assertRaises(SystemExit) as raised,
                ):
                    main()
                self.assertEqual(raised.exception.code, 2)
                self.assertIn(expected, stderr.getvalue())
