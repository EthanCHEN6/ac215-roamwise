# TF demo and individual preparation

Use the [five-person plan](TEAM_PLAN.md) for ownership and a 13-minute presentation schedule. Use [presentation notes](PRESENTATION_NOTES.md) for the current RAG explanation. The existing PPTX documents the earlier retrieval-only build and needs a content update before presenting the current system.

## Live demonstration

1. Open the [cloud app](https://roamwise-rag-74919420019.us-central1.run.app). Confirm it responds before the meeting.
2. Select Cambridge, one day, History, Museums, Food and Nature.
3. Show that result filters preserve the selected interests. A place may match more than one search.
4. Open one source passage and its file/line reference. The sources are historical.
5. Select two or three stops and generate an itinerary. Open a citation and the generation record.
6. Explain one validation rule and one limit: citation membership is checked, but claim meaning is not automatically verified.

For a baseline comparison, use the saved retrieval benchmark and its recorded input/output. The current trip form does not provide the earlier baseline-switching interface.

If the service fails, use saved evidence or a recording and label it as a recorded run. Cached retrieval data alone cannot replace a cloud LLM. Local Ollama is an alternative whose response quality has not been evaluated in this release.

## Everyone should be able to explain

- The data source, selection bias, chunking, embeddings and version IDs.
- How uv, Docker and Compose support reproduction.
- The difference between retrieval, generation and model training.
- How the server restricts searches and validates place IDs and citations.
- Why historical data, estimated transfers and unverified prices limit the itinerary.
- What tests check, what the category benchmark measures and what remains unverified.
- How runtime credentials reach the container without exposing secrets.
- Their actual contribution and how they checked AI-assisted work.

Current evidence: [RAG verification](RAG_RESULTS.md), [retrieval results](RESULTS.md), `evidence/cloud/interest-filter-check.json` and `evidence/cloud/interest-release-check.json`. Keep evidence from different prompt versions clearly labeled.
