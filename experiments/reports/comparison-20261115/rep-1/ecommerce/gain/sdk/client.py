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

class GetCustomersResponse(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    items: list[JsonValue] = Field(..., alias='items')
    total: int = Field(..., alias='total')
    links: list[dict[str, JsonValue]] = Field(..., alias='links')

class PostCustomersRequest(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    name: str = Field(..., alias='name')

class PostCustomersResponse(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    id: int = Field(..., alias='id')
    name: str = Field(..., alias='name')
    status: str = Field(..., alias='status')
    links: list[dict[str, JsonValue]] = Field(..., alias='links')

class GetProductsResponse(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    items: list[JsonValue] = Field(..., alias='items')
    total: int = Field(..., alias='total')
    links: list[dict[str, JsonValue]] = Field(..., alias='links')

class PostProductsRequest(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    name: str = Field(..., alias='name')
    quantity: int = Field(..., alias='quantity')

class PostProductsResponse(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    id: int = Field(..., alias='id')
    name: str = Field(..., alias='name')
    quantity: int = Field(..., alias='quantity')
    status: str = Field(..., alias='status')
    links: list[dict[str, JsonValue]] = Field(..., alias='links')

class GetOrdersResponse(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    items: list[JsonValue] = Field(..., alias='items')
    total: int = Field(..., alias='total')
    links: list[dict[str, JsonValue]] = Field(..., alias='links')

class PostOrdersRequest(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    customer_id: int = Field(..., alias='customer_id')

class PostOrdersResponse(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    id: int = Field(..., alias='id')
    customer_id: int = Field(..., alias='customer_id')
    status: str = Field(..., alias='status')
    links: list[dict[str, JsonValue]] = Field(..., alias='links')

class GetItemsResponse(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    items: list[JsonValue] = Field(..., alias='items')
    total: int = Field(..., alias='total')
    links: list[dict[str, JsonValue]] = Field(..., alias='links')

class PostItemsRequest(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    order_id: int = Field(..., alias='order_id')
    product_id: int = Field(..., alias='product_id')
    quantity: int = Field(..., alias='quantity')

class PostItemsResponse(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    id: int = Field(..., alias='id')
    order_id: int = Field(..., alias='order_id')
    product_id: int = Field(..., alias='product_id')
    quantity: int = Field(..., alias='quantity')
    status: str = Field(..., alias='status')
    links: list[dict[str, JsonValue]] = Field(..., alias='links')

class GetInventoryResponse(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    items: list[JsonValue] = Field(..., alias='items')
    total: int = Field(..., alias='total')
    links: list[dict[str, JsonValue]] = Field(..., alias='links')

class PostInventoryRequest(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    product_id: int = Field(..., alias='product_id')
    quantity: int = Field(..., alias='quantity')

class PostInventoryResponse(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    id: int = Field(..., alias='id')
    product_id: int = Field(..., alias='product_id')
    quantity: int = Field(..., alias='quantity')
    status: str = Field(..., alias='status')
    links: list[dict[str, JsonValue]] = Field(..., alias='links')

class GetPaymentsResponse(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    items: list[JsonValue] = Field(..., alias='items')
    total: int = Field(..., alias='total')
    links: list[dict[str, JsonValue]] = Field(..., alias='links')

class PostPaymentsRequest(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    order_id: int = Field(..., alias='order_id')
    amount: float = Field(..., alias='amount')

class PostPaymentsResponse(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    id: int = Field(..., alias='id')
    order_id: int = Field(..., alias='order_id')
    amount: float = Field(..., alias='amount')
    status: str = Field(..., alias='status')
    links: list[dict[str, JsonValue]] = Field(..., alias='links')

class GetShipmentsResponse(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    items: list[JsonValue] = Field(..., alias='items')
    total: int = Field(..., alias='total')
    links: list[dict[str, JsonValue]] = Field(..., alias='links')

class GetCustomersIdResponse(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    id: int = Field(..., alias='id')
    name: str = Field(..., alias='name')
    status: str = Field(..., alias='status')
    links: list[dict[str, JsonValue]] = Field(..., alias='links')

class GetProductsIdResponse(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    id: int = Field(..., alias='id')
    name: str = Field(..., alias='name')
    quantity: int = Field(..., alias='quantity')
    status: str = Field(..., alias='status')
    links: list[dict[str, JsonValue]] = Field(..., alias='links')

class GetOrdersIdResponse(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    id: int = Field(..., alias='id')
    customer_id: int = Field(..., alias='customer_id')
    status: str = Field(..., alias='status')
    links: list[dict[str, JsonValue]] = Field(..., alias='links')

class PostOrdersIdReserveRequest(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)

class PostOrdersIdReserveResponse(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    id: int = Field(..., alias='id')
    customer_id: int = Field(..., alias='customer_id')
    status: str = Field(..., alias='status')
    links: list[dict[str, JsonValue]] = Field(..., alias='links')

class PostOrdersIdPayRequest(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)

class PostOrdersIdPayResponse(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    id: int = Field(..., alias='id')
    customer_id: int = Field(..., alias='customer_id')
    status: str = Field(..., alias='status')
    links: list[dict[str, JsonValue]] = Field(..., alias='links')

class GetItemsIdResponse(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    id: int = Field(..., alias='id')
    order_id: int = Field(..., alias='order_id')
    product_id: int = Field(..., alias='product_id')
    quantity: int = Field(..., alias='quantity')
    status: str = Field(..., alias='status')
    links: list[dict[str, JsonValue]] = Field(..., alias='links')

class GetInventoryIdResponse(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    id: int = Field(..., alias='id')
    product_id: int = Field(..., alias='product_id')
    quantity: int = Field(..., alias='quantity')
    status: str = Field(..., alias='status')
    links: list[dict[str, JsonValue]] = Field(..., alias='links')

class GetPaymentsIdResponse(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    id: int = Field(..., alias='id')
    order_id: int = Field(..., alias='order_id')
    amount: float = Field(..., alias='amount')
    status: str = Field(..., alias='status')
    links: list[dict[str, JsonValue]] = Field(..., alias='links')

class PostShipmentsRequest(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    order_id: int = Field(..., alias='order_id')

class PostShipmentsResponse(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    id: int = Field(..., alias='id')
    order_id: int = Field(..., alias='order_id')
    status: str = Field(..., alias='status')
    links: list[dict[str, JsonValue]] = Field(..., alias='links')

class GetShipmentsIdResponse(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    id: int = Field(..., alias='id')
    order_id: int = Field(..., alias='order_id')
    status: str = Field(..., alias='status')
    links: list[dict[str, JsonValue]] = Field(..., alias='links')

class PostOrdersIdShipRequest(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)

class PostOrdersIdShipResponse(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    id: int = Field(..., alias='id')
    customer_id: int = Field(..., alias='customer_id')
    status: str = Field(..., alias='status')
    links: list[dict[str, JsonValue]] = Field(..., alias='links')

class OptionsCustomersResponse(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    links: list[dict[str, JsonValue]] = Field(..., alias='links')

class OptionsProductsResponse(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    links: list[dict[str, JsonValue]] = Field(..., alias='links')

class OptionsOrdersResponse(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    links: list[dict[str, JsonValue]] = Field(..., alias='links')

class OptionsItemsResponse(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    links: list[dict[str, JsonValue]] = Field(..., alias='links')

class OptionsInventoryResponse(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    links: list[dict[str, JsonValue]] = Field(..., alias='links')

class OptionsPaymentsResponse(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    links: list[dict[str, JsonValue]] = Field(..., alias='links')

class OptionsShipmentsResponse(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
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

    def get_customers(self, *, cursor: int | None = None, limit: int | None = None) -> GetCustomersResponse:
        return GetCustomersResponse.model_validate(self._request('GET', '/customers', None, params={key: value for key, value in {'cursor': cursor, 'limit': limit}.items() if value is not None}))

    def iter_get_customers_pages(self, max_pages: int = 100) -> Iterator[GetCustomersResponse]:
        for data in self._pages('/customers', max_pages):
            yield GetCustomersResponse.model_validate(data)

    def post_customers(self, body: PostCustomersRequest) -> PostCustomersResponse:
        return PostCustomersResponse.model_validate(self._request('POST', '/customers', body))

    def get_products(self, *, cursor: int | None = None, limit: int | None = None) -> GetProductsResponse:
        return GetProductsResponse.model_validate(self._request('GET', '/products', None, params={key: value for key, value in {'cursor': cursor, 'limit': limit}.items() if value is not None}))

    def iter_get_products_pages(self, max_pages: int = 100) -> Iterator[GetProductsResponse]:
        for data in self._pages('/products', max_pages):
            yield GetProductsResponse.model_validate(data)

    def post_products(self, body: PostProductsRequest) -> PostProductsResponse:
        return PostProductsResponse.model_validate(self._request('POST', '/products', body))

    def get_orders(self, *, cursor: int | None = None, limit: int | None = None) -> GetOrdersResponse:
        return GetOrdersResponse.model_validate(self._request('GET', '/orders', None, params={key: value for key, value in {'cursor': cursor, 'limit': limit}.items() if value is not None}))

    def iter_get_orders_pages(self, max_pages: int = 100) -> Iterator[GetOrdersResponse]:
        for data in self._pages('/orders', max_pages):
            yield GetOrdersResponse.model_validate(data)

    def post_orders(self, body: PostOrdersRequest) -> PostOrdersResponse:
        return PostOrdersResponse.model_validate(self._request('POST', '/orders', body))

    def get_items(self, *, cursor: int | None = None, limit: int | None = None) -> GetItemsResponse:
        return GetItemsResponse.model_validate(self._request('GET', '/items', None, params={key: value for key, value in {'cursor': cursor, 'limit': limit}.items() if value is not None}))

    def iter_get_items_pages(self, max_pages: int = 100) -> Iterator[GetItemsResponse]:
        for data in self._pages('/items', max_pages):
            yield GetItemsResponse.model_validate(data)

    def post_items(self, body: PostItemsRequest) -> PostItemsResponse:
        return PostItemsResponse.model_validate(self._request('POST', '/items', body))

    def get_inventory(self, *, cursor: int | None = None, limit: int | None = None) -> GetInventoryResponse:
        return GetInventoryResponse.model_validate(self._request('GET', '/inventory', None, params={key: value for key, value in {'cursor': cursor, 'limit': limit}.items() if value is not None}))

    def iter_get_inventory_pages(self, max_pages: int = 100) -> Iterator[GetInventoryResponse]:
        for data in self._pages('/inventory', max_pages):
            yield GetInventoryResponse.model_validate(data)

    def post_inventory(self, body: PostInventoryRequest) -> PostInventoryResponse:
        return PostInventoryResponse.model_validate(self._request('POST', '/inventory', body))

    def get_payments(self, *, cursor: int | None = None, limit: int | None = None) -> GetPaymentsResponse:
        return GetPaymentsResponse.model_validate(self._request('GET', '/payments', None, params={key: value for key, value in {'cursor': cursor, 'limit': limit}.items() if value is not None}))

    def iter_get_payments_pages(self, max_pages: int = 100) -> Iterator[GetPaymentsResponse]:
        for data in self._pages('/payments', max_pages):
            yield GetPaymentsResponse.model_validate(data)

    def post_payments(self, body: PostPaymentsRequest) -> PostPaymentsResponse:
        return PostPaymentsResponse.model_validate(self._request('POST', '/payments', body))

    def get_shipments(self, *, cursor: int | None = None, limit: int | None = None) -> GetShipmentsResponse:
        return GetShipmentsResponse.model_validate(self._request('GET', '/shipments', None, params={key: value for key, value in {'cursor': cursor, 'limit': limit}.items() if value is not None}))

    def iter_get_shipments_pages(self, max_pages: int = 100) -> Iterator[GetShipmentsResponse]:
        for data in self._pages('/shipments', max_pages):
            yield GetShipmentsResponse.model_validate(data)

    def get_customers_id(self, id: int) -> GetCustomersIdResponse:
        return GetCustomersIdResponse.model_validate(self._request('GET', f'/customers/{id}', None))

    def get_products_id(self, id: int) -> GetProductsIdResponse:
        return GetProductsIdResponse.model_validate(self._request('GET', f'/products/{id}', None))

    def get_orders_id(self, id: int) -> GetOrdersIdResponse:
        return GetOrdersIdResponse.model_validate(self._request('GET', f'/orders/{id}', None))

    def post_orders_id_reserve(self, id: int, body: PostOrdersIdReserveRequest) -> PostOrdersIdReserveResponse:
        return PostOrdersIdReserveResponse.model_validate(self._request('POST', f'/orders/{id}/reserve', body))

    def post_orders_id_pay(self, id: int, body: PostOrdersIdPayRequest) -> PostOrdersIdPayResponse:
        return PostOrdersIdPayResponse.model_validate(self._request('POST', f'/orders/{id}/pay', body))

    def get_items_id(self, id: int) -> GetItemsIdResponse:
        return GetItemsIdResponse.model_validate(self._request('GET', f'/items/{id}', None))

    def get_inventory_id(self, id: int) -> GetInventoryIdResponse:
        return GetInventoryIdResponse.model_validate(self._request('GET', f'/inventory/{id}', None))

    def get_payments_id(self, id: int) -> GetPaymentsIdResponse:
        return GetPaymentsIdResponse.model_validate(self._request('GET', f'/payments/{id}', None))

    def post_shipments(self, body: PostShipmentsRequest) -> PostShipmentsResponse:
        return PostShipmentsResponse.model_validate(self._request('POST', '/shipments', body))

    def get_shipments_id(self, id: int) -> GetShipmentsIdResponse:
        return GetShipmentsIdResponse.model_validate(self._request('GET', f'/shipments/{id}', None))

    def post_orders_id_ship(self, id: int, body: PostOrdersIdShipRequest) -> PostOrdersIdShipResponse:
        return PostOrdersIdShipResponse.model_validate(self._request('POST', f'/orders/{id}/ship', body))

    def options_customers(self) -> OptionsCustomersResponse:
        return OptionsCustomersResponse.model_validate(self._request('OPTIONS', '/customers', None))

    def options_products(self) -> OptionsProductsResponse:
        return OptionsProductsResponse.model_validate(self._request('OPTIONS', '/products', None))

    def options_orders(self) -> OptionsOrdersResponse:
        return OptionsOrdersResponse.model_validate(self._request('OPTIONS', '/orders', None))

    def options_items(self) -> OptionsItemsResponse:
        return OptionsItemsResponse.model_validate(self._request('OPTIONS', '/items', None))

    def options_inventory(self) -> OptionsInventoryResponse:
        return OptionsInventoryResponse.model_validate(self._request('OPTIONS', '/inventory', None))

    def options_payments(self) -> OptionsPaymentsResponse:
        return OptionsPaymentsResponse.model_validate(self._request('OPTIONS', '/payments', None))

    def options_shipments(self) -> OptionsShipmentsResponse:
        return OptionsShipmentsResponse.model_validate(self._request('OPTIONS', '/shipments', None))
