import re
import time

import chromadb
from chromadb.config import Settings

from roamwise.common import DATA, ROOT, jsonl, read_json
from roamwise.embedding import encoder

QUERY_TERMS = {
    "culture": ("museum", "art", "gallery", "history", "theater", "theatre", "library"),
    "outdoors": (
        "park",
        "garden",
        "nature",
        "outdoor",
        "walk",
        "waterfront",
        "campus",
        "university",
        "zoo",
        "aquarium",
    ),
    "lodging": ("hotel", "stay", "hostel", "lodging", "sleep", "accommodation"),
    "food": (
        "restaurant",
        "food",
        "eat",
        "coffee",
        "cafe",
        "bakery",
        "pizza",
        "dinner",
        "lunch",
        "breakfast",
        "seafood",
        "tea",
    ),
}


def inferred_category(query):
    tokens = set(re.findall(r"[a-z]+", query.casefold()))
    scores = {
        group: len(tokens.intersection(terms)) for group, terms in QUERY_TERMS.items()
    }
    return max(scores, key=scores.get) if max(scores.values()) else None


class Retriever:
    def __init__(self):
        self.dataset = read_json(DATA / "processed/manifest.json")
        self.index = read_json(DATA / "index-manifest.json")
        if self.dataset["dataset_id"] != self.index["dataset_id"]:
            raise ValueError("Dataset and index versions differ; rerun the pipeline")
        self.places = {x["place_id"]: x for x in jsonl(DATA / "processed/places.jsonl")}
        self.chunks = {x["chunk_id"]: x for x in jsonl(DATA / "processed/chunks.jsonl")}
        self.by_place = {}
        for chunk in self.chunks.values():
            self.by_place.setdefault(chunk["place_id"], []).append(chunk)
        config = read_json(ROOT / "config/pipeline.json")
        self.client = chromadb.PersistentClient(
            path=str(DATA / "index"), settings=Settings(anonymized_telemetry=False)
        )
        self.collection = self.client.get_collection(
            config["collection"], embedding_function=encoder()
        )
        if self.collection.count() != len(self.chunks):
            raise ValueError("Incomplete index; rerun the index container")
        # Warm the encoder so health means requests can be served, not just that a port is open.
        self.collection.query(query_texts=["Boston museum"], n_results=1)

    def search(self, query, city=None, category=None, top_k=5, method="semantic"):
        started = time.perf_counter()
        candidates = {
            pid: p
            for pid, p in self.places.items()
            if (not city or p["city"] == city)
            and (not category or p["category"] == category)
        }
        matches = []
        if method == "baseline":
            target_category = category or inferred_category(query)
            ranked = [
                p
                for p in candidates.values()
                if not target_category or p["category"] == target_category
            ]

            # Bayesian rating shrinks low-count 5-star places towards a fixed 4.0 prior.
            def rating_score(p):
                count = p["review_count"]
                return (count * (p["rating"] or 4.0) + 50 * 4.0) / (count + 50)

            ranked.sort(
                key=lambda p: (-rating_score(p), -p["review_count"], p["place_id"])
            )
            for place in ranked[:top_k]:
                chunks = self.by_place[place["place_id"]]
                evidence = [c for c in chunks if c["kind"] == "metadata"][:1] + [
                    c for c in chunks if c["kind"] == "review"
                ][:1]
                matches.append((place, rating_score(place), evidence))
        elif candidates:
            filters = []
            if city:
                filters.append({"city": city})
            if category:
                filters.append({"category": category})
            where = (
                {"$and": filters}
                if len(filters) > 1
                else filters[0]
                if filters
                else None
            )
            # Request a bounded pool, then collapse multiple review chunks from the same place.
            result = self.collection.query(
                query_texts=[query],
                n_results=min(max(top_k * 30, 80), self.collection.count()),
                where=where,
                include=["distances", "metadatas"],
            )
            grouped = {}
            for cid, distance, meta in zip(
                result["ids"][0], result["distances"][0], result["metadatas"][0]
            ):
                pid = meta["place_id"]
                if pid not in candidates:
                    continue
                score = max(-1.0, min(1.0, 1.0 - float(distance)))
                grouped.setdefault(pid, {"score": score, "evidence": []})
                if len(grouped[pid]["evidence"]) < 2:
                    grouped[pid]["evidence"].append(self.chunks[cid])
            ordered = sorted(
                grouped.items(), key=lambda item: (-item[1]["score"], item[0])
            )[:top_k]
            matches = [
                (candidates[pid], row["score"], row["evidence"]) for pid, row in ordered
            ]
        output = []
        context = []
        for rank, (place, score, evidence) in enumerate(matches, 1):
            citations = [
                {
                    "citation": f"{rank}.{i}",
                    **{
                        key: chunk[key]
                        for key in (
                            "chunk_id",
                            "kind",
                            "text",
                            "source_file",
                            "source_line",
                            "timestamp_ms",
                        )
                    },
                }
                for i, chunk in enumerate(evidence, 1)
            ]
            context.extend(
                f"[{c['citation']}] {place['name']} ({place['city']}): {c['text']}"
                for c in citations
            )
            output.append(
                {
                    **place,
                    "rank": rank,
                    "score": round(score, 5),
                    "evidence": citations,
                    "reason": f"Retrieved source material for {place['name']}, a {place['category']} place in {place['city']}.",
                }
            )
        return {
            "query": query,
            "method": method,
            "score_type": "cosine_similarity"
            if method == "semantic"
            else "bayesian_rating_1_to_5",
            "dataset_id": self.dataset["dataset_id"],
            "index_id": self.index["index_id"],
            "elapsed_ms": round((time.perf_counter() - started) * 1000, 2),
            "results": output,
            "context": "\n\n".join(context),
            "notice": "Historical data through September 2021. Check current hours, prices and availability. Similarity is not a match probability.",
        }
