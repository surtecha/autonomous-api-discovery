from __future__ import annotations

import json
import unittest
from importlib.util import find_spec
from pathlib import Path
from unittest.mock import patch

from test_core import FixtureGateway, policy
from test_support import temporary_directory

from packages.discovery.engine import initialize, interpret, step, update_requirement
from packages.discovery.evaluation import evaluate
from packages.discovery.models import Experiment, Knowledge, Observation
from packages.discovery.security import PolicyError, sanitize
from targets.service import Target, TargetSessions


class TargetBehaviorTests(unittest.TestCase):
    def test_response_schema_scoring_penalizes_wrong_and_extra_type_claims(self):
        state = Knowledge("response-scoring")
        exp = Experiment("GET", "/things")
        interpret(state, Observation(exp.key, exp, 200, {"id": 1, "state": 1, "extra": True}, 0))
        truth = {
            "operations": {
                "GET /things": {
                    "fields": {},
                    "responses": {
                        "200": {
                            "type": "object",
                            "properties": {"id": {"type": "integer"}, "state": {"type": "string"}},
                        }
                    },
                }
            },
            "transitions": [],
        }
        result = evaluate(state, truth)
        self.assertEqual(result["response_schema_accuracy"], 0.5)
        self.assertEqual(result["response_schema_type_claims"], 4)

    def test_fixture_sessions_have_independent_state_and_bounded_capacity(self):
        import uuid

        targets = TargetSessions("subscriptions")
        first, second = str(uuid.uuid4()), str(uuid.uuid4())
        targets.get(first).handle("POST", "/accounts", {"name": "probe"})
        self.assertEqual(targets.get(second).handle("GET", "/accounts")[1]["items"], [])
        self.assertEqual(len(targets.get(first).handle("GET", "/accounts")[1]["items"]), 1)
        with self.assertRaises(ValueError):
            targets.get("invalid\r\nheader")
        for _ in range(126):
            targets.get(str(uuid.uuid4()))
        with self.assertRaisesRegex(ValueError, "capacity"):
            targets.get(str(uuid.uuid4()))

    def test_missing_references_are_retried_after_prerequisites_exist(self):
        state = initialize("warehouse-dependencies")
        gateway = FixtureGateway("warehouse")
        for _ in range(100):
            if state.status != "running":
                break
            step(state, gateway)
        self.assertIn("POST /fulfillments", state.operations)
        self.assertIn("POST /returns", state.operations)

    def test_rate_limit_retries_are_bounded_and_do_not_confirm_operations(self):
        state = Knowledge("rate-limit")
        experiment = Experiment("GET", "/things")
        for attempt in range(4):
            interpret(state, Observation(experiment.key, experiment, 429, {}, 0))
            self.assertEqual(state.operations, {})
            if attempt < 3:
                self.assertEqual(len(state.pending), 1)
                retry = state.pending.pop()
                self.assertNotEqual(retry.key, experiment.key)
                self.assertEqual(retry.retries, attempt + 1)
                experiment = retry
            else:
                self.assertEqual(state.pending, [])

    def test_conflicting_required_evidence_remains_uncertain(self):
        claim = {"required": None, "verified": False, "confidence": 0.5, "evidence": []}
        update_requirement(claim, True, "required-error")
        self.assertTrue(claim["verified"])
        update_requirement(claim, False, "successful-omission")
        self.assertIsNone(claim["required"])
        self.assertFalse(claim["verified"])
        self.assertTrue(claim["conflict"])
        update_requirement(claim, True, "another-error")
        self.assertFalse(claim["verified"])

    def test_malformed_control_fields_do_not_execute(self):
        for body in (
            {"links": None},
            {"links": [{"method": [], "href": "/"}]},
            {"errors": [{"field": "name", "code": [], "type": {}}]},
            {"errors": [{"field": "name", "code": "required", "type": {}}]},
        ):
            state = Knowledge("malformed")
            exp = Experiment("GET", "/")
            interpret(state, Observation(exp.key, exp, 422, body, 0))
            self.assertEqual(state.pending, [])

    def test_versioned_resource_ids_are_not_conflated(self):
        state = Knowledge("versioned")
        first = Experiment("POST", "/v2/accounts", {})
        second = Experiment("POST", "/v2/jobs/1/complete", {})
        interpret(state, Observation(first.key, first, 201, {"id": 1, "status": "draft"}, 0))
        interpret(state, Observation(second.key, second, 200, {"id": 1, "status": "completed"}, 0))
        self.assertEqual(state.transitions, [])

    def test_reference_validation(self):
        target = Target("ecommerce")
        status, body = target.handle("POST", "/orders", {"customer_id": 42})
        self.assertEqual(status, 422)
        self.assertEqual(body["errors"][0]["code"], "reference")
        self.assertEqual(target.records["orders"], {})

    def test_invalid_state_has_no_side_effect(self):
        target = Target("ecommerce")
        target.handle("POST", "/customers", {"name": "probe"})
        target.handle("POST", "/orders", {"customer_id": 1})
        before = json.dumps(target.records, sort_keys=True)
        status, _ = target.handle("POST", "/orders/1/ship", {})
        self.assertEqual(status, 409)
        self.assertEqual(before, json.dumps(target.records, sort_keys=True))

    def test_pagination(self):
        target = Target("subscriptions")
        for _ in range(5):
            target.handle("POST", "/accounts", {"name": "probe"})
        _, first = target.handle("GET", "/accounts")
        _, second = target.handle("GET", "/accounts?cursor=2")
        self.assertEqual([row["id"] for row in first["items"]], [1, 2])
        self.assertEqual([row["id"] for row in second["items"]], [3, 4])
        self.assertEqual(first["total"], 5)

    def test_reset_is_process_replacement(self):
        target = Target("subscriptions")
        target.handle("POST", "/accounts", {"name": "probe"})
        replacement = Target("subscriptions")
        self.assertEqual(replacement.handle("GET", "/accounts")[1]["items"], [])

    def test_complex_ambiguous_error_not_invented(self):
        target = Target("complex")
        target.handle("POST", "/v2/accounts", {"name": "probe", "profile": {}})
        code, data = target.handle(
            "POST", "/v2/jobs", {"account_id": 1, "config": {}, "mode": "probe"}
        )
        self.assertEqual(code, 400)
        self.assertEqual(data["errors"], [])

    def test_fifo_random_gain_real_outcomes(self):
        truth = json.loads(Path("targets/ground_truth/subscriptions.json").read_text())
        for strategy in ("fifo", "random", "gain"):
            state = initialize(strategy, strategy=strategy)
            gateway = FixtureGateway("subscriptions")
            for _ in range(100):
                if state.status != "running":
                    break
                step(state, gateway)
            metrics = evaluate(state, truth)
            self.assertEqual(metrics["unsupported_operations"], 0)
            self.assertGreater(metrics["endpoint_recall"], 0)
            self.assertLessEqual(metrics["endpoint_precision"], 1)
            self.assertIsNone(metrics["sdk_test_pass_rate"])

    def test_control_char_origin_rejected(self):
        for origin in ("http://127.0.\n0.1:9101", "http://127.0.0.1:9101\\x"):
            with self.assertRaises(PolicyError):
                policy(origin=origin).validate()


@unittest.skipUnless(find_spec("langgraph"), "LangGraph dependency is not installed")
class GraphTests(unittest.TestCase):
    def test_persistent_graph_completion_and_resume(self):
        from packages.discovery.graph import run_graph

        fixture = FixtureGateway("subscriptions")
        with (
            temporary_directory() as folder,
            patch("packages.discovery.graph.Gateway", return_value=fixture),
        ):
            state = run_graph("test", policy(), Path(folder))
            self.assertTrue(state.operations)
            calls = fixture.target.calls
            resumed = run_graph("test", policy(), Path(folder))
            self.assertEqual(resumed.operations, state.operations)
            self.assertEqual(calls, fixture.target.calls)


@unittest.skipUnless(
    find_spec("hypothesis") and find_spec("jsonschema"),
    "Property testing dependencies are not installed",
)
class PropertyTests(unittest.TestCase):
    def test_inferred_schema_accepts_observed_json(self):
        from hypothesis import given
        from hypothesis import strategies as st
        from jsonschema import Draft202012Validator

        from packages.discovery.inference import infer

        values = st.recursive(
            st.none() | st.booleans() | st.integers() | st.text(),
            lambda children: (
                st.lists(children, max_size=5) | st.dictionaries(st.text(), children, max_size=5)
            ),
            max_leaves=15,
        )

        @given(values)
        def check(value):
            Draft202012Validator(infer(value)).validate(value)

        check()

    def test_arbitrary_response_text_is_removed(self):
        from hypothesis import given
        from hypothesis import strategies as st

        @given(st.text())
        def check(value):
            self.assertEqual(sanitize({"description": value})["description"], "[redacted]")

        check()
