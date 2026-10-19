"""Audit the historical snapshot and maintain a Google place-ID catalog.

Google response content is used on demand, not inserted into the historical vector index.
Run maintenance as a container job, not as an unauthenticated public API.
"""

import argparse
import json
import os
import sqlite3
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from roamwise.common import DATA, EVIDENCE, jsonl, now, read_json, sha256, write_json


class SourceUnavailable(RuntimeError):
    pass


class GooglePlaces:
    endpoint = "https://places.googleapis.com/v1/places"

    def __init__(self, key=None):
        self.key = key or os.getenv("GOOGLE_PLACES_API_KEY")
        self.oauth = os.getenv("GOOGLE_PLACES_AUTH") == "adc"

    def request(self, suffix, fields, payload=None):
        if not self.key and not self.oauth:
            raise SourceUnavailable("Live Google Maps lookup is not configured. Historical sources remain available.")
        headers = {"X-Goog-FieldMask": fields, "Content-Type": "application/json"}
        if self.key:
            headers["X-Goog-Api-Key"] = self.key
        else:
            import google.auth
            from google.auth.transport.requests import Request as AuthRequest
            try:
                credentials, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
                credentials.refresh(AuthRequest())
            except google.auth.exceptions.GoogleAuthError as exc:
                raise SourceUnavailable("Live lookup could not authenticate.") from exc
            headers["Authorization"] = "Bearer " + credentials.token
            headers["X-Goog-User-Project"] = os.environ["GOOGLE_CLOUD_PROJECT"]
        request = Request(self.endpoint + suffix, data=json.dumps(payload).encode() if payload else None,
                          headers=headers, method="POST" if payload else "GET")
        try:
            with urlopen(request, timeout=20) as response:
                return json.load(response)
        except (HTTPError, URLError, TimeoutError, ValueError) as exc:
            raise SourceUnavailable("Google Maps could not return current details. No historical value was relabeled as current.") from exc

    def discover(self, query):
        result = self.request(":searchText", "places.id", {
            "textQuery": query, "pageSize": 10,
            "locationRestriction": {"rectangle": {"low": {"latitude": 42.22, "longitude": -71.20},
                                                    "high": {"latitude": 42.43, "longitude": -70.98}}}})
        return [p["id"] for p in result.get("places", [])]

    def lookup(self, name, city):
        results = self.request(":searchText", "places.id,places.displayName,places.formattedAddress,places.googleMapsUri,places.businessStatus,places.currentOpeningHours", {
            "textQuery": f"{name}, {city}, Massachusetts", "pageSize": 1,
            "locationRestriction": {"rectangle": {"low": {"latitude": 42.22, "longitude": -71.20},
                                                    "high": {"latitude": 42.43, "longitude": -70.98}}}})
        if not results.get("places"):
            raise SourceUnavailable("No live match was found for this historical record.")
        return {"provider": "Google Maps", "checked_at": now(), "match_status": "text-search candidate; confirm name and address",
                "place": results["places"][0], "persist": False}


def audit_snapshot():
    manifest = read_json(DATA / "processed/manifest.json")
    for name, expected in manifest["files"].items():
        if sha256(DATA / "processed" / name) != expected:
            raise ValueError(f"Processed file checksum mismatch: {name}")
    places = list(jsonl(DATA / "processed/places.jsonl"))
    ids = {p["place_id"] for p in places}
    chunks = list(jsonl(DATA / "processed/chunks.jsonl"))
    if len(ids) != len(places) or any(c["place_id"] not in ids for c in chunks):
        raise ValueError("Duplicate places or orphan chunks")
    report = {"checked_at": now(), "dataset_id": manifest["dataset_id"], "places": len(places),
              "chunks": len(chunks), "checksums_match": True, "orphan_chunks": 0,
              "source_cutoff": "2021-09", "new_google_api_content_in_vector_index": False}
    write_json(EVIDENCE / "data-agent-audit.json", report)
    return report


def refresh_catalog(queries, path=None, client=None):
    path = path or DATA / "google-place-ids.sqlite"
    client = client or GooglePlaces()
    with sqlite3.connect(path) as db:
        db.execute("CREATE TABLE IF NOT EXISTS place_ids (place_id TEXT PRIMARY KEY, checked_at TEXT NOT NULL)")
        total = 0
        for query in queries[:4]:
            for pid in client.discover(query):
                db.execute("INSERT INTO place_ids VALUES (?,?) ON CONFLICT(place_id) DO UPDATE SET checked_at=excluded.checked_at", (pid, now()))
                total += 1
        return {"checked_at": now(), "queries": min(len(queries), 4), "ids_seen": total,
                "catalog_size": db.execute("SELECT count(*) FROM place_ids").fetchone()[0],
                "stored_fields": ["place_id", "checked_at"]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--discover-google", action="store_true")
    args = parser.parse_args()
    report = {"snapshot": audit_snapshot()}
    if args.discover_google:
        report["google_catalog"] = refresh_catalog(["museums in Boston Massachusetts", "parks in Cambridge Massachusetts", "restaurants in Somerville Massachusetts"])
    write_json(EVIDENCE / "data-agent-run.json", report)
    print(json.dumps(report))


if __name__ == "__main__":
    main()
