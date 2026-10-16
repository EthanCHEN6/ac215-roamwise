import importlib.metadata
import os
import time

import chromadb
from chromadb.config import Settings

from roamwise.common import (
    DATA,
    EVIDENCE,
    ROOT,
    jsonl,
    log,
    now,
    read_json,
    stable_hash,
    write_json,
)
from roamwise.embedding import encoder, model_info


def main():
    started = time.perf_counter()
    config = read_json(ROOT / "config/pipeline.json")
    dataset = read_json(DATA / "processed/manifest.json")
    model = model_info()
    index_id = stable_hash(
        {
            "dataset": dataset["dataset_id"],
            "model": model,
            "chroma": importlib.metadata.version("chromadb"),
        }
    )[:16]
    client = chromadb.PersistentClient(
        path=str(DATA / "index"), settings=Settings(anonymized_telemetry=False)
    )
    embedding = encoder()
    name = config["collection"]
    existing = next((c for c in client.list_collections() if c.name == name), None)
    if (
        existing
        and existing.metadata.get("index_id") == index_id
        and existing.count() == dataset["counts"]["chunks"]
    ):
        write_json(
            EVIDENCE / "index-manifest.json", read_json(DATA / "index-manifest.json")
        )
        log("index_cached", index_id=index_id, chunks=existing.count())
        return
    if existing:
        client.delete_collection(name)
    collection = client.create_collection(
        name,
        embedding_function=embedding,
        metadata={
            "hnsw:space": "cosine",
            "index_id": index_id,
            "dataset_id": dataset["dataset_id"],
        },
    )
    rows = list(jsonl(DATA / "processed/chunks.jsonl"))
    for start in range(0, len(rows), 64):
        batch = rows[start : start + 64]
        collection.add(
            ids=[r["chunk_id"] for r in batch],
            documents=[r["embedding_text"] for r in batch],
            metadatas=[
                {
                    k: r[k]
                    for k in (
                        "place_id",
                        "city",
                        "category",
                        "kind",
                        "source_file",
                        "source_line",
                        "dataset_id",
                    )
                }
                for r in batch
            ],
        )
        if start % 512 == 0:
            log("index_progress", indexed=min(start + 64, len(rows)), total=len(rows))
    manifest = {
        "created_at": now(),
        "index_id": index_id,
        "dataset_id": dataset["dataset_id"],
        "collection": name,
        "chunks": collection.count(),
        "model": model,
        "chromadb_version": importlib.metadata.version("chromadb"),
        "seconds": round(time.perf_counter() - started, 3),
    }
    write_json(DATA / "index-manifest.json", manifest)
    write_json(EVIDENCE / "index-manifest.json", manifest)
    log("index_complete", **manifest)


if __name__ == "__main__":
    main()
