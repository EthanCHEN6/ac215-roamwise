# RoamWise

Find places in Boston, Cambridge and Somerville using historical Google Local metadata and reviews. The web app sends a request to FastAPI, retrieves source passages from Chroma, and shows places with citations. This MS2 build implements retrieval; it does not generate itineraries or claim live availability.

## Run

Install Docker Desktop with Linux containers (Windows: WSL 2 backend), or Docker Engine with Compose on Linux. Allow at least 8 GB memory and about 8 GB free disk space. No host Python, GPU, cloud account or API key is needed.

```bash
git clone https://github.com/EthanCHEN6/ac215-roamwise.git
cd ac215-roamwise
git checkout milestone2
docker compose up --build
```

The last line downloads the data, preprocesses it, builds the vector index, starts the API and website, and runs the evaluation. The first run needs internet access and downloads about 844 MB of source data plus images and the encoder. Later runs reuse verified data and the index. Wait for the API health check and `evaluation_complete`.

- App: http://localhost:8080
- API schema and interactive requests: http://localhost:8000/docs
- Status and versions: http://localhost:8000/api/status

Stop with Ctrl+C and `docker compose down`. Named volumes keep the dataset and model. Do not add `-v` unless you intend to delete them. To run in the background, use `docker compose up --build -d`.

## Pipeline

```text
UCSD gzip files → ingest → preprocess → MiniLM / Chroma → FastAPI → static UI
                                                         ↓
                                              evaluation + saved evidence
```

| Component | What it does |
|---|---|
| `ingest` | Downloads two Massachusetts files and checks committed SHA-256 values. |
| `preprocess` | Filters geography/categories, removes duplicate place IDs and review texts, drops reviewer identifiers, and chunks text. |
| `index` | Embeds chunks with pretrained all-MiniLM-L6-v2 on CPU and persists a cosine index in Chroma. |
| `api` | Validates requests, filters by city/type, deduplicates places, and returns source context. |
| `web` | Offers search, source details, saved places and shortlist export. |
| `evaluate` | Compares semantic retrieval with a category-and-rating baseline on 20 fixed queries. |

Each Python service has a Dockerfile, `pyproject.toml` and `uv.lock`. Images use `uv sync --frozen`; CPU work, including tests and evaluation, runs in containers. The static frontend is also served in a container.

## Data and model

The pilot takes up to 125 places per category, ordered by source review count, and the first six distinct nonempty review texts per place in source order. This is a small, popularity-biased sample. Text chunks contain 100 words with 20-word overlap; reviews are capped at 400 words. Each chunk retains its place ID, source file, source line and dataset ID. See [data and model notes](docs/DATA.md).

The baseline infers a broad category from query keywords and ranks using a Bayesian-adjusted rating. Semantic retrieval uses a pretrained encoder; no model is trained in MS2. Similarity is not a probability. The automatic category benchmark is not human Precision@5.

## Verify and inspect

```bash
docker compose --profile test run --build --rm test
docker compose run --rm --no-deps evaluate
docker compose ps -a
docker compose logs --no-color
```

Checked-in evidence includes [sample input](evidence/sample-input.json), [retrieved output](evidence/sample-output.json), [evaluation](evidence/evaluation.json), data/model manifests, logs and screenshots. Run evidence is regenerated in `evidence/`. Raw files, full review texts and model weights are not committed.

See [results](docs/RESULTS.md), [the Chinese requirement/code guide](docs/MS2_中文对照说明.md), and [the presentation](slides/RoamWise_MS2.pptx).

## Limits and next step

Source data ends in September 2021. Prices and hours may be missing or outdated. English queries work best with this encoder. Geographic selection uses address parsing plus a bounding box, not city polygons. A place with few reviews can return fewer results under a restrictive filter. MS3 work should add independently reviewed relevance labels and train/evaluate a small reranker before adding generated explanations.

Submission: push the `milestone2` branch and submit its full commit hash on Canvas. The [course MS2 page](https://harvard-iacs.github.io/2026-AC215/milestone2/) lists October 20, 10 PM ET and a team presentation with individual checks.
