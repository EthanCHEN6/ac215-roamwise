"""Select a bounded pilot dataset and preserve the source of every text chunk."""

import gzip
import json
import math
import re
from collections import Counter, defaultdict

from roamwise.common import (
    DATA,
    EVIDENCE,
    ROOT,
    log,
    now,
    read_json,
    sha256,
    stable_hash,
    write_json,
    write_jsonl,
)

CATEGORY_TERMS = {
    "culture": (
        "museum",
        "art gallery",
        "theater",
        "theatre",
        "concert hall",
        "performing arts",
        "library",
    ),
    "outdoors": (
        "park",
        "garden",
        "tourist attraction",
        "historical landmark",
        "hiking",
        "beach",
        "aquarium",
        "zoo",
        "university",
    ),
    "lodging": ("hotel", "hostel", "bed & breakfast", "inn", "motel", "lodging"),
    "food": (
        "restaurant",
        "cafe",
        "coffee shop",
        "bakery",
        "tea house",
        "ice cream",
        "pizza",
    ),
}
CAMPUS_NAMES = {"harvard university", "massachusetts institute of technology"}


def clean_text(value):
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    text = re.sub(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", "[email removed]", text)
    text = re.sub(
        r"(?<!\d)(?:\+1[ .-]?)?\(?\d{3}\)?[ .-]\d{3}[ .-]\d{4}(?!\d)",
        "[phone removed]",
        text,
    )
    return text


def category_for(categories, name=""):
    if name.casefold() in CAMPUS_NAMES:
        return "outdoors"
    joined = " | ".join(categories).casefold()
    for group, terms in CATEGORY_TERMS.items():
        if any(re.search(r"\b" + re.escape(term) + r"\b", joined) for term in terms):
            return group
    return None


def city_for(address, name, config):
    match = re.search(
        r",\s*([^,]+),\s*MA(?:\s+\d{5}(?:-\d{4})?)?(?:,|$)", address or "", re.I
    )
    city = match.group(1).strip() if match else ""
    if name.casefold() in CAMPUS_NAMES:
        city = "Cambridge"
    if city.casefold() in {x.casefold() for x in config["boston_neighborhoods"]}:
        city = "Boston"
    return next((x for x in config["cities"] if x.casefold() == city.casefold()), None)


def normalized_place(row, config):
    name = clean_text(row.get("name"))
    categories = [str(x) for x in (row.get("category") or [])]
    group = category_for(categories, name)
    city = city_for(row.get("address"), name, config)
    try:
        lat, lon = float(row["latitude"]), float(row["longitude"])
        rating = float(row.get("avg_rating") or 0)
        count = int(row.get("num_of_reviews") or 0)
    except (ValueError, TypeError, KeyError):
        return None
    bounds = config["bounds"]
    if not (name and group and city and row.get("gmap_id")):
        return None
    if not (math.isfinite(lat) and math.isfinite(lon) and math.isfinite(rating)):
        return None
    if not (
        bounds["min_lat"] <= lat <= bounds["max_lat"]
        and bounds["min_lon"] <= lon <= bounds["max_lon"]
    ):
        return None
    if "permanently closed" in str(row.get("state", "")).casefold():
        return None
    return {
        "place_id": str(row["gmap_id"]),
        "name": name,
        "city": city,
        "category": group,
        "categories": categories,
        "address": clean_text(row.get("address")),
        "latitude": lat,
        "longitude": lon,
        "rating": rating if 0 < rating <= 5 else None,
        "review_count": max(count, 0),
        "price": row.get("price") or None,
        "historical_hours": row.get("hours") or None,
        "description": clean_text(row.get("description")),
        "source_url": "https://www.google.com/maps?cid="
        + str(int(str(row["gmap_id"]).split(":")[-1], 16))
        if re.fullmatch(r"0x[0-9a-f]+:0x[0-9a-f]+", str(row["gmap_id"]))
        else None,
        "source_snapshot": "Google Local 2021",
    }


def word_chunks(text, size=100, overlap=20):
    if not 0 <= overlap < size:
        raise ValueError("Chunk overlap must be smaller than chunk size")
    words = text.split()
    for start in range(0, len(words), size - overlap):
        yield " ".join(words[start : start + size])
        if start + size >= len(words):
            break


def read_gzip(path):
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            try:
                yield line_number, json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(
                    f"Invalid JSON in {path.name}, line {line_number}"
                ) from error


def main():
    config = read_json(ROOT / "config/pipeline.json")
    source = read_json(DATA / "raw/manifest.json")
    dataset_id = (
        "boston-"
        + stable_hash(
            {"sources": [x["sha256"] for x in source["files"]], "config": config}
        )[:16]
    )
    processed = DATA / "processed"
    previous = processed / "manifest.json"
    if previous.exists():
        cached = read_json(previous)
        if cached["dataset_id"] == dataset_id and all(
            (processed / name).exists() and sha256(processed / name) == digest
            for name, digest in cached["files"].items()
        ):
            write_json(EVIDENCE / "dataset-manifest.json", cached)
            log("preprocess_cached", dataset_id=dataset_id)
            return
    by_id = {}
    stats = Counter()
    for line, row in read_gzip(DATA / "raw/meta-Massachusetts.json.gz"):
        stats["metadata_rows"] += 1
        place = normalized_place(row, config)
        if place:
            if place["place_id"] in by_id:
                stats["duplicate_eligible_places"] += 1
            else:
                place["metadata_source_line"] = line
                by_id[place["place_id"]] = place
    grouped = defaultdict(list)
    for place in by_id.values():
        grouped[place["category"]].append(place)
    places = []
    for group in sorted(grouped):
        places.extend(
            sorted(grouped[group], key=lambda x: (-x["review_count"], x["place_id"]))[
                : config["places_per_category"]
            ]
        )
    selected = {x["place_id"]: x for x in places}
    reviews = defaultdict(list)
    seen = defaultdict(set)
    log("places_selected", count=len(places), eligible=len(by_id))
    for line, row in read_gzip(DATA / "raw/review-Massachusetts.json.gz"):
        stats["review_rows_scanned"] += 1
        pid = row.get("gmap_id")
        if pid not in selected:
            continue
        text = clean_text(row.get("text"))
        if not text:
            continue
        fingerprint = stable_hash(text.casefold())
        if fingerprint in seen[pid]:
            stats["selected_place_duplicate_texts"] += 1
            continue
        seen[pid].add(fingerprint)
        if len(reviews[pid]) < config["reviews_per_place"]:
            # Retain no reviewer names, IDs, profile links or photos.
            reviews[pid].append(
                {
                    "text": " ".join(text.split()[: config["max_review_words"]]),
                    "source_line": line,
                    "text_sha256": fingerprint,
                    "timestamp_ms": row.get("time"),
                    "rating": row.get("rating"),
                }
            )
    chunks = []
    for place in places:
        pid = place["place_id"]
        place["sampled_review_count"] = len(reviews[pid])
        metadata_text = f"{place['name']}. {place['city']}. Categories: {', '.join(place['categories'])}. {place['description']}"
        records = [
            {
                "text": metadata_text,
                "kind": "metadata",
                "source_line": place["metadata_source_line"],
            }
        ]
        records += [{**r, "kind": "review"} for r in reviews[pid]]
        for record in records:
            for ordinal, text in enumerate(
                word_chunks(
                    record["text"], config["chunk_words"], config["chunk_overlap"]
                )
            ):
                # Place context is embedded with each review to keep its identity attached.
                embedding_text = f"{place['name']} | {place['city']} | {', '.join(place['categories'])}\n{text}"
                chunk = {
                    "place_id": pid,
                    "text": text,
                    "embedding_text": embedding_text,
                    "kind": record["kind"],
                    "source_line": record["source_line"],
                    "source_file": "meta-Massachusetts.json.gz"
                    if record["kind"] == "metadata"
                    else "review-Massachusetts.json.gz",
                    "ordinal": ordinal,
                    "timestamp_ms": record.get("timestamp_ms"),
                    "city": place["city"],
                    "category": place["category"],
                    "dataset_id": dataset_id,
                }
                chunk["chunk_id"] = stable_hash(chunk)[:32]
                chunks.append(chunk)
    if not places or not any(x["kind"] == "review" for x in chunks):
        raise ValueError("The real-data pipeline produced no places or reviews")
    write_jsonl(processed / "places.jsonl", sorted(places, key=lambda x: x["place_id"]))
    write_jsonl(processed / "chunks.jsonl", chunks)
    manifest = {
        "dataset_id": dataset_id,
        "created_at": now(),
        "config": config,
        "counts": {
            **stats,
            "eligible_places": len(by_id),
            "places": len(places),
            "sampled_reviews": sum(map(len, reviews.values())),
            "chunks": len(chunks),
        },
        "category_counts": dict(Counter(p["category"] for p in places)),
        "city_counts": dict(Counter(p["city"] for p in places)),
        "files": {
            name: sha256(processed / name) for name in ("places.jsonl", "chunks.jsonl")
        },
        "source_sha256": {x["name"]: x["sha256"] for x in source["files"]},
    }
    write_json(previous, manifest)
    write_json(EVIDENCE / "dataset-manifest.json", manifest)
    log("preprocess_complete", **manifest["counts"], dataset_id=dataset_id)


if __name__ == "__main__":
    main()
