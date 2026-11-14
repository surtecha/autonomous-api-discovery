"""Generated from observed evidence. Runtime credentials remain caller-supplied."""
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


class GetResponse(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    links: list[dict[str, JsonValue]] = Field(..., alias='links')

class GetV2AccountsResponse(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    items: list[JsonValue] = Field(..., alias='items')
    total: int = Field(..., alias='total')
    links: list[dict[str, JsonValue]] = Field(..., alias='links')

class OptionsV2AccountsResponse(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    links: list[dict[str, JsonValue]] = Field(..., alias='links')

class GetV2JobsResponse(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    items: list[JsonValue] = Field(..., alias='items')
    total: int = Field(..., alias='total')
    links: list[dict[str, JsonValue]] = Field(..., alias='links')

class OptionsV2JobsResponse(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    links: list[dict[str, JsonValue]] = Field(..., alias='links')

class GetV2BatchesResponse(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    items: list[JsonValue] = Field(..., alias='items')
    total: int = Field(..., alias='total')
    links: list[dict[str, JsonValue]] = Field(..., alias='links')

class OptionsV2BatchesResponse(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    links: list[dict[str, JsonValue]] = Field(..., alias='links')

class PostV2AccountsRequest(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    name: str = Field(..., alias='name')
    profile: dict[str, JsonValue] = Field(..., alias='profile')

class PostV2AccountsResponse(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    id: int = Field(..., alias='id')
    name: str = Field(..., alias='name')
    profile: dict[str, JsonValue] = Field(..., alias='profile')
    status: str = Field(..., alias='status')
    links: list[dict[str, JsonValue]] = Field(..., alias='links')

class GetV2AccountsIdResponse(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    id: int = Field(..., alias='id')
    name: str = Field(..., alias='name')
    profile: dict[str, JsonValue] = Field(..., alias='profile')
    status: str = Field(..., alias='status')
    links: list[dict[str, JsonValue]] = Field(..., alias='links')

class Client:
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

    def get_(self) -> GetResponse:
        return GetResponse.model_validate(self._request('GET', '/', None))

    def get_v2_accounts(self, *, cursor: int | None = None, limit: int | None = None) -> GetV2AccountsResponse:
        return GetV2AccountsResponse.model_validate(self._request('GET', '/v2/accounts', None, params={key: value for key, value in {'cursor': cursor, 'limit': limit}.items() if value is not None}))

    def iter_get_v2_accounts_pages(self, max_pages: int = 100) -> Iterator[GetV2AccountsResponse]:
        for data in self._pages('/v2/accounts', max_pages):
            yield GetV2AccountsResponse.model_validate(data)

    def options_v2_accounts(self) -> OptionsV2AccountsResponse:
        return OptionsV2AccountsResponse.model_validate(self._request('OPTIONS', '/v2/accounts', None))

    def get_v2_jobs(self, *, cursor: int | None = None, limit: int | None = None) -> GetV2JobsResponse:
        return GetV2JobsResponse.model_validate(self._request('GET', '/v2/jobs', None, params={key: value for key, value in {'cursor': cursor, 'limit': limit}.items() if value is not None}))

    def iter_get_v2_jobs_pages(self, max_pages: int = 100) -> Iterator[GetV2JobsResponse]:
        for data in self._pages('/v2/jobs', max_pages):
            yield GetV2JobsResponse.model_validate(data)

    def options_v2_jobs(self) -> OptionsV2JobsResponse:
        return OptionsV2JobsResponse.model_validate(self._request('OPTIONS', '/v2/jobs', None))

    def get_v2_batches(self, *, cursor: int | None = None, limit: int | None = None) -> GetV2BatchesResponse:
        return GetV2BatchesResponse.model_validate(self._request('GET', '/v2/batches', None, params={key: value for key, value in {'cursor': cursor, 'limit': limit}.items() if value is not None}))

    def iter_get_v2_batches_pages(self, max_pages: int = 100) -> Iterator[GetV2BatchesResponse]:
        for data in self._pages('/v2/batches', max_pages):
            yield GetV2BatchesResponse.model_validate(data)

    def options_v2_batches(self) -> OptionsV2BatchesResponse:
        return OptionsV2BatchesResponse.model_validate(self._request('OPTIONS', '/v2/batches', None))

    def post_v2_accounts(self, body: PostV2AccountsRequest) -> PostV2AccountsResponse:
        return PostV2AccountsResponse.model_validate(self._request('POST', '/v2/accounts', body))

    def get_v2_accounts_id(self, id: int) -> GetV2AccountsIdResponse:
        return GetV2AccountsIdResponse.model_validate(self._request('GET', f'/v2/accounts/{id}', None))
