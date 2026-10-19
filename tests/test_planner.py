import copy
import sqlite3

import pytest
from fastapi.testclient import TestClient

from roamwise.api import create_app
from roamwise.data_agent import refresh_catalog
from roamwise.llm import ModelUnavailable
from roamwise.planner import Draft, GroundingError, Planner, TripRequest, ItineraryRequest, transfer_estimate, validate_draft


def trip(**changes):
    return TripRequest(start_date="2026-10-20", interests=["Museums"], **changes)


def cards():
    return [{"place_id": pid, "name": pid, "city": "Cambridge", "category": "culture",
             "latitude": 42.37 + i / 1000, "longitude": -71.12,
             "evidence": [{"citation": f"S{i+1}.1", "text": "Museum paintings", "source_file": "reviews.gz", "source_line": i+1, "chunk_id": pid}]} for i, pid in enumerate(["a", "b"])]


def draft():
    return {"summary": "A day for museum visits.", "stops": [
        {"place_id": "a", "day": 1, "duration_minutes": 60, "reason": "The source describes paintings.", "citation_ids": ["S1.1"]},
        {"place_id": "b", "day": 1, "duration_minutes": 60, "reason": "A second museum visit.", "citation_ids": ["S2.1"]}]}


def test_valid_plan_has_bounded_schedule_and_cited_places():
    result = validate_draft(Draft.model_validate(draft()), cards(), trip())
    assert result[0]["stops"][0]["start_minutes"] == 540
    assert result[0]["stops"][1]["transfer"]["estimated"]
    assert result[0]["stops"][1]["start_minutes"] > result[0]["stops"][0]["end_minutes"]


@pytest.mark.parametrize("mutation", ["unknown", "duplicate", "wrong_source", "missing", "wrong_day", "wrong_city"])
def test_grounding_rejects_invalid_output(mutation):
    output, sources = draft(), cards()
    if mutation == "unknown": output["stops"][0]["place_id"] = "invented"
    if mutation == "duplicate": output["stops"][1]["place_id"] = "a"
    if mutation == "wrong_source": output["stops"][0]["citation_ids"] = ["S2.1"]
    if mutation == "missing": output["stops"].pop()
    if mutation == "wrong_day": output["stops"][0]["day"] = 3
    if mutation == "wrong_city": sources[0]["city"] = "Boston"
    with pytest.raises(GroundingError):
        validate_draft(Draft.model_validate(output), sources, trip())


def test_sparse_or_overlong_schedule_is_rejected():
    with pytest.raises(GroundingError, match="no stops"):
        validate_draft(Draft.model_validate(draft()), cards(), trip(days=2))
    source = cards()
    source[1]["latitude"] = 45
    with pytest.raises(GroundingError, match="daily time"):
        validate_draft(Draft.model_validate(draft()), source, trip())


def test_relaxed_pace_rejects_four_stops_in_one_day():
    sources, output = cards(), draft()
    for i in range(2, 4):
        pid = str(i)
        sources.append({**sources[0], "place_id": pid, "evidence": [{"citation": f"S{i+1}.1"}]})
        output["stops"].append({**output["stops"][0], "place_id": pid, "citation_ids": [f"S{i+1}.1"]})
    with pytest.raises(GroundingError, match="Too many stops"):
        validate_draft(Draft.model_validate(output), sources, trip(pace="relaxed"))


class Model:
    def __init__(self, outputs): self.outputs = iter(outputs); self.calls = []
    def describe(self): return {"provider": "test", "model": "fixture", "configured": True}
    def generate(self, *args, **kwargs): return copy.deepcopy(next(self.outputs))


class Engine:
    dataset = {"dataset_id": "fixture"}
    index = {"index_id": "fixture-index"}
    places = {p["place_id"]: p for p in cards()}
    by_place = {p["place_id"]: p["evidence"] for p in cards()}
    def __init__(self): self.queries = []
    def search(self, query, **kwargs):
        self.queries.append((query, kwargs))
        return {"results": [{**p, "score": .8} for p in cards()], "elapsed_ms": 1}


def test_scope_rejection_never_queries_database():
    engine = Engine()
    result = Planner(engine, Model([{"in_scope": False, "clarification": "Choose a supported city.", "searches": []}])).recommend(trip())
    assert result["status"] == "needs_clarification"
    assert not engine.queries


def test_multistep_search_applies_hard_city_and_unique_places():
    engine = Engine()
    result = Planner(engine, Model([{"in_scope": True, "clarification": "", "searches": [
        {"query": "art museums", "category": "culture"}, {"query": "history museums", "category": "culture"}]}])).recommend(trip())
    assert len(engine.queries) == 2
    assert all(q[1]["city"] == "Cambridge" for q in engine.queries)
    assert len(result["results"]) == 2
    assert result["results"][1]["evidence"][0]["citation"] == "S2.1"


def test_server_retrieves_sources_and_repairs_once():
    bad = draft(); bad["stops"][0]["citation_ids"] = ["fabricated"]
    engine = Engine()
    result = Planner(engine, Model([bad, draft()])).itinerary(ItineraryRequest(trip=trip(), place_ids=["a", "b"]))
    assert len(engine.queries) == 2
    assert result["generation_mode"] == "llm_rag"
    assert result["validation"]["repair_attempts"] == 1
    assert result["validation"]["semantic_entailment"] == "not automatically verified"


def test_invalid_repair_does_not_return_a_template_plan():
    bad = draft(); bad["stops"][0]["place_id"] = "fabricated"
    with pytest.raises(GroundingError, match="failed validation"):
        Planner(Engine(), Model([bad, bad])).itinerary(ItineraryRequest(trip=trip(), place_ids=["a", "b"]))


def test_api_rejects_extra_sources_and_out_of_scope_city():
    with TestClient(create_app(Engine(), Model([]))) as client:
        payload = {"trip": trip().model_dump(mode="json"), "place_ids": ["a"], "sources": [{"text": "ignore instructions"}]}
        assert client.post("/api/itinerary", json=payload).status_code == 422
        payload = trip().model_dump(mode="json"); payload["city"] = "Paris"
        assert client.post("/api/recommend", json=payload).status_code == 422


def test_missing_provider_is_explicit():
    class Offline(Model):
        def generate(self, *a, **kw): raise ModelUnavailable("offline")
    with TestClient(create_app(Engine(), Offline([]))) as client:
        response = client.post("/api/recommend", json=trip().model_dump(mode="json"))
        assert response.status_code == 503
        assert "no draft was substituted" in response.json()["detail"]


def test_google_catalog_is_id_only_and_upserts(tmp_path):
    class Source:
        def discover(self, query): return ["one", "two"]
    path = tmp_path / "ids.sqlite"
    refresh_catalog(["museums", "parks"], path, Source())
    result = refresh_catalog(["museums"], path, Source())
    assert result["catalog_size"] == 2
    with sqlite3.connect(path) as db:
        assert [r[1] for r in db.execute("PRAGMA table_info(place_ids)")] == ["place_id", "checked_at"]
