# RAG verification — 19 October 2026 (UTC)

- Container unit tests: **34 passed**. One upstream AnyIO deprecation warning.
- Real Vertex AI integration: **9/9 checks passed** after a prompt correction.
- Cambridge: eight recommended places; a two-stop itinerary passed all structural checks.
- Boston: thirteen recommended places; a four-stop, two-day itinerary passed all structural checks.
- In the local API test, recommendation and itinerary requests took about 3–6 seconds. These are individual observations, not a latency benchmark.
- Three Google place-ID discovery queries produced 30 distinct IDs. The SQLite catalog stores only IDs and our check timestamps.
- One current-details lookup returned a candidate name and opening-hours fields. Its Google response content was not persisted.
- The standalone cloud image served all required HTML, CSS, JavaScript and image assets under 1 CPU / 2 GiB limits.

## Observed failure and change

The first scope test expected an instruction-override request to be rejected. The model instead ignored the malicious text and returned ordinary Cambridge museum searches. It did not expose credentials or call an unauthorized tool. We made the rejection rule explicit and repeated the test; it returned a clarification. Both runs are retained. This single example does not establish general prompt-injection resistance.

## What remains unverified

Browser automation could not start because of a local tool runtime error. We checked JavaScript syntax, HTTP assets and real API flows, but did not complete visual, keyboard or mobile-browser QA. There is no independent human relevance, semantic-entailment or itinerary-usefulness score. Historical claims and current conditions need review before travel.

Files: `rag-unit-tests.txt`, `rag-live-initial-evaluation.json`, `rag-live-evaluation.json`, `rag-cambridge-*.json`, `rag-boston-*.json`, `data-agent-audit.json`, `rag-server-log.txt`.

## Interest-filter update

Prompt version `rag-planner-v2` preserves one search per selected interest and records matching interests on each place. Container tests: **36 passed**. A JavaScript DOM fixture checks filter labels and counts, overlapping interests, retained selections, empty results and refresh of older cached results. It does not test browser layout.

One live four-interest request returned 16 unique Cambridge places: four matches for each selected interest. City and category filters passed. This verifies the response structure, not human relevance. See `evidence/cloud/interest-filter-check.json`. The earlier 9-case results below belong to prompt version v1; they have not been relabeled as v2 results.

Current submission files use English. The language check covers text, filenames and PowerPoint XML, including speaker notes. Existing screenshot evidence was inspected separately. Private preparation notes are kept outside the repository.

## Public deployment check

The public Cloud Run service passed the same 9-case integration suite with its production service account. Observed recommendation and itinerary requests took 1.7–2.9 seconds in this small warm run. All required page assets returned HTTP 200. The separate Sites origin passed the CORS check. A live Google Places lookup also returned name and hours fields without persisting response content.

See `evidence/cloud/rag-live-evaluation.json`, `evidence/cloud-http-checks.json`, `evidence/cloud-google-lookup-check.json` and `evidence/cloud-deployment.json`. These checks do not replace browser or human quality review.
