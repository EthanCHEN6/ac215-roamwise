"""Save a small, explicit replay of real API requests for the public showcase."""

import json
from datetime import datetime, timezone
from pathlib import Path

import httpx


def main():
    cases = [
        ("art", "Art near Harvard", "art museum with paintings near Harvard", "Cambridge"),
        ("parks", "A walk in Boston", "A park for an outdoor walk", "Boston"),
        ("coffee", "Coffee in Cambridge", "Coffee shop for breakfast", "Cambridge"),
    ]
    output = {"recorded_at": datetime.now(timezone.utc).isoformat(), "examples": []}
    with httpx.Client(base_url="http://api:8000", timeout=120) as client:
        for key, title, query, city in cases:
            case = {"id": key, "title": title, "query": query, "city": city, "methods": {}}
            for method in ("semantic", "baseline"):
                request = {"query": query, "city": city, "method": method, "top_k": 3}
                response = client.post("/api/search", json=request)
                response.raise_for_status()
                result = response.json()
                for place in result["results"]:
                    for citation in place["evidence"]:
                        citation["text"] = " ".join(citation["text"].split()[:25])
                result.pop("context", None)
                case["methods"][method] = result
            output["examples"].append(case)
    output["note"] = "Recorded API results, not live search. Excerpts shortened to 25 words."
    Path("/export/examples.json").write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Exported 3 queries × 2 methods with source citations.")


if __name__ == "__main__":
    main()
