# MS2 requirements and evidence

Course reference: [AC215 Milestone 2](https://harvard-iacs.github.io/2026-AC215/milestone2/).

| Requirement | Implementation | Evidence |
|---|---|---|
| Reproducible environment | Python dependencies use uv lockfiles. Computation runs in Docker. | `services/*/Dockerfile`, `pyproject.toml`, `uv.lock` |
| One-command pipeline | Ingest, clean, chunk, embed, index and serve. | `compose.yaml`, `compose.rag.yaml`, [run instructions](../README.md#run) |
| Initial RAG | MiniLM embeddings and Chroma retrieval supply context to an LLM. The server checks generated place IDs and citations. | [RAG design](RAG.md), `evidence/cloud/rag-live-evaluation.json` |
| Working application | Preferences, recommendations, source details and a cited itinerary. | [Live app](https://roamwise-rag-74919420019.us-central1.run.app) |
| Documentation and evidence | Data provenance, test results, retrieval evaluation and deployment instructions. | [Data](DATA.md), [retrieval results](RESULTS.md), [RAG verification](RAG_RESULTS.md), [deployment](DEPLOYMENT.md) |

The pilot has 500 places, 3,000 reviews and 3,976 chunks. Sources end in September 2021. The category benchmark is a retrieval check, not a human relevance score. Citation checks confirm reference membership; they do not prove every generated claim.

The LLM/RAG path is our primary MS2 scope. A category-and-rating baseline remains for comparison. We use pretrained models; API calls are not model training. Confirm the assessment path with the TF if the project is assessed as a hybrid recommendation system.

Submit the full commit hash of `milestone2`. The original slides describe the earlier retrieval build. Use [presentation notes](PRESENTATION_NOTES.md) for the current RAG demonstration.
