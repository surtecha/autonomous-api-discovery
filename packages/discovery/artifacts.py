"""Deterministic OpenAPI and typed SDK generation. No generated code is executed here."""

from __future__ import annotations

import ast
import json
import keyword
import re
from pathlib import Path

from .engine import canonical
from .inference import merge
from .models import Json, Knowledge


def operation_name(method: str, path: str) -> str:
    return method.lower() + "_" + re.sub(r"[^a-zA-Z0-9]+", "_", path).strip("_")


def openapi(state: Knowledge) -> Json:
    paths: Json = {}
    for operation in state.operations.values():
        path, method = operation["path"], operation["method"].lower()
        item: Json = {
            "operationId": operation_name(method, path),
            "x-evidence": operation["evidence"],
            "x-verification": "observed-success",
            "responses": {
                code: {
                    "description": "Observed sanitized response",
                    "content": {"application/json": {"schema": schema}},
                }
                for code, schema in operation["responses"].items()
            },
        }
        if "{id}" in path:
            item["parameters"] = [
                {"name": "id", "in": "path", "required": True, "schema": {"type": "integer"}}
            ]
        if operation["request"]:
            schema = dict(operation["request"])
            schema["required"] = sorted(
                name
                for name, claim in operation["fields"].items()
                if claim["required"] is True and claim["verified"]
            )
            schema["x-field-evidence"] = operation["fields"]
            item["requestBody"] = {
                "required": True,
                "content": {"application/json": {"schema": schema}},
            }
        paths.setdefault(path, {})[method] = item
    return {
        "openapi": "3.1.0",
        "info": {"title": "Observed API contract", "version": "0.1.0"},
        "paths": paths,
        "x-session-id": state.session_id,
        "x-limitations": [
            "Response required sets describe observed samples, not universal guarantees",
            "Sensitive fields and arbitrary strings are removed before inference",
        ],
    }


def annotation(schema: Json) -> str:
    if "anyOf" in schema:
        return " | ".join(dict.fromkeys(annotation(item) for item in schema["anyOf"]))
    kind = schema.get("type", "")
    if kind == "array":
        return "list[" + annotation(schema.get("items", {})) + "]"
    return {
        "integer": "int",
        "number": "float",
        "string": "str",
        "boolean": "bool",
        "object": "dict[str, JsonValue]",
        "null": "None",
    }.get(kind, "JsonValue")


def model_source(name: str, schema: Json, required: set[str]) -> str:
    lines = [
        f"class {name}(BaseModel):",
        '    model_config = ConfigDict(extra="allow", strict=True)',
    ]
    properties = schema.get("properties", {})
    used = set(properties) | set(dir(object))
    for index, (field, subschema) in enumerate(properties.items()):
        attribute = field
        # Preserve wire names while avoiding Python keywords and BaseModel attributes.
        if (
            not re.fullmatch(r"[a-z][a-z0-9_]*", field)
            or keyword.iskeyword(field)
            or field.startswith("model_")
            or field
            in {
                "dict",
                "json",
                "copy",
                "schema",
                "schema_json",
                "validate",
                "construct",
                "parse_obj",
                "parse_raw",
                "parse_file",
                "from_orm",
                "update_forward_refs",
            }
        ):
            attribute = f"wire_field_{index}"
            while attribute in used:
                attribute += "_"
        used.add(attribute)
        typed = annotation(subschema)
        if field not in required and "None" not in typed.split(" | "):
            typed += " | None"
        default = "..." if field in required else "None"
        lines.append(f"    {attribute}: {typed} = Field({default}, alias={field!r})")
    return "\n".join(lines) + "\n\n"


SDK_HEADER = '''"""Generated from observed evidence. Runtime credentials remain caller-supplied."""
from __future__ import annotations

import re
from collections.abc import Iterator
from types import TracebackType
from typing import Self

import httpx
from pydantic import BaseModel, ConfigDict, Field, JsonValue


class APIError(Exception):
    def __init__(self, status: int) -> None:
        self.status = status
        super().__init__(f"API returned HTTP {status}")


'''
CLIENT_HEADER = r"""class Client:
    def __init__(self, base_url: str, token: str | None = None, timeout: float = 5,
                 transport: httpx.BaseTransport | None = None) -> None:
        headers = {"Authorization": "Bearer " + token} if token else {}
        self._http = httpx.Client(base_url=base_url, timeout=timeout, headers=headers,
                                  follow_redirects=False, trust_env=False, transport=transport)

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type: type[BaseException] | None,
                 exc: BaseException | None, tb: TracebackType | None) -> None:
        self._http.close()

    def _request(self, method: str, path: str, body: BaseModel | None = None,
                 params: dict[str, int] | None = None) -> dict[str, JsonValue]:
        response = self._http.request(method, path, params=params,
            json=body.model_dump(exclude_unset=True, by_alias=True) if body else None)
        if not 200 <= response.status_code < 300:
            raise APIError(response.status_code)
        data = response.json()
        if not isinstance(data, dict):
            raise TypeError("Expected an object response")
        return data

    def _pages(self, path: str, max_pages: int) -> Iterator[dict[str, JsonValue]]:
        if not 1 <= max_pages <= 1000:
            raise ValueError("max_pages must be between 1 and 1000")
        current = path
        seen: set[str] = set()
        for _ in range(max_pages):
            if current in seen:
                raise ValueError("Pagination cycle detected")
            seen.add(current)
            data = self._request("GET", current)
            yield data
            links = data.get("links", [])
            following: str | None = None
            if isinstance(links, list):
                for link in links:
                    if not isinstance(link, dict) or link.get("method", "GET") != "GET":
                        continue
                    href = link.get("href")
                    if isinstance(href, str) and re.fullmatch(
                        re.escape(path) + r"\?(?:cursor|limit)=[0-9]{1,6}", href
                    ):
                        following = href
                        break
            if following is None:
                return
            current = following
        raise ValueError("Pagination page limit exceeded")

"""


def generate(state: Knowledge, output: Path) -> Json:
    output.mkdir(parents=True, exist_ok=True)
    spec = openapi(state)
    (output / "openapi.json").write_text(json.dumps(spec, indent=2) + "\n")
    models, methods = [], []
    for operation in state.operations.values():
        name = operation_name(operation["method"], operation["path"])
        class_name = "".join(part.capitalize() for part in name.split("_"))
        request_name, response_name = class_name + "Request", class_name + "Response"
        body = operation["request"]
        if body:
            required = {
                key
                for key, claim in operation["fields"].items()
                if claim["required"] is True and claim["verified"]
            }
            models.append(model_source(request_name, body, required))
        responses = list(operation["responses"].values())
        schema: Json = {}
        for response in responses:
            schema = merge(schema, response)
        models.append(model_source(response_name, schema, set(schema.get("required", []))))
        parameters = ", id: int" if "{id}" in operation["path"] else ""
        paginated = (
            operation["method"] == "GET"
            and "{id}" not in operation["path"]
            and "items" in schema.get("properties", {})
        )
        if body:
            parameters += f", body: {request_name}"
        if paginated:
            parameters += ", *, cursor: int | None = None, limit: int | None = None"
        path = repr(operation["path"])
        if "{id}" in operation["path"]:
            path = "f" + path
        query = (
            ", params={key: value for key, value in {'cursor': cursor, 'limit': limit}.items() "
            "if value is not None}"
            if paginated
            else ""
        )
        methods.append(
            f"    def {name}(self{parameters}) -> {response_name}:\n"
            f"        return {response_name}.model_validate(self._request("
            f"{operation['method']!r}, {path}, {'body' if body else 'None'}{query}))\n\n"
        )
        if paginated:
            methods.append(
                f"    def iter_{name}_pages(self, max_pages: int = 100) -> Iterator[{response_name}]:\n"
                f"        for data in self._pages({path}, max_pages):\n"
                f"            yield {response_name}.model_validate(data)\n\n"
            )
    imports = ["BaseModel", "JsonValue"]
    if models:
        imports.append("ConfigDict")
    if any("Field(" in model for model in models):
        imports.append("Field")
    header = SDK_HEADER.replace(
        "from pydantic import BaseModel, ConfigDict, Field, JsonValue",
        "from pydantic import " + ", ".join(sorted(imports)),
    )
    source = (header + "".join(models) + CLIENT_HEADER + "".join(methods)).rstrip() + "\n"
    ast.parse(source)
    (output / "client.py").write_text(source)
    (output / "pyproject.toml").write_text("""[build-system]
requires = ["setuptools>=75"]
build-backend = "setuptools.build_meta"
[project]
name = "observed-api-client"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = ["httpx>=0.28,<1", "pydantic>=2.10,<3"]
[tool.setuptools]
py-modules = ["client"]
""")
    fixtures = []
    for observation in state.observations:
        if 200 <= observation.status < 300 and observation.category in {
            "http",
            "in_process_fixture",
        }:
            name = operation_name(
                observation.experiment.method, canonical(observation.experiment.path)
            )
            class_name = "".join(part.capitalize() for part in name.split("_"))
            operation = state.operations[
                observation.experiment.method + " " + canonical(observation.experiment.path)
            ]
            fixtures.append(
                {
                    "method": observation.experiment.method,
                    "operation": name,
                    "request_model": class_name + "Request" if operation["request"] else None,
                    "response_model": class_name + "Response",
                    "path": observation.experiment.path,
                    "body": observation.experiment.body,
                    "status": observation.status,
                    "response": observation.body,
                }
            )
    (output / "fixtures.json").write_text(json.dumps(fixtures, indent=2) + "\n")
    (output / "test_client.py").write_text("""import json
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
import httpx
import pytest
from pydantic import ValidationError
import client
from jsonschema import Draft202012Validator

FIXTURES = json.loads(Path(__file__).with_name("fixtures.json").read_text())

@pytest.mark.parametrize("fixture", FIXTURES)
def test_observed_response(fixture):
    def handler(request):
        assert request.method == fixture["method"]
        assert request.url.raw_path.decode() == fixture["path"]
        assert request.headers["authorization"] == "Bearer synthetic-test-value"
        if fixture["body"] is not None:
            assert json.loads(request.content) == fixture["body"]
        return httpx.Response(fixture["status"], json=fixture["response"])
    with client.Client("https://example.invalid", token="synthetic-test-value",
                       transport=httpx.MockTransport(handler)) as sdk:
        kwargs = {}
        for segment in urlsplit(fixture["path"]).path.split("/"):
            if segment.isdigit():
                kwargs["id"] = int(segment)
        kwargs.update({key: int(values[0]) for key, values in
                       parse_qs(urlsplit(fixture["path"]).query).items()})
        if fixture["request_model"]:
            kwargs["body"] = getattr(client, fixture["request_model"]).model_validate(fixture["body"])
        parsed = getattr(sdk, fixture["operation"])(**kwargs)
        assert isinstance(parsed, getattr(client, fixture["response_model"]))
        assert parsed.model_dump(exclude_unset=True, by_alias=True) == fixture["response"]

@pytest.mark.parametrize("status", [400, 401, 403, 404, 409, 422, 429, 500, 302])
def test_http_errors(status):
    with client.Client("https://example.invalid", transport=httpx.MockTransport(
        lambda request: httpx.Response(status, json={"secret": "never logged"})
    )) as sdk:
        with pytest.raises(client.APIError) as caught:
            sdk._request("GET", "/")
        assert caught.value.status == status
        assert "never logged" not in str(caught.value)

@pytest.mark.parametrize("fixture", FIXTURES)
def test_observed_contract(fixture):
    specification = json.loads(Path(__file__).with_name("openapi.json").read_text())
    operation = next(operation for methods in specification["paths"].values()
                     for operation in methods.values() if operation["operationId"] == fixture["operation"])
    schema = operation["responses"][str(fixture["status"])]["content"]["application/json"]["schema"]
    Draft202012Validator(schema).validate(fixture["response"])

def test_generated_models():
    for name, model in vars(client).items():
        if isinstance(model, type) and name.endswith("Request"):
            if any(field.is_required() for field in model.model_fields.values()):
                with pytest.raises(ValidationError):
                    model.model_validate({})

def test_pagination_bounds_and_origin():
    requests = []
    def handler(request):
        requests.append(str(request.url))
        return httpx.Response(200, json={"items": [], "links": [
            {"method": "GET", "href": "https://external.invalid/collection?cursor=2"}]})
    with client.Client("https://example.invalid", transport=httpx.MockTransport(handler)) as sdk:
        assert len(list(sdk._pages("/collection", 2))) == 1
        assert len(requests) == 1
        for limit in [0, 1001]:
            with pytest.raises(ValueError):
                list(sdk._pages("/collection", limit))

def test_pagination_cycles_and_limits():
    def handler(request):
        return httpx.Response(200, json={"items": [], "links": [
            {"method": "GET", "href": "/collection?cursor=2"}]})
    with client.Client("https://example.invalid", transport=httpx.MockTransport(handler)) as sdk:
        with pytest.raises(ValueError, match="cycle"):
            list(sdk._pages("/collection", 10))
        with pytest.raises(ValueError, match="page limit"):
            list(sdk._pages("/collection", 1))
""")
    result: Json = {
        "source_ast": "passed",
        "openapi_validation": "not_run",
        "sdk_tests": "not_run",
        "sdk_lint": "not_run",
        "sdk_types": "not_run",
        "sdk_packaging": "not_run",
        "execution": "requires_restricted_container",
    }
    try:
        from openapi_spec_validator import validate
    except ImportError:
        pass
    else:
        try:
            validate(spec)
            result["openapi_validation"] = "passed"
        except Exception:  # noqa: BLE001 - Validator failures are recorded without leaking data.
            result["openapi_validation"] = "failed"
    (output / "validation.json").write_text(json.dumps(result, indent=2) + "\n")
    return result
