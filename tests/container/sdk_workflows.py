"""Trusted live workflow checks. Executed only in the restricted validator container."""

import importlib
import inspect
import os
import socket
import subprocess
import sys
import time

import pytest

sys.path.insert(0, "/artifacts")
client = importlib.import_module("client")
KIND = os.environ["SDK_KIND"]


@pytest.fixture
def sdk():
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    process = subprocess.Popen(
        [sys.executable, "-m", "targets.service", KIND, "--port", str(port)],
        cwd="/target",
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        for _ in range(100):
            assert process.poll() is None, "Disposable target failed to start"
            try:
                with socket.create_connection(("127.0.0.1", port), timeout=0.1):
                    break
            except OSError:
                time.sleep(0.02)
        else:
            pytest.fail("Disposable target startup timed out")
        with client.Client(f"http://127.0.0.1:{port}") as instance:
            yield instance
    finally:
        process.terminate()
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=3)


def call(sdk, method, body=None, **kwargs):
    operation = getattr(sdk, method)
    if "body" in inspect.signature(operation).parameters:
        model = "".join(part.capitalize() for part in method.split("_")) + "Request"
        kwargs["body"] = getattr(client, model).model_validate(body or {})
    return operation(**kwargs)


def test_live_creation_reads_and_pagination(sdk):
    collection = (
        "customers"
        if KIND == "ecommerce"
        else (
            "warehouses"
            if KIND == "warehouse"
            else "v2_accounts"
            if KIND == "complex"
            else "accounts"
        )
    )
    for index in range(5):
        data = {"name": f"record-{index}"}
        if KIND == "complex":
            data["profile"] = {"region": "local"}
        created = call(sdk, "post_" + collection, data)
        assert created.id == index + 1
    pages = list(getattr(sdk, "iter_get_" + collection + "_pages")())
    assert [item["id"] for page in pages for item in page.items] == [1, 2, 3, 4, 5]
    second = getattr(sdk, "get_" + collection)(cursor=2)
    assert second.items[0]["id"] == 3


def test_live_resource_workflow(sdk):
    if KIND == "ecommerce":
        call(sdk, "post_customers", {"name": "customer"})
        call(sdk, "post_products", {"name": "product", "quantity": 10})
        call(sdk, "post_orders", {"customer_id": 1})
        call(sdk, "post_items", {"order_id": 1, "product_id": 1, "quantity": 1})
        call(sdk, "post_inventory", {"product_id": 1, "quantity": 10})
        assert call(sdk, "post_orders_id_reserve", id=1).status == "reserved"
        call(sdk, "post_payments", {"order_id": 1, "amount": 5.0})
        assert call(sdk, "post_orders_id_pay", id=1).status == "paid"
        call(sdk, "post_shipments", {"order_id": 1})
        assert call(sdk, "post_orders_id_ship", id=1).status == "shipped"
    elif KIND == "subscriptions":
        call(sdk, "post_accounts", {"name": "account"})
        call(sdk, "post_plans", {"name": "plan", "amount": 5.0})
        call(sdk, "post_subscriptions", {"account_id": 1, "plan_id": 1})
        assert call(sdk, "post_subscriptions_id_activate", id=1).status == "active"
        assert call(sdk, "post_subscriptions_id_renew", id=1).status == "active"
        call(sdk, "post_invoices", {"subscription_id": 1, "amount": 5.0})
        call(sdk, "post_payments", {"invoice_id": 1, "amount": 5.0})
        assert call(sdk, "post_subscriptions_id_cancel", id=1).status == "cancelled"
    elif KIND == "warehouse":
        call(sdk, "post_warehouses", {"name": "warehouse"})
        call(sdk, "post_locations", {"warehouse_id": 1, "name": "location"})
        call(sdk, "post_stock", {"location_id": 1, "quantity": 10})
        call(sdk, "post_transfers", {"stock_id": 1, "location_id": 1, "quantity": 1})
        call(sdk, "post_reservations", {"stock_id": 1, "quantity": 1})
        assert call(sdk, "post_reservations_id_fulfill", id=1).status == "fulfilled"
        call(sdk, "post_fulfillments", {"reservation_id": 1})
        call(sdk, "post_returns", {"fulfillment_id": 1, "quantity": 1})
        assert call(sdk, "post_reservations_id_return", id=1).status == "returned"
        assert call(sdk, "patch_stock_id", {"quantity": 20}, id=1).quantity == 20
    else:
        # Ambiguous configuration is deliberately outside the observed contract.
        created = call(sdk, "post_v2_accounts", {"name": "account", "profile": {}})
        assert call(sdk, "get_v2_accounts_id", id=created.id).id == created.id


def test_live_status_error(sdk):
    path = "/v2/accounts/99999" if KIND == "complex" else "/missing/99999"
    with pytest.raises(client.APIError) as caught:
        sdk._request("GET", path)
    assert caught.value.status == 404
