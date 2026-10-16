from roamwise.retrieval import Retriever, inferred_category
from roamwise.ingest import download
from roamwise.common import sha256
import pytest


def test_cached_source_is_checked(tmp_path):
    source = tmp_path / "source.gz"
    source.write_bytes(b"original")
    expected = sha256(source)
    assert download({"sha256": expected}, source) == expected
    source.write_bytes(b"changed")
    with pytest.raises(ValueError, match="checksum mismatch"):
        download({"sha256": expected}, source)


class Collection:
    def count(self):
        return 3

    def query(self, **kwargs):
        self.filters = kwargs["where"]
        return {
            "ids": [["a1", "a2", "b1"]],
            "distances": [[0.1, 0.2, 0.3]],
            "metadatas": [[{"place_id": "a"}, {"place_id": "a"}, {"place_id": "b"}]],
        }


def retriever():
    engine = Retriever.__new__(Retriever)
    engine.dataset = {"dataset_id": "test"}
    engine.index = {"index_id": "test-index"}
    engine.places = {
        pid: {
            "place_id": pid,
            "name": pid,
            "city": "Boston",
            "category": "culture",
            "review_count": 20,
            "rating": 4.5,
        }
        for pid in ("a", "b")
    }
    engine.chunks = {
        cid: {
            "chunk_id": cid,
            "kind": "review",
            "text": "museum exhibits",
            "source_file": "reviews.gz",
            "source_line": i,
            "timestamp_ms": None,
        }
        for i, cid in enumerate(("a1", "a2", "b1"), 1)
    }
    engine.collection = Collection()
    return engine


def test_semantic_results_deduplicate_places_and_keep_citations():
    engine = retriever()
    result = engine.search("museum", city="Boston", category="culture")
    assert [x["place_id"] for x in result["results"]] == ["a", "b"]
    assert len(result["results"][0]["evidence"]) == 2
    assert result["results"][0]["score"] == 0.9
    assert "[1.1]" in result["context"]
    assert engine.collection.filters == {
        "$and": [{"city": "Boston"}, {"category": "culture"}]
    }


def test_empty_filter_does_not_query_index():
    engine = retriever()
    assert engine.search("museum", city="Somerville")["results"] == []
    assert not hasattr(engine.collection, "filters")


def test_baseline_query_category():
    assert inferred_category("coffee and breakfast") == "food"
    assert inferred_category("zzzz") is None
