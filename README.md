# RoamWise

Plan short trips in Boston, Cambridge or Somerville. A language model plans database searches, reads retrieved passages and drafts a cited itinerary from the places you select. The server checks place IDs, citations, daily stop limits and the proposed schedule.

The website follows our six-page prototype: home → preferences → retrieval → selection → itinerary, with source details. This is a course prototype, not a booking service.

Live app: [Open RoamWise](https://roamwise-rag-74919420019.us-central1.run.app). The service runs on Cloud Run; the owner's computer can be off.

## Run

Install Docker with Compose. All Python services use uv and committed lockfiles. Computation runs in containers.

```bash
git clone https://github.com/EthanCHEN6/ac215-roamwise.git
cd ac215-roamwise
git checkout milestone2
docker compose -f compose.yaml -f compose.rag.yaml up --build
```

Open **http://localhost:8080** after the API is healthy. The first run downloads data, images and model weights. Allow at least 8 GB RAM and 12 GB disk. Local CPU generation uses Ollama and can be slow. The shared cloud service uses Vertex AI; see [deployment](docs/DEPLOYMENT.md).

For the original retrieval pipeline, use `docker compose up --build`. The new trip form needs a configured LLM and reports an error if generation is unavailable.

```text
Historical source → clean/chunk → MiniLM embeddings → Chroma
                                                       ↑
Preferences → LLM search plan → retrieval → selection → LLM draft → validation
Data maintenance: snapshot audit + Google ID discovery + on-demand current details
```

The pilot contains 500 places, 3,000 reviews and 3,976 chunks, with sources through September 2021. Every chunk retains its source file, line, place ID and dataset ID. New Google API content is not inserted into this historical index. The maintenance catalog stores place IDs and our check timestamps only.

## Verify

```bash
docker compose --profile test run --build --rm test
docker compose run --rm --no-deps evaluate
docker compose -f compose.yaml -f compose.rag.yaml --profile maintenance run --build --rm data-agent
```

Read [RAG design](docs/RAG.md), [presentation notes and TF questions](docs/PRESENTATION_NOTES.md), [data notes](docs/DATA.md) and [retrieval results](docs/RESULTS.md). The original slides in `slides/` describe the earlier retrieval-only build; use the RAG notes for this update.

## Limits

Budget is a preference. Current prices, total cost, accessibility and availability are not verified by the planner. Travel times use distance and assumed speed, not routing. Citation checks establish reference membership, not the truth of every sentence. The 0.25 similarity cutoff is provisional. Results on 20 synthetic category queries are not human relevance or RAG-quality scores.

The [AC215 MS2 requirements](https://harvard-iacs.github.io/2026-AC215/milestone2/) require a one-command container pipeline, retrieval evidence, a working application skeleton and documentation. Submit the full commit hash of the `milestone2` branch. A functioning demo does not establish a particular grade.
