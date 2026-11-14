"""Independent scorer. Invoke after discovery, with a separately supplied ground truth."""

from __future__ import annotations

from .models import Json, Knowledge


def schema_types(schema: Json, path: tuple[str, ...] = ()) -> dict[tuple[str, ...], set[str]]:
    """Flatten structural type claims; required fields and values are scored separately."""
    result: dict[tuple[str, ...], set[str]] = {}
    kind = schema.get("type")
    if isinstance(kind, str):
        result[path] = {kind}
    for name, child in schema.get("properties", {}).items():
        result.update(schema_types(child, (*path, name)))
    if "items" in schema:
        result.update(schema_types(schema["items"], (*path, "[]")))
    for variant in schema.get("anyOf", []):
        for location, types in schema_types(variant, path).items():
            result.setdefault(location, set()).update(types)
    return result


def evaluate(state: Knowledge, truth: Json) -> Json:
    actual, expected = set(state.operations), set(truth["operations"])
    correct = actual & expected
    fields_correct = fields_total = required_correct = 0
    unsupported = 0
    response_correct = response_total = 0
    for key, operation in state.operations.items():
        if not operation["evidence"]:
            unsupported += 1
        ground_fields = truth["operations"].get(key, {}).get("fields", {})
        properties = operation["request"].get("properties", {})
        for field in ground_fields.keys() | properties.keys():
            fields_total += 1
            if field in ground_fields and field in properties:
                fields_correct += properties[field].get("type") == ground_fields[field]["type"]
                claim = operation["fields"].get(field, {})
                required_correct += (
                    claim.get("verified", False)
                    and claim.get("required") == ground_fields[field]["required"]
                )
        expected_responses = truth["operations"].get(key, {}).get("responses", {})
        for status in operation["responses"].keys() | expected_responses.keys():
            observed_types = schema_types(operation["responses"].get(status, {}))
            expected_types = schema_types(expected_responses.get(status, {}))
            for location in observed_types.keys() | expected_types.keys():
                response_total += 1
                observed = observed_types.get(location, set())
                expected_type = expected_types.get(location, set())
                response_correct += bool(observed and expected_type) and (
                    observed == expected_type
                    or (observed == {"integer"} and expected_type == {"number"})
                )
    expected_transitions = {(t["operation"], t["from"], t["to"]) for t in truth["transitions"]}
    found_transitions = {
        (t["operation"], t["from"], t["to"]) for t in state.transitions if t["verified"]
    }
    count = len(state.observations)
    success = sum(200 <= o.status < 300 for o in state.observations)
    return {
        "session_id": state.session_id,
        "strategy": state.strategy,
        "discovered_operations": len(actual),
        "correct_operations": len(correct),
        "ground_truth_operations": len(expected),
        "endpoint_precision": len(correct) / len(actual) if actual else None,
        "endpoint_recall": len(correct) / len(expected) if expected else None,
        "request_field_type_accuracy": fields_correct / fields_total if fields_total else None,
        "required_field_accuracy": required_correct / fields_total if fields_total else None,
        "response_schema_accuracy": response_correct / response_total if response_total else None,
        "response_schema_type_claims": response_total,
        "state_transition_coverage": len(found_transitions & expected_transitions)
        / len(expected_transitions)
        if expected_transitions
        else None,
        "requests": count,
        "valid_request_rate": success / count if count else None,
        "requests_per_correct_operation": count / len(correct) if correct else None,
        "unsupported_operations": unsupported,
        "model_usage": state.model_usage,
        "estimated_llm_cost": None,
        "sdk_test_pass_rate": None,
        "limitations": [
            "Schema scoring covers discovered request fields only",
            "Response scoring compares structural types on discovered operations, not values or requiredness",
            "No estimated provider cost without configured pricing",
        ],
    }
