"""Generator regression checks without importing generated code on the host."""

import ast
import json
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from test_support import temporary_directory

from packages.discovery.artifacts import generate, model_source, openapi
from packages.discovery.models import Experiment, Knowledge, Observation
from scripts.test_sandbox import CHECKS, main, run, validation_passed


class ArtifactTests(unittest.TestCase):
    def test_rejected_success_does_not_become_sdk_fixture(self):
        state = Knowledge("unsupported-response")
        state.observations.append(
            Observation("unsupported", Experiment("GET", "/"), 200, {}, 1.0, "unsupported_content")
        )
        with temporary_directory() as folder:
            generate(state, Path(folder))
            self.assertEqual(json.loads((Path(folder) / "fixtures.json").read_text()), [])

    def test_optional_null_field_has_valid_annotation(self):
        source = model_source("Response", {"properties": {"value": {"type": "null"}}}, set())
        model = ast.parse(source).body[0]
        field = next(node for node in model.body if isinstance(node, ast.AnnAssign))
        self.assertIsInstance(field.annotation, ast.Constant)
        self.assertIsNone(field.annotation.value)

    def test_reserved_wire_fields_keep_aliases_and_required_validation(self):
        names = ["class", "model_dump", "first-name", "dict", "wire_field_0", "normal"]
        source = model_source(
            "Request", {"properties": {name: {"type": "string"} for name in names}}, set(names)
        )
        model = ast.parse(source).body[0]
        fields = [node for node in model.body if isinstance(node, ast.AnnAssign)]
        attributes = [node.target.id for node in fields]
        self.assertEqual(len(attributes), len(set(attributes)))
        aliases = [
            ast.literal_eval(next(k.value for k in node.value.keywords if k.arg == "alias"))
            for node in fields
        ]
        self.assertEqual(aliases, names)
        self.assertTrue(all(isinstance(node.value.args[0], ast.Constant) for node in fields))
        self.assertTrue(all(node.value.args[0].value is Ellipsis for node in fields))

    def test_response_status_schemas_merge_and_uncertain_fields_remain_optional(self):
        state = Knowledge("generator-regression")
        state.operations["POST /things"] = {
            "method": "POST",
            "path": "/things",
            "evidence": ["observed"],
            "request": {"type": "object", "properties": {"name": {"type": "string"}}},
            "fields": {"name": {"required": True, "verified": False}},
            "responses": {
                "200": {
                    "type": "object",
                    "properties": {"name": {"type": "string"}},
                    "required": ["name"],
                },
                "201": {
                    "type": "object",
                    "properties": {"id": {"type": "integer"}},
                    "required": ["id"],
                },
            },
        }
        spec = openapi(state)
        self.assertEqual(
            spec["paths"]["/things"]["post"]["requestBody"]["content"]["application/json"][
                "schema"
            ]["required"],
            [],
        )
        with temporary_directory() as folder:
            generate(state, Path(folder))
            tree = ast.parse((Path(folder) / "client.py").read_text())
            classes = {node.name: node for node in tree.body if isinstance(node, ast.ClassDef)}
            response = classes["PostThingsResponse"]
            fields = [node for node in response.body if isinstance(node, ast.AnnAssign)]
            self.assertEqual({node.target.id for node in fields}, {"name", "id"})
            request = classes["PostThingsRequest"]
            name = next(node for node in request.body if isinstance(node, ast.AnnAssign))
            self.assertIsNone(name.value.args[0].value)
            validation = json.loads((Path(folder) / "validation.json").read_text())
            self.assertEqual(validation["sdk_tests"], "not_run")


class ValidationGateTests(unittest.TestCase):
    def test_cli_fails_when_docker_is_unavailable(self):
        with (
            patch("sys.argv", ["test_sandbox", "unused"]),
            patch(
                "scripts.test_sandbox.run", return_value=dict.fromkeys(CHECKS, "unavailable_docker")
            ),
            redirect_stdout(StringIO()),
        ):
            self.assertEqual(main(), 1)

    def test_mount_rejects_extra_files_and_directory_symlinks(self):
        with temporary_directory() as folder:
            directory = Path(folder) / "sdk"
            generate(Knowledge("empty"), directory)
            (directory / ".env").write_text("must not enter the sandbox")
            with self.assertRaisesRegex(ValueError, "Only generated SDK bundle"):
                run(directory)
            (directory / ".env").unlink()
            link = Path(folder) / "linked-sdk"
            link.symlink_to(directory, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "symlinks"):
                run(link)

    def test_all_checks_and_actual_test_counts_are_required(self):
        passed = dict.fromkeys(CHECKS, "passed") | {
            "test_counts": {"tests": 10, "failures": 0, "errors": 0, "skipped": 0}
        }
        self.assertTrue(validation_passed(passed))
        for check in CHECKS:
            for status in ("failed", "timeout", "unavailable_docker", "not_run"):
                self.assertFalse(validation_passed(passed | {check: status}))
        for counts in (
            None,
            {},
            {"tests": 0, "failures": 0, "errors": 0, "skipped": 0},
            {"tests": 10, "failures": 0, "errors": 0, "skipped": 1},
        ):
            self.assertFalse(validation_passed(passed | {"test_counts": counts}))
