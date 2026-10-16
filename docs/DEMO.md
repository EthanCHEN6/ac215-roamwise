# TF demo and individual preparation

Use the slides for 10–15 minutes, then navigate the repository. Suggested sequence:

1. Show the problem and pilot scope (1 min).
2. Explain source data, selection and limitations (2 min).
3. Walk through Compose dependencies, one Dockerfile and a lockfile (2 min).
4. Search for an art museum near Harvard. Open a result's source details (2 min).
5. Switch to the baseline and explain why the ordering differs (1 min).
6. Show the saved input/output, manifests, tests and benchmark (2 min).
7. Explain limitations and the next experiment (1 min).

Before presenting, run the app and confirm the index is ready. If internet is unavailable, cached data, weights and images are sufficient. Keep the saved screenshots and example JSON as a backup; describe them as a recorded run.

## Questions everyone should be able to answer

- Why use containers and uv? Containers fix the OS/runtime; the lockfile fixes Python dependencies.
- What makes a run reproducible? Source checksums, deterministic selection, config, model checksum, dependency locks and persisted manifests.
- Why split text? Smaller passages make the relevant evidence easier to retrieve. Overlap preserves context at boundaries.
- What does the vector score mean? Cosine similarity in the encoder's space; it is not a probability or a quality rating.
- Where is the LLM? MS2 implements the retrieval foundation required for the LLM track. It returns context; generation is not implemented.
- Why can two methods disagree? The baseline uses broad category words and historical ratings. Semantic search compares source text, which can retrieve related but unwanted categories.
- What is the benchmark measuring? Broad category consistency and latency on 20 fixed queries, not human relevance or travel quality.
- What happens if the source changes? Ingestion fails its checksum check; inspect and intentionally version a new snapshot.
- What remains for MS3? Human relevance judgments, a reranker training experiment, tracked runs and a serving/deployment plan.

Team members must describe their real contributions and review the whole codebase. The initial implementation was AI-assisted; no team member's contribution or understanding is claimed by these materials.
