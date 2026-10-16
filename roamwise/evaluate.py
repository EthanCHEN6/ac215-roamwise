"""A fixed smoke benchmark. Category labels are proxies, not human relevance labels."""

import os
import statistics
import time
import httpx

from roamwise.common import EVIDENCE, ROOT, log, now, read_json, sha256, write_json


def main():
    base = os.getenv("API_URL", "http://api:8000")
    queries_path = ROOT / "evaluation/queries.json"
    queries = read_json(queries_path)
    rows = []
    with httpx.Client(base_url=base, timeout=120) as client:
        status = client.get("/api/status")
        status.raise_for_status()
        for method in ("baseline", "semantic"):
            for case in queries:
                request = {
                    "query": case["query"],
                    "city": case["city"],
                    "method": method,
                    "top_k": 5,
                }
                start = time.perf_counter()
                response = client.post("/api/search", json=request)
                response.raise_for_status()
                result = response.json()
                hits = sum(
                    p["category"] == case["expected_category"]
                    for p in result["results"]
                )
                rows.append(
                    {
                        "query_id": case["id"],
                        "request": request,
                        "expected_category": case["expected_category"],
                        "category_hits_at_5": hits / 5,
                        "returned": len(result["results"]),
                        "duplicate_places": len(result["results"])
                        - len({p["place_id"] for p in result["results"]}),
                        "http_ms": round((time.perf_counter() - start) * 1000, 2),
                        "results": [
                            {
                                k: p[k]
                                for k in (
                                    "place_id",
                                    "name",
                                    "category",
                                    "city",
                                    "score",
                                )
                            }
                            for p in result["results"]
                        ],
                    }
                )
        example_input = {
            "query": "art museum with paintings near Harvard",
            "city": "Cambridge",
            "top_k": 3,
            "method": "semantic",
        }
        response = client.post("/api/search", json=example_input)
        response.raise_for_status()
        example = response.json()
        # Keep the checked-in evidence excerpt short; full context remains available through the API.
        for place in example["results"]:
            for citation in place["evidence"]:
                citation["text"] = " ".join(citation["text"].split()[:25])
        example["context"] = "\n\n".join(
            f"[{c['citation']}] {p['name']}: {c['text']}"
            for p in example["results"]
            for c in p["evidence"]
        )
        example["evidence_note"] = (
            "Source excerpts shortened to at most 25 words for this saved example."
        )
        write_json(EVIDENCE / "sample-input.json", example_input)
        write_json(EVIDENCE / "sample-output.json", example)
    summary = {}
    for method in ("baseline", "semantic"):
        selected = [r for r in rows if r["request"]["method"] == method]
        times = sorted(r["http_ms"] for r in selected)
        summary[method] = {
            "mean_category_hits_at_5": round(
                statistics.mean(r["category_hits_at_5"] for r in selected), 3
            ),
            "median_http_ms": round(statistics.median(times), 2),
            "p95_http_ms": times[int(0.95 * (len(times) - 1))],
            "duplicate_places": sum(r["duplicate_places"] for r in selected),
        }
    report = {
        "run_at": now(),
        "query_file_sha256": sha256(queries_path),
        "queries_per_method": len(queries),
        "dataset_id": status.json()["dataset"]["dataset_id"],
        "index_id": status.json()["index"]["index_id"],
        "interpretation": "Category hits are an automatic proxy for broad type consistency, NOT human Precision@5 or itinerary quality. Queries contain category words and favor the keyword baseline. No model was tuned on these cases.",
        "summary": summary,
        "cases": rows,
    }
    write_json(EVIDENCE / "evaluation.json", report)
    log("evaluation_complete", summary=summary)


if __name__ == "__main__":
    main()
