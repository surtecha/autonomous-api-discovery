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

class GetAccountsResponse(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    items: list[JsonValue] = Field(..., alias='items')
    total: int = Field(..., alias='total')
    links: list[dict[str, JsonValue]] = Field(..., alias='links')

class OptionsSubscriptionsResponse(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    links: list[dict[str, JsonValue]] = Field(..., alias='links')

class GetInvoicesResponse(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    items: list[JsonValue] = Field(..., alias='items')
    total: int = Field(..., alias='total')
    links: list[dict[str, JsonValue]] = Field(..., alias='links')

class OptionsPaymentsResponse(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    links: list[dict[str, JsonValue]] = Field(..., alias='links')

class GetPlansResponse(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    items: list[JsonValue] = Field(..., alias='items')
    total: int = Field(..., alias='total')
    links: list[dict[str, JsonValue]] = Field(..., alias='links')

class GetSubscriptionsResponse(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    items: list[JsonValue] = Field(..., alias='items')
    total: int = Field(..., alias='total')
    links: list[dict[str, JsonValue]] = Field(..., alias='links')

class OptionsPlansResponse(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    links: list[dict[str, JsonValue]] = Field(..., alias='links')

class OptionsAccountsResponse(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    links: list[dict[str, JsonValue]] = Field(..., alias='links')

class GetPaymentsResponse(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    items: list[JsonValue] = Field(..., alias='items')
    total: int = Field(..., alias='total')
    links: list[dict[str, JsonValue]] = Field(..., alias='links')

class PostPlansRequest(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    name: str = Field(..., alias='name')
    amount: float = Field(..., alias='amount')

class PostPlansResponse(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    id: int = Field(..., alias='id')
    name: str = Field(..., alias='name')
    amount: float = Field(..., alias='amount')
    status: str = Field(..., alias='status')
    links: list[dict[str, JsonValue]] = Field(..., alias='links')

class GetPlansIdResponse(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    id: int = Field(..., alias='id')
    name: str = Field(..., alias='name')
    amount: float = Field(..., alias='amount')
    status: str = Field(..., alias='status')
    links: list[dict[str, JsonValue]] = Field(..., alias='links')

class OptionsInvoicesResponse(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    links: list[dict[str, JsonValue]] = Field(..., alias='links')

class PostAccountsRequest(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    name: str = Field(..., alias='name')

class PostAccountsResponse(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    id: int = Field(..., alias='id')
    name: str = Field(..., alias='name')
    status: str = Field(..., alias='status')
    links: list[dict[str, JsonValue]] = Field(..., alias='links')

class GetAccountsIdResponse(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    id: int = Field(..., alias='id')
    name: str = Field(..., alias='name')
    status: str = Field(..., alias='status')
    links: list[dict[str, JsonValue]] = Field(..., alias='links')

class PostSubscriptionsRequest(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    account_id: int = Field(..., alias='account_id')
    plan_id: int = Field(..., alias='plan_id')

class PostSubscriptionsResponse(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    id: int = Field(..., alias='id')
    account_id: int = Field(..., alias='account_id')
    plan_id: int = Field(..., alias='plan_id')
    status: str = Field(..., alias='status')
    links: list[dict[str, JsonValue]] = Field(..., alias='links')

class PostInvoicesRequest(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    subscription_id: int = Field(..., alias='subscription_id')
    amount: float = Field(..., alias='amount')

class PostInvoicesResponse(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    id: int = Field(..., alias='id')
    subscription_id: int = Field(..., alias='subscription_id')
    amount: float = Field(..., alias='amount')
    status: str = Field(..., alias='status')
    links: list[dict[str, JsonValue]] = Field(..., alias='links')

class GetSubscriptionsIdResponse(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    id: int = Field(..., alias='id')
    account_id: int = Field(..., alias='account_id')
    plan_id: int = Field(..., alias='plan_id')
    status: str = Field(..., alias='status')
    links: list[dict[str, JsonValue]] = Field(..., alias='links')

class PostPaymentsRequest(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    invoice_id: int = Field(..., alias='invoice_id')
    amount: float = Field(..., alias='amount')

class PostPaymentsResponse(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    id: int = Field(..., alias='id')
    invoice_id: int = Field(..., alias='invoice_id')
    amount: float = Field(..., alias='amount')
    status: str = Field(..., alias='status')
    links: list[dict[str, JsonValue]] = Field(..., alias='links')

class PostSubscriptionsIdActivateRequest(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)

class PostSubscriptionsIdActivateResponse(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    id: int = Field(..., alias='id')
    account_id: int = Field(..., alias='account_id')
    plan_id: int = Field(..., alias='plan_id')
    status: str = Field(..., alias='status')
    links: list[dict[str, JsonValue]] = Field(..., alias='links')

class GetInvoicesIdResponse(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    id: int = Field(..., alias='id')
    subscription_id: int = Field(..., alias='subscription_id')
    amount: float = Field(..., alias='amount')
    status: str = Field(..., alias='status')
    links: list[dict[str, JsonValue]] = Field(..., alias='links')

class PostSubscriptionsIdRenewRequest(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)

class PostSubscriptionsIdRenewResponse(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    id: int = Field(..., alias='id')
    account_id: int = Field(..., alias='account_id')
    plan_id: int = Field(..., alias='plan_id')
    status: str = Field(..., alias='status')
    links: list[dict[str, JsonValue]] = Field(..., alias='links')

class PostSubscriptionsIdCancelRequest(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)

class PostSubscriptionsIdCancelResponse(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    id: int = Field(..., alias='id')
    account_id: int = Field(..., alias='account_id')
    plan_id: int = Field(..., alias='plan_id')
    status: str = Field(..., alias='status')
    links: list[dict[str, JsonValue]] = Field(..., alias='links')

class GetPaymentsIdResponse(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    id: int = Field(..., alias='id')
    invoice_id: int = Field(..., alias='invoice_id')
    amount: float = Field(..., alias='amount')
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

    def get_accounts(self, *, cursor: int | None = None, limit: int | None = None) -> GetAccountsResponse:
        return GetAccountsResponse.model_validate(self._request('GET', '/accounts', None, params={key: value for key, value in {'cursor': cursor, 'limit': limit}.items() if value is not None}))

    def iter_get_accounts_pages(self, max_pages: int = 100) -> Iterator[GetAccountsResponse]:
        for data in self._pages('/accounts', max_pages):
            yield GetAccountsResponse.model_validate(data)

    def options_subscriptions(self) -> OptionsSubscriptionsResponse:
        return OptionsSubscriptionsResponse.model_validate(self._request('OPTIONS', '/subscriptions', None))

    def get_invoices(self, *, cursor: int | None = None, limit: int | None = None) -> GetInvoicesResponse:
        return GetInvoicesResponse.model_validate(self._request('GET', '/invoices', None, params={key: value for key, value in {'cursor': cursor, 'limit': limit}.items() if value is not None}))

    def iter_get_invoices_pages(self, max_pages: int = 100) -> Iterator[GetInvoicesResponse]:
        for data in self._pages('/invoices', max_pages):
            yield GetInvoicesResponse.model_validate(data)

    def options_payments(self) -> OptionsPaymentsResponse:
        return OptionsPaymentsResponse.model_validate(self._request('OPTIONS', '/payments', None))

    def get_plans(self, *, cursor: int | None = None, limit: int | None = None) -> GetPlansResponse:
        return GetPlansResponse.model_validate(self._request('GET', '/plans', None, params={key: value for key, value in {'cursor': cursor, 'limit': limit}.items() if value is not None}))

    def iter_get_plans_pages(self, max_pages: int = 100) -> Iterator[GetPlansResponse]:
        for data in self._pages('/plans', max_pages):
            yield GetPlansResponse.model_validate(data)

    def get_subscriptions(self, *, cursor: int | None = None, limit: int | None = None) -> GetSubscriptionsResponse:
        return GetSubscriptionsResponse.model_validate(self._request('GET', '/subscriptions', None, params={key: value for key, value in {'cursor': cursor, 'limit': limit}.items() if value is not None}))

    def iter_get_subscriptions_pages(self, max_pages: int = 100) -> Iterator[GetSubscriptionsResponse]:
        for data in self._pages('/subscriptions', max_pages):
            yield GetSubscriptionsResponse.model_validate(data)

    def options_plans(self) -> OptionsPlansResponse:
        return OptionsPlansResponse.model_validate(self._request('OPTIONS', '/plans', None))

    def options_accounts(self) -> OptionsAccountsResponse:
        return OptionsAccountsResponse.model_validate(self._request('OPTIONS', '/accounts', None))

    def get_payments(self, *, cursor: int | None = None, limit: int | None = None) -> GetPaymentsResponse:
        return GetPaymentsResponse.model_validate(self._request('GET', '/payments', None, params={key: value for key, value in {'cursor': cursor, 'limit': limit}.items() if value is not None}))

    def iter_get_payments_pages(self, max_pages: int = 100) -> Iterator[GetPaymentsResponse]:
        for data in self._pages('/payments', max_pages):
            yield GetPaymentsResponse.model_validate(data)

    def post_plans(self, body: PostPlansRequest) -> PostPlansResponse:
        return PostPlansResponse.model_validate(self._request('POST', '/plans', body))

    def get_plans_id(self, id: int) -> GetPlansIdResponse:
        return GetPlansIdResponse.model_validate(self._request('GET', f'/plans/{id}', None))

    def options_invoices(self) -> OptionsInvoicesResponse:
        return OptionsInvoicesResponse.model_validate(self._request('OPTIONS', '/invoices', None))

    def post_accounts(self, body: PostAccountsRequest) -> PostAccountsResponse:
        return PostAccountsResponse.model_validate(self._request('POST', '/accounts', body))

    def get_accounts_id(self, id: int) -> GetAccountsIdResponse:
        return GetAccountsIdResponse.model_validate(self._request('GET', f'/accounts/{id}', None))

    def post_subscriptions(self, body: PostSubscriptionsRequest) -> PostSubscriptionsResponse:
        return PostSubscriptionsResponse.model_validate(self._request('POST', '/subscriptions', body))

    def post_invoices(self, body: PostInvoicesRequest) -> PostInvoicesResponse:
        return PostInvoicesResponse.model_validate(self._request('POST', '/invoices', body))

    def get_subscriptions_id(self, id: int) -> GetSubscriptionsIdResponse:
        return GetSubscriptionsIdResponse.model_validate(self._request('GET', f'/subscriptions/{id}', None))

    def post_payments(self, body: PostPaymentsRequest) -> PostPaymentsResponse:
        return PostPaymentsResponse.model_validate(self._request('POST', '/payments', body))

    def post_subscriptions_id_activate(self, id: int, body: PostSubscriptionsIdActivateRequest) -> PostSubscriptionsIdActivateResponse:
        return PostSubscriptionsIdActivateResponse.model_validate(self._request('POST', f'/subscriptions/{id}/activate', body))

    def get_invoices_id(self, id: int) -> GetInvoicesIdResponse:
        return GetInvoicesIdResponse.model_validate(self._request('GET', f'/invoices/{id}', None))

    def post_subscriptions_id_renew(self, id: int, body: PostSubscriptionsIdRenewRequest) -> PostSubscriptionsIdRenewResponse:
        return PostSubscriptionsIdRenewResponse.model_validate(self._request('POST', f'/subscriptions/{id}/renew', body))

    def post_subscriptions_id_cancel(self, id: int, body: PostSubscriptionsIdCancelRequest) -> PostSubscriptionsIdCancelResponse:
        return PostSubscriptionsIdCancelResponse.model_validate(self._request('POST', f'/subscriptions/{id}/cancel', body))

    def get_payments_id(self, id: int) -> GetPaymentsIdResponse:
        return GetPaymentsIdResponse.model_validate(self._request('GET', f'/payments/{id}', None))
