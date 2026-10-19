# RAG implementation

The earlier build retrieved places and passages. It did not call a generative model. This update adds model-planned searches and an itinerary grounded in server-selected context.

## Request flow

1. Validate the structured trip preferences and notes.
2. Ask the LLM for one search per selected interest (at most four). The server fills an omitted interest with a short default query and records that choice in the trace. Only an allowlisted database search is available; the model cannot execute code or browse arbitrary URLs.
3. Apply hard city/category filters. Retrieve four places per search, keep similarity ≥ 0.25 and merge duplicates while keeping each matching interest. History and Museums use the culture index filter; Nature uses outdoors. The website keeps the original interest labels. A match means that a place was retrieved for that search, not that its relevance has been verified by a person. The threshold is not calibrated against human labels.
4. Let the user select stops. Retrieve context again on the server; reject client-supplied source text.
5. Generate JSON with selected place IDs, days, suggested durations, reasons and citations.
6. Check every selected place exactly once, citation membership, city, days, daily stop count and the 09:00–18:00 window. Allow one repair; return an error if it fails.

`roamwise/llm.py` implements Vertex AI and Ollama adapters. `roamwise/planner.py` contains prompts and validation. The prompt version is `rag-planner-v2`. There is no template fallback when a model fails.

## Two connected components

**Data maintenance** is an operator-controlled container job. It checks snapshot hashes and orphan chunks. With Places enabled, it upserts Google place IDs. Current details are fetched on demand and attributed. This deterministic job is not an autonomous LLM agent. It does not rebuild the historical index from Google API content.

**Trip planning** uses an LLM for intent-to-search conversion and context-to-itinerary generation. The server controls tools, hard filters and validation. This is bounded orchestration, not an open-ended agent loop.

Google Maps restricts content storage; place IDs are exempt. See the [Places policy](https://developers.google.com/maps/documentation/places/web-service/policies). The historical academic dataset and newly queried Google data have separate handling.

## Evidence and limits

Unit tests use model fixtures to check validation and failure paths. They do not measure model quality. The existing 20-query synthetic benchmark evaluates retrieval by category, not generated explanations.

Real sample requests and outputs are saved as `evidence/rag-*.json`. Each generated itinerary records model, prompt, dataset/index IDs, context hash, latency and validation. Server logs record token usage and metadata, not full preference text.

Independent human labels for relevance, claim support and itinerary usefulness remain future work. Citation membership does not prove that a sentence follows from its cited source. Current prices and availability are not verified. Transfers use straight-line distance and assumed speed; no route optimization is claimed.

## Operating bounds

- Four retrieval calls per recommendation; twelve selected stops across at most three days.
- Three stops per relaxed day, or four per balanced day.
- Ninety-second model timeout per call; at most one repair.
- Public service: two expensive requests at once, 60 per process per hour, 16 KB request bodies.
- Cloud Run: 1 CPU, 2 GiB, minimum zero and maximum one instance.

The hourly counter resets on restart. These controls are not hard billing caps.

Local Ollama is an included alternative. The real-model checks in this release used Vertex AI; local-model output quality has not been evaluated. See [verification results](RAG_RESULTS.md).
