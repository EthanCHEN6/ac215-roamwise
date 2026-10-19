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
