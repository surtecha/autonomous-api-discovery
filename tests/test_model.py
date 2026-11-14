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
