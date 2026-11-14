import json
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
