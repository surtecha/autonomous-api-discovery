"""Static consistency checks only. Generated modules are never imported."""

from __future__ import annotations

import ast
import json
from pathlib import Path


def validate(root: Path) -> dict[str, object]:
    checked = 0
    for specification in sorted(root.rglob("openapi.json")):
        directory = specification.parent
        spec = json.loads(specification.read_text())
        client = ast.parse((directory / "client.py").read_text())
        ast.parse((directory / "test_client.py").read_text())
        classes = {node.name for node in client.body if isinstance(node, ast.ClassDef)}
        sdk = next(
            node for node in client.body if isinstance(node, ast.ClassDef) and node.name == "Client"
        )
        methods = {node.name for node in sdk.body if isinstance(node, ast.FunctionDef)}
        names = []
        assert spec["openapi"] == "3.1.0"
        for path, operations in spec["paths"].items():
            assert path.startswith("/")
            for method, operation in operations.items():
                assert method in {"get", "post", "put", "patch", "delete", "options", "head"}
                names.append(operation["operationId"])
                assert operation["operationId"] in methods
                assert operation["x-evidence"]
                if "{id}" in path:
                    assert any(
                        parameter["name"] == "id" and parameter["required"]
                        for parameter in operation["parameters"]
                    )
        assert len(names) == len(set(names))
        for fixture in json.loads((directory / "fixtures.json").read_text()):
            assert fixture["operation"] in methods
            assert fixture["response_model"] in classes
            if fixture["request_model"]:
                assert fixture["request_model"] in classes
        checked += 1
    if checked == 0:
        raise ValueError("No generated specifications found")
    return {
        "artifact_bundles": checked,
        "static_consistency": "passed",
        "generated_code_executed": False,
        "openapi_standard_validation": "not_performed_by_this_check",
    }


if __name__ == "__main__":
    root = Path("experiments/reports/fixture-diagnostics")
    result = validate(root)
    (root.parent / "artifact-static-checks.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))
