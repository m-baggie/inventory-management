"""
Tests for restocking order endpoints.
"""
import pytest
from datetime import date, timedelta

import main as main_module


@pytest.fixture(autouse=True)
def reset_restocking_state():
    """Reset module-level restocking state before each test for isolation."""
    main_module.restocking_orders.clear()
    main_module.restocking_order_counter = 0
    yield


SAMPLE_ITEM = {
    "sku": "WDG-001",
    "name": "Industrial Widget Type A",
    "quantity": 450,
    "unit_cost": 14.50,
}

SAMPLE_PAYLOAD = {"items": [SAMPLE_ITEM]}


class TestGetRestockingOrders:
    def test_get_empty_restocking_orders(self, client):
        response = client.get("/api/restocking-orders")
        assert response.status_code == 200
        assert response.json() == []

    def test_created_orders_appear_in_get(self, client):
        client.post("/api/restocking-orders", json=SAMPLE_PAYLOAD)
        response = client.get("/api/restocking-orders")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["items"][0]["sku"] == "WDG-001"


class TestCreateRestockingOrder:
    def test_create_restocking_order_status_201(self, client):
        response = client.post("/api/restocking-orders", json=SAMPLE_PAYLOAD)
        assert response.status_code == 201

    def test_create_restocking_order_fields(self, client):
        response = client.post("/api/restocking-orders", json=SAMPLE_PAYLOAD)
        data = response.json()
        assert data["status"] == "Restocking"
        assert data["id"].startswith("RST-")
        assert len(data["items"]) == 1
        assert data["items"][0]["sku"] == "WDG-001"

    def test_restocking_order_id_format(self, client):
        response = client.post("/api/restocking-orders", json=SAMPLE_PAYLOAD)
        order_id = response.json()["id"]
        parts = order_id.split("-")
        assert parts[0] == "RST"
        assert len(parts[1]) == 4  # year
        assert len(parts[2]) == 4  # zero-padded counter

    def test_restocking_order_lead_time(self, client):
        response = client.post("/api/restocking-orders", json=SAMPLE_PAYLOAD)
        data = response.json()
        order_date = date.fromisoformat(data["order_date"])
        expected = date.fromisoformat(data["expected_delivery"])
        assert (expected - order_date).days == 14

    def test_total_value_single_item(self, client):
        response = client.post("/api/restocking-orders", json=SAMPLE_PAYLOAD)
        data = response.json()
        expected_total = round(450 * 14.50, 2)
        assert data["total_value"] == expected_total

    def test_total_value_multi_item(self, client):
        payload = {
            "items": [
                {"sku": "WDG-001", "name": "Widget A", "quantity": 100, "unit_cost": 14.50},
                {"sku": "BRG-102", "name": "Bearing", "quantity": 50, "unit_cost": 38.00},
            ]
        }
        response = client.post("/api/restocking-orders", json=payload)
        data = response.json()
        expected_total = round(100 * 14.50 + 50 * 38.00, 2)
        assert data["total_value"] == expected_total

    def test_create_order_with_notes(self, client):
        payload = {**SAMPLE_PAYLOAD, "notes": "Urgent restock needed"}
        response = client.post("/api/restocking-orders", json=payload)
        assert response.json()["notes"] == "Urgent restock needed"

    def test_create_order_empty_items_returns_422(self, client):
        response = client.post("/api/restocking-orders", json={"items": []})
        assert response.status_code == 422

    def test_create_order_missing_items_field_returns_422(self, client):
        response = client.post("/api/restocking-orders", json={})
        assert response.status_code == 422
