import pytest
from fastapi.testclient import TestClient
from main import app
from src.services.price_tracker_db import get_tracked_flights, add_tracked_flights


@pytest.fixture
def client():
    with TestClient(app) as client:
        yield client


def test_home_route(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello"}


def test_about_route(client):
    response = client.get("/about")
    assert response.status_code == 200
    assert response.json() == {"message": "This is the about page."}


def test_add_tracked_flights():
    chat_id = 123456
    flights = [
        {
            "from_city": "MOW",
            "to_city": "BKK",
            "date": "2025-08-01",
            "flight_number": "SU123",
            "airline": "Aeroflot",
            "departure_time": "2025-08-01T10:00:00",
            "arrival_time": "2025-08-01T18:00:00",
            "transfers": 0,
            "current_price": 15000
        }
    ]
    add_tracked_flights(chat_id, flights)
    tracked = get_tracked_flights()
    assert any(f["chat_id"] == chat_id and f["flight_number"] == "SU123" for f in tracked)
