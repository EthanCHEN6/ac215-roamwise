import pytest
from roamwise.common import read_json, ROOT
from roamwise.preprocess import (
    normalized_place,
    word_chunks,
    clean_text,
    city_for,
    category_for,
)

CONFIG = read_json(ROOT / "config/pipeline.json")


def place(**changes):
    return {
        "gmap_id": "0x1:0x2",
        "name": "Sample Museum",
        "address": "10 Main St, Cambridge, MA 02138",
        "latitude": 42.37,
        "longitude": -71.12,
        "avg_rating": 4.4,
        "num_of_reviews": 30,
        "category": ["Art museum"],
        **changes,
    }


def test_geography_and_closed_filters():
    assert normalized_place(place(), CONFIG)["city"] == "Cambridge"
    assert normalized_place(place(latitude=43.1), CONFIG) is None
    assert normalized_place(place(state="Permanently closed"), CONFIG) is None
    assert (
        normalized_place(place(address="10 Main St, Worcester, MA 01608"), CONFIG)
        is None
    )
    assert normalized_place(place(latitude=float("nan")), CONFIG) is None


def test_neighborhood_and_campus_are_explicit():
    assert city_for("Cafe, 10 Main St, Allston, MA 02134", "Cafe", CONFIG) == "Boston"
    assert city_for("Cambridge, MA", "Harvard University", CONFIG) == "Cambridge"
    assert category_for(["University"], "Harvard University") == "outdoors"
    assert category_for(["Parking garage"]) is None
    assert category_for(["Art museum", "Cafe"]) == "culture"


def test_missing_fields_are_not_invented():
    result = normalized_place(place(avg_rating=None), CONFIG)
    assert result["price"] is None
    assert result["historical_hours"] is None
    assert result["rating"] is None


def test_chunks_cover_text_and_overlap_without_empty_tail():
    words = [str(i) for i in range(215)]
    chunks = list(word_chunks(" ".join(words), 100, 20))
    assert [len(c.split()) for c in chunks] == [100, 100, 55]
    assert chunks[0].split()[-20:] == chunks[1].split()[:20]
    assert set(" ".join(chunks).split()) == set(words)
    assert list(word_chunks("")) == []
    with pytest.raises(ValueError):
        list(word_chunks("text", 20, 20))


def test_contact_redaction():
    text = clean_text("Email test@example.com\nCall 617-555-1234")
    assert "test@example.com" not in text
    assert "617-555-1234" not in text
    assert "[email removed]" in text
