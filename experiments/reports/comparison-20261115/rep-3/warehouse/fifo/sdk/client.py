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

class GetWarehousesResponse(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    items: list[JsonValue] = Field(..., alias='items')
    total: int = Field(..., alias='total')
    links: list[dict[str, JsonValue]] = Field(..., alias='links')

class OptionsWarehousesResponse(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    links: list[dict[str, JsonValue]] = Field(..., alias='links')

class GetLocationsResponse(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    items: list[JsonValue] = Field(..., alias='items')
    total: int = Field(..., alias='total')
    links: list[dict[str, JsonValue]] = Field(..., alias='links')

class OptionsLocationsResponse(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    links: list[dict[str, JsonValue]] = Field(..., alias='links')

class GetStockResponse(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    items: list[JsonValue] = Field(..., alias='items')
    total: int = Field(..., alias='total')
    links: list[dict[str, JsonValue]] = Field(..., alias='links')

class OptionsStockResponse(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    links: list[dict[str, JsonValue]] = Field(..., alias='links')

class GetTransfersResponse(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    items: list[JsonValue] = Field(..., alias='items')
    total: int = Field(..., alias='total')
    links: list[dict[str, JsonValue]] = Field(..., alias='links')

class OptionsTransfersResponse(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    links: list[dict[str, JsonValue]] = Field(..., alias='links')

class GetReservationsResponse(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    items: list[JsonValue] = Field(..., alias='items')
    total: int = Field(..., alias='total')
    links: list[dict[str, JsonValue]] = Field(..., alias='links')

class OptionsReservationsResponse(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    links: list[dict[str, JsonValue]] = Field(..., alias='links')

class GetFulfillmentsResponse(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    items: list[JsonValue] = Field(..., alias='items')
    total: int = Field(..., alias='total')
    links: list[dict[str, JsonValue]] = Field(..., alias='links')

class OptionsFulfillmentsResponse(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    links: list[dict[str, JsonValue]] = Field(..., alias='links')

class GetReturnsResponse(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    items: list[JsonValue] = Field(..., alias='items')
    total: int = Field(..., alias='total')
    links: list[dict[str, JsonValue]] = Field(..., alias='links')

class OptionsReturnsResponse(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    links: list[dict[str, JsonValue]] = Field(..., alias='links')

class PostWarehousesRequest(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    name: str = Field(..., alias='name')

class PostWarehousesResponse(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    id: int = Field(..., alias='id')
    name: str = Field(..., alias='name')
    status: str = Field(..., alias='status')
    links: list[dict[str, JsonValue]] = Field(..., alias='links')

class PostLocationsRequest(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    warehouse_id: int = Field(..., alias='warehouse_id')
    name: str = Field(..., alias='name')

class PostLocationsResponse(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    id: int = Field(..., alias='id')
    warehouse_id: int = Field(..., alias='warehouse_id')
    name: str = Field(..., alias='name')
    status: str = Field(..., alias='status')
    links: list[dict[str, JsonValue]] = Field(..., alias='links')

class PostStockRequest(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    location_id: int = Field(..., alias='location_id')
    quantity: int = Field(..., alias='quantity')

class PostStockResponse(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    id: int = Field(..., alias='id')
    location_id: int = Field(..., alias='location_id')
    quantity: int = Field(..., alias='quantity')
    status: str = Field(..., alias='status')
    links: list[dict[str, JsonValue]] = Field(..., alias='links')

class PostTransfersRequest(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    stock_id: int = Field(..., alias='stock_id')
    location_id: int = Field(..., alias='location_id')
    quantity: int = Field(..., alias='quantity')

class PostTransfersResponse(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    id: int = Field(..., alias='id')
    stock_id: int = Field(..., alias='stock_id')
    location_id: int = Field(..., alias='location_id')
    quantity: int = Field(..., alias='quantity')
    status: str = Field(..., alias='status')
    links: list[dict[str, JsonValue]] = Field(..., alias='links')

class GetWarehousesIdResponse(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    id: int = Field(..., alias='id')
    name: str = Field(..., alias='name')
    status: str = Field(..., alias='status')
    links: list[dict[str, JsonValue]] = Field(..., alias='links')

class GetLocationsIdResponse(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    id: int = Field(..., alias='id')
    warehouse_id: int = Field(..., alias='warehouse_id')
    name: str = Field(..., alias='name')
    status: str = Field(..., alias='status')
    links: list[dict[str, JsonValue]] = Field(..., alias='links')

class GetStockIdResponse(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    id: int = Field(..., alias='id')
    location_id: int = Field(..., alias='location_id')
    quantity: int = Field(..., alias='quantity')
    status: str = Field(..., alias='status')
    links: list[dict[str, JsonValue]] = Field(..., alias='links')

class GetTransfersIdResponse(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    id: int = Field(..., alias='id')
    stock_id: int = Field(..., alias='stock_id')
    location_id: int = Field(..., alias='location_id')
    quantity: int = Field(..., alias='quantity')
    status: str = Field(..., alias='status')
    links: list[dict[str, JsonValue]] = Field(..., alias='links')

class PatchStockIdRequest(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    quantity: int = Field(..., alias='quantity')

class PatchStockIdResponse(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    id: int = Field(..., alias='id')
    location_id: int = Field(..., alias='location_id')
    quantity: int = Field(..., alias='quantity')
    status: str = Field(..., alias='status')
    links: list[dict[str, JsonValue]] = Field(..., alias='links')

class PostReservationsRequest(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    stock_id: int = Field(..., alias='stock_id')
    quantity: int = Field(..., alias='quantity')

class PostReservationsResponse(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    id: int = Field(..., alias='id')
    stock_id: int = Field(..., alias='stock_id')
    quantity: int = Field(..., alias='quantity')
    status: str = Field(..., alias='status')
    links: list[dict[str, JsonValue]] = Field(..., alias='links')

class PostFulfillmentsRequest(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    reservation_id: int = Field(..., alias='reservation_id')

class PostFulfillmentsResponse(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    id: int = Field(..., alias='id')
    reservation_id: int = Field(..., alias='reservation_id')
    status: str = Field(..., alias='status')
    links: list[dict[str, JsonValue]] = Field(..., alias='links')

class PostReturnsRequest(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    fulfillment_id: int = Field(..., alias='fulfillment_id')
    quantity: int = Field(..., alias='quantity')

class PostReturnsResponse(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    id: int = Field(..., alias='id')
    fulfillment_id: int = Field(..., alias='fulfillment_id')
    quantity: int = Field(..., alias='quantity')
    status: str = Field(..., alias='status')
    links: list[dict[str, JsonValue]] = Field(..., alias='links')

class GetReservationsIdResponse(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    id: int = Field(..., alias='id')
    stock_id: int = Field(..., alias='stock_id')
    quantity: int = Field(..., alias='quantity')
    status: str = Field(..., alias='status')
    links: list[dict[str, JsonValue]] = Field(..., alias='links')

class PostReservationsIdFulfillRequest(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)

class PostReservationsIdFulfillResponse(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    id: int = Field(..., alias='id')
    stock_id: int = Field(..., alias='stock_id')
    quantity: int = Field(..., alias='quantity')
    status: str = Field(..., alias='status')
    links: list[dict[str, JsonValue]] = Field(..., alias='links')

class PostReservationsIdReturnRequest(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)

class PostReservationsIdReturnResponse(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    id: int = Field(..., alias='id')
    stock_id: int = Field(..., alias='stock_id')
    quantity: int = Field(..., alias='quantity')
    status: str = Field(..., alias='status')
    links: list[dict[str, JsonValue]] = Field(..., alias='links')

class GetFulfillmentsIdResponse(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    id: int = Field(..., alias='id')
    reservation_id: int = Field(..., alias='reservation_id')
    status: str = Field(..., alias='status')
    links: list[dict[str, JsonValue]] = Field(..., alias='links')

class GetReturnsIdResponse(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    id: int = Field(..., alias='id')
    fulfillment_id: int = Field(..., alias='fulfillment_id')
    quantity: int = Field(..., alias='quantity')
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

    def get_warehouses(self, *, cursor: int | None = None, limit: int | None = None) -> GetWarehousesResponse:
        return GetWarehousesResponse.model_validate(self._request('GET', '/warehouses', None, params={key: value for key, value in {'cursor': cursor, 'limit': limit}.items() if value is not None}))

    def iter_get_warehouses_pages(self, max_pages: int = 100) -> Iterator[GetWarehousesResponse]:
        for data in self._pages('/warehouses', max_pages):
            yield GetWarehousesResponse.model_validate(data)

    def options_warehouses(self) -> OptionsWarehousesResponse:
        return OptionsWarehousesResponse.model_validate(self._request('OPTIONS', '/warehouses', None))

    def get_locations(self, *, cursor: int | None = None, limit: int | None = None) -> GetLocationsResponse:
        return GetLocationsResponse.model_validate(self._request('GET', '/locations', None, params={key: value for key, value in {'cursor': cursor, 'limit': limit}.items() if value is not None}))

    def iter_get_locations_pages(self, max_pages: int = 100) -> Iterator[GetLocationsResponse]:
        for data in self._pages('/locations', max_pages):
            yield GetLocationsResponse.model_validate(data)

    def options_locations(self) -> OptionsLocationsResponse:
        return OptionsLocationsResponse.model_validate(self._request('OPTIONS', '/locations', None))

    def get_stock(self, *, cursor: int | None = None, limit: int | None = None) -> GetStockResponse:
        return GetStockResponse.model_validate(self._request('GET', '/stock', None, params={key: value for key, value in {'cursor': cursor, 'limit': limit}.items() if value is not None}))

    def iter_get_stock_pages(self, max_pages: int = 100) -> Iterator[GetStockResponse]:
        for data in self._pages('/stock', max_pages):
            yield GetStockResponse.model_validate(data)

    def options_stock(self) -> OptionsStockResponse:
        return OptionsStockResponse.model_validate(self._request('OPTIONS', '/stock', None))

    def get_transfers(self, *, cursor: int | None = None, limit: int | None = None) -> GetTransfersResponse:
        return GetTransfersResponse.model_validate(self._request('GET', '/transfers', None, params={key: value for key, value in {'cursor': cursor, 'limit': limit}.items() if value is not None}))

    def iter_get_transfers_pages(self, max_pages: int = 100) -> Iterator[GetTransfersResponse]:
        for data in self._pages('/transfers', max_pages):
            yield GetTransfersResponse.model_validate(data)

    def options_transfers(self) -> OptionsTransfersResponse:
        return OptionsTransfersResponse.model_validate(self._request('OPTIONS', '/transfers', None))

    def get_reservations(self, *, cursor: int | None = None, limit: int | None = None) -> GetReservationsResponse:
        return GetReservationsResponse.model_validate(self._request('GET', '/reservations', None, params={key: value for key, value in {'cursor': cursor, 'limit': limit}.items() if value is not None}))

    def iter_get_reservations_pages(self, max_pages: int = 100) -> Iterator[GetReservationsResponse]:
        for data in self._pages('/reservations', max_pages):
            yield GetReservationsResponse.model_validate(data)

    def options_reservations(self) -> OptionsReservationsResponse:
        return OptionsReservationsResponse.model_validate(self._request('OPTIONS', '/reservations', None))

    def get_fulfillments(self, *, cursor: int | None = None, limit: int | None = None) -> GetFulfillmentsResponse:
        return GetFulfillmentsResponse.model_validate(self._request('GET', '/fulfillments', None, params={key: value for key, value in {'cursor': cursor, 'limit': limit}.items() if value is not None}))

    def iter_get_fulfillments_pages(self, max_pages: int = 100) -> Iterator[GetFulfillmentsResponse]:
        for data in self._pages('/fulfillments', max_pages):
            yield GetFulfillmentsResponse.model_validate(data)

    def options_fulfillments(self) -> OptionsFulfillmentsResponse:
        return OptionsFulfillmentsResponse.model_validate(self._request('OPTIONS', '/fulfillments', None))

    def get_returns(self, *, cursor: int | None = None, limit: int | None = None) -> GetReturnsResponse:
        return GetReturnsResponse.model_validate(self._request('GET', '/returns', None, params={key: value for key, value in {'cursor': cursor, 'limit': limit}.items() if value is not None}))

    def iter_get_returns_pages(self, max_pages: int = 100) -> Iterator[GetReturnsResponse]:
        for data in self._pages('/returns', max_pages):
            yield GetReturnsResponse.model_validate(data)

    def options_returns(self) -> OptionsReturnsResponse:
        return OptionsReturnsResponse.model_validate(self._request('OPTIONS', '/returns', None))

    def post_warehouses(self, body: PostWarehousesRequest) -> PostWarehousesResponse:
        return PostWarehousesResponse.model_validate(self._request('POST', '/warehouses', body))

    def post_locations(self, body: PostLocationsRequest) -> PostLocationsResponse:
        return PostLocationsResponse.model_validate(self._request('POST', '/locations', body))

    def post_stock(self, body: PostStockRequest) -> PostStockResponse:
        return PostStockResponse.model_validate(self._request('POST', '/stock', body))

    def post_transfers(self, body: PostTransfersRequest) -> PostTransfersResponse:
        return PostTransfersResponse.model_validate(self._request('POST', '/transfers', body))

    def get_warehouses_id(self, id: int) -> GetWarehousesIdResponse:
        return GetWarehousesIdResponse.model_validate(self._request('GET', f'/warehouses/{id}', None))

    def get_locations_id(self, id: int) -> GetLocationsIdResponse:
        return GetLocationsIdResponse.model_validate(self._request('GET', f'/locations/{id}', None))

    def get_stock_id(self, id: int) -> GetStockIdResponse:
        return GetStockIdResponse.model_validate(self._request('GET', f'/stock/{id}', None))

    def get_transfers_id(self, id: int) -> GetTransfersIdResponse:
        return GetTransfersIdResponse.model_validate(self._request('GET', f'/transfers/{id}', None))

    def patch_stock_id(self, id: int, body: PatchStockIdRequest) -> PatchStockIdResponse:
        return PatchStockIdResponse.model_validate(self._request('PATCH', f'/stock/{id}', body))

    def post_reservations(self, body: PostReservationsRequest) -> PostReservationsResponse:
        return PostReservationsResponse.model_validate(self._request('POST', '/reservations', body))

    def post_fulfillments(self, body: PostFulfillmentsRequest) -> PostFulfillmentsResponse:
        return PostFulfillmentsResponse.model_validate(self._request('POST', '/fulfillments', body))

    def post_returns(self, body: PostReturnsRequest) -> PostReturnsResponse:
        return PostReturnsResponse.model_validate(self._request('POST', '/returns', body))

    def get_reservations_id(self, id: int) -> GetReservationsIdResponse:
        return GetReservationsIdResponse.model_validate(self._request('GET', f'/reservations/{id}', None))

    def post_reservations_id_fulfill(self, id: int, body: PostReservationsIdFulfillRequest) -> PostReservationsIdFulfillResponse:
        return PostReservationsIdFulfillResponse.model_validate(self._request('POST', f'/reservations/{id}/fulfill', body))

    def post_reservations_id_return(self, id: int, body: PostReservationsIdReturnRequest) -> PostReservationsIdReturnResponse:
        return PostReservationsIdReturnResponse.model_validate(self._request('POST', f'/reservations/{id}/return', body))

    def get_fulfillments_id(self, id: int) -> GetFulfillmentsIdResponse:
        return GetFulfillmentsIdResponse.model_validate(self._request('GET', f'/fulfillments/{id}', None))

    def get_returns_id(self, id: int) -> GetReturnsIdResponse:
        return GetReturnsIdResponse.model_validate(self._request('GET', f'/returns/{id}', None))
