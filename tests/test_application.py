from datetime import datetime

import pytest

GET_ENDPOINTS = [
    ("/clients", 200),
    ("/clients/1", 200),
]


@pytest.mark.parametrize(
    "path, status",
    [
        ("/clients", 200),
        ("/clients/1", 200),
    ],
)
def test_get_endpoints(client, sample_data, path, status):
    rv = client.get(path)
    assert rv.status_code == status


def test_create_client(client):
    payload = {
        "name": "Petr",
        "surname": "Sidorov",
        "credit_card": "5555666677778888",
        "car_number": "B222BB",
    }
    rv = client.post("/clients", json=payload)
    assert rv.status_code == 201

    data = rv.get_json()
    assert data["name"] == payload["name"]
    assert data["surname"] == payload["surname"]
    assert "id" in data


def test_create_parking(client):
    payload = {"address": "Prospekt 10", "count_places": 5}
    rv = client.post("/parkings", json=payload)
    assert rv.status_code == 201
    data = rv.get_json()
    assert data["address"] == payload["address"]
    assert data["count_places"] == 5
    assert data["count_available_places"] == 5
    assert data["opened"] is True


@pytest.mark.parking
def test_enter_parking(client, sample_data):
    rv_c = client.post("/clients", json={"name": "Anna", "surname": "Ivanova"})
    assert rv_c.status_code == 201
    cid = rv_c.get_json()["id"]
    rv_p = client.post("/parkings", json={"address": "Pushkina 5", "count_places": 2})
    assert rv_p.status_code == 201
    pid = rv_p.get_json()["id"]

    rv_enter = client.post(
        "/client_parkings", json={"client_id": cid, "parking_id": pid}
    )
    assert rv_enter.status_code == 201
    entry = rv_enter.get_json()
    assert entry["client_id"] == cid
    assert entry["parking_id"] == pid
    assert entry.get("time_in") is not None


@pytest.mark.parking
def test_exit_parking(client):
    rv_c = client.post(
        "/clients",
        json={"name": "Max", "surname": "Kovalenko", "credit_card": "9999000011112222"},
    )
    cid = rv_c.get_json()["id"]
    rv_p = client.post("/parkings", json={"address": "Test 7", "count_places": 1})
    pid = rv_p.get_json()["id"]

    rv_enter = client.post(
        "/client_parkings", json={"client_id": cid, "parking_id": pid}
    )
    assert rv_enter.status_code == 201
    entry = rv_enter.get_json()
    ep_id = entry["id"]

    rv_exit = client.delete(
        "/client_parkings", json={"client_id": cid, "parking_id": pid}
    )
    assert rv_exit.status_code == 200 or rv_exit.status_code == 204
