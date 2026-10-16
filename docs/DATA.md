# Data and model

## Source

[UCSD Google Local 2021](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/) supplies Massachusetts metadata and reviews through September 2021. `config/sources.json` pins both files by URL and SHA-256. A changed or corrupt file stops ingestion. The pipeline downloads from the source; it does not depend on a teammate's spreadsheet or local folder.

Dataset citations requested by its authors:

- Jiacheng Li, Jingbo Shang, Julian McAuley. *UCTopic: Unsupervised Contrastive Learning for Phrase Representations and Topic Mining.* ACL, 2022.
- An Yan, Zhankui He, Jiacheng Li, Tianyang Zhang, Julian McAuley. *Personalized Showcases: Generating Multi-Modal Explanations for Recommendations.* SIGIR, 2023.

Raw files and full review texts stay in the local Docker volume. They are not redistributed with the repository. This academic prototype does not establish permission for commercial redistribution; consult the source and original content terms before a broader deployment.

## Selection

`config/pipeline.json` controls selection. Eligible places must have an ID, name, recognized travel category, parsed target city, finite coordinates inside the bounding box, and no historical “permanently closed” flag. Boston neighborhood names map to Boston. Harvard University and MIT have an explicit campus allowlist, while coordinate bounds still apply. This is a pilot area filter, not an authoritative municipal boundary.

The first eligible row for each place ID is retained. Categories use ordered rules: culture, outdoors, lodging, food. A museum with a cafe is therefore culture. Within each group, the most-reviewed 125 places are selected; ties use place ID. Smaller groups keep all eligible places.

Reviews are scanned in file order. Case-normalized duplicate texts are dropped per selected place. At most six distinct nonempty texts per place are kept, capped at 400 words each. This is not a random or sentiment-balanced sample. Reviewer IDs, names, profile URLs and photos are discarded; email and common US phone patterns are redacted from text. Free text can still contain personal information.

## Storage contract

| File | Key fields |
|---|---|
| `places.jsonl` | `place_id`, name, city, category, original categories, coordinates, historical rating/count, nullable price/hours |
| `chunks.jsonl` | `chunk_id`, `place_id`, text, embedding text, source file/line, kind, optional timestamp, dataset ID |
| `manifest.json` | source hashes, selection config, row counts, output hashes, dataset ID |
| Chroma collection | chunk ID, 384-value embedding, document, filter metadata |

Dataset ID hashes the source checksums and preprocessing configuration. Output file hashes verify cache integrity. Index ID additionally includes the model archive checksum and Chroma version. A new ID triggers a rebuild. Run only one pipeline writer at a time; the API starts after indexing has finished. To rebuild after changing preprocessing code, also increment `selection_version` in the config.

## Encoder

Chroma's ONNX implementation of [all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) runs on CPU, returns 384 dimensions, and uses cosine distance. The ONNX archive SHA-256 is `913d7300ceae3b2dbc2c50d1de4baacab4be7b9380491c27fab7418616a16ec3`; Chroma verifies the archive during download. The same function embeds index documents and queries. Package versions are frozen in each service's lockfile; the model manifest records the resolved archive and implementation.

A 100-word chunk is a heuristic: subword tokenization can still truncate unusually long inputs. Retrieval considers up to `max(80, 30 × top_k)` chunks, then keeps the best-scoring chunk per place and at most two passages per result. This bounded candidate pool can reduce recall when many high-ranking chunks come from the same place.

## Missing and historical fields

Null price/hours means unknown. Source ratings and closure flags describe the historical snapshot. Neither metadata nor reviews establish current opening status, affordability, accessibility or availability. Generated schedules, walking times and route optimization are outside this milestone.
