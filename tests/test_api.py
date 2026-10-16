import pytest
from fastapi.testclient import TestClient
from roamwise.api import create_app


class Engine:
    dataset = {"dataset_id": "test-v1"}
    index = {"index_id": "index-v1"}
    places = {"known": {"name": "Known place"}}

    def search(self, **request):
        self.request = request
        return {"results": [], "elapsed_ms": 1, "dataset_id": "test-v1"}


@pytest.fixture
def client():
    with TestClient(create_app(Engine())) as client:
        yield client


@pytest.mark.parametrize(
    "body",
    [
        {"query": "   "},
        {"query": "museum", "top_k": 0},
        {"query": "museum", "top_k": 11},
        {"query": "museum", "city": "Paris"},
        {"query": "museum", "method": "unknown"},
        {"query": "x" * 501},
        {"query": "museum", "unexpected": "field"},
    ],
)
def test_invalid_search_is_rejected(client, body):
    assert client.post("/api/search", json=body).status_code == 422


def test_filters_reach_engine_and_empty_result_is_valid(client):
    response = client.post(
        "/api/search",
        json={
            "query": " art museum ",
            "city": "Cambridge",
            "category": "culture",
            "top_k": 3,
        },
    )
    assert response.status_code == 200
    assert response.json()["results"] == []
    assert client.app.state.engine.request == {
        "query": "art museum",
        "city": "Cambridge",
        "category": "culture",
        "top_k": 3,
        "method": "semantic",
    }


def test_health_details_and_unknown_place(client):
    assert client.get("/api/health").json()["status"] == "ok"
    assert client.get("/api/places/known").status_code == 200
    assert client.get("/api/places/missing").status_code == 404
