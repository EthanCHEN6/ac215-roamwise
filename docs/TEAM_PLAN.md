# Five-person MS2 work plan

Replace A–E with team members' names after agreeing on ownership. This is a proposed handoff plan, not a record of completed personal contributions. The current implementation was AI-assisted. Each person must run, inspect and explain their work before claiming it.

The [MS2 instructions](https://harvard-iacs.github.io/2026-AC215/milestone2/) specify a 10–15-minute presentation, about 10 minutes of group questions, and separate individual checks of about five minutes with 3–4 questions. Everyone must understand the full project. Use the TF's booked meeting time for the actual schedule.

## Ownership and next tasks

| Owner | Scope | Existing foundation | Required handoff before the presentation |
|---|---|---|---|
| A | Product, frontend and demo | Preferences, interest filters, source details and itineraries | Check the full flow in desktop and mobile browsers. Record failures and fixes. Capture current screenshots and a short backup recording. Assemble the shared slides from each owner's material. |
| B | Data, cleaning and provenance | Pinned sources, pilot selection, chunks, manifests and maintenance job | Trace one place and passage to their source file/line. Run the snapshot audit. Explain filters, missing fields and sampling bias. Match dataset IDs to the evidence. |
| C | Embeddings, retrieval and evaluation | MiniLM, Chroma, city/category filters and category/rating baseline | Reproduce one query-to-context example and the fixed benchmark. Inspect misses without tuning the benchmark. Produce a small, clearly labeled manual relevance review and explain its limits. |
| D | RAG, API and output checks | Search planning, context retrieval, itinerary generation and bounded repair | Walk through a complete request and one rejected output. Coordinate current v2 integration checks within the agreed API budget. Explain citation membership versus claim support. |
| E | uv, containers, cloud and release | Compose, lockfiles, Cloud Run and public URLs | Verify startup on a teammate's machine or a clean isolated volume. Run tests, check health and runtime identity, and collect release evidence. Coordinate the final branch and commit hash. |

**Code map**

- A: `frontend/plan.html`, `frontend/recommendations.html`, `frontend/planner-app.js`, `frontend/site.css`.
- B: `config/sources.json`, `config/pipeline.json`, `roamwise/ingest.py`, `roamwise/preprocess.py`, `roamwise/data_agent.py`, `tests/test_pipeline.py`.
- C: `roamwise/embedding.py`, `roamwise/index.py`, `roamwise/retrieval.py`, `roamwise/evaluate.py`, `evaluation/queries.json`, `tests/test_retrieval.py`.
- D: `roamwise/api.py`, `roamwise/llm.py`, `roamwise/planner.py`, `roamwise/evaluate_rag.py`, `tests/test_api.py`, `tests/test_planner.py`.
- E: `compose.yaml`, `compose.rag.yaml`, `services/`, `roamwise/cloud.py`, `deploy/`, `docs/DEPLOYMENT.md`.

Each owner supplies one or two slides, one saved evidence example, a component walkthrough and an honest contribution note. Record the action, file or command, result and reviewer. A coordinates slide formatting; each owner writes their technical explanation. E runs combined checks; each owner fixes failures in their component.

**Interfaces:** B gives C the data contract and dataset ID. C gives D place IDs, passages, scores and index ID. D gives A API fields and failure behavior. E packages the components and checks startup order. A reports user-flow failures to the relevant owner.

## Cross-review

Reviewers ask the owner to run the component, explain one design choice and show one failure case.

| Owner | Reviewer | Review focus |
|---|---|---|
| A | D | API fields, selections and visible errors |
| B | E | Data integrity, versions and reproducible inputs |
| C | B | Filters, sources and evaluation labels |
| D | C | Context, citations and invalid outputs |
| E | A | A teammate can start and use the app |

This is the minimum review. Every member must also explain the path from raw data to the displayed itinerary.

## Proposed 13-minute presentation

This allocation is our rehearsal plan, not an extra course requirement. Q&A is separate.

| Time | Speaker | Slides / action | Evidence |
|---|---|---|---|
| 0:00–1:00 | A | 1. Problem, users and scope | One concrete Cambridge trip request |
| 1:00–3:00 | B | 2. Data and provenance | 500 places, 3,000 reviews, 3,976 chunks; one source trace |
| 3:00–5:00 | E | 3. Reproducible pipeline | Compose order, one Dockerfile, uv lockfile and version IDs |
| 5:00–7:30 | C | 4–5. Retrieval and baseline comparison | Query → passages; category proxy and its limits |
| 7:30–10:00 | D | 6–7. RAG and output validation | Model context; one citation check and one rejected case |
| 10:00–12:00 | A | 8. Live demonstration | Preferences → filters → selected places → cited itinerary |
| 12:00–13:00 | E | 9. Verification, limits and next work | Current tests, unverified areas and human evaluation plan |

Use `docs/PRESENTATION_NOTES.md` for current RAG wording. The existing `slides/RoamWise_MS2.pptx` still describes the earlier retrieval-only release; translating its notes did not update its technical content. Revise it before presenting this flow. Keep submitted slides and notes in English.

## Questions to rehearse

| First responder | Likely question | Minimum accurate answer |
|---|---|---|
| A | Why do History and Museums overlap? | They use separate queries against the culture index. A place may match both. A match records retrieval, not verified relevance. |
| B | Are the data current and representative? | Sources end in 2021. Popular places and a few reviews per place form a biased pilot. Current details are checked separately. |
| C | What do embeddings and similarity mean? | MiniLM maps text to 384 values. Chroma compares vectors. Similarity is not a probability. |
| C | Why does the baseline score better? | The small benchmark checks categories and contains category words. It does not measure human trip relevance. |
| D | Where is RAG? Did you train the LLM? | Retrieved passages enter the generation prompt. We use pretrained models and did not train an LLM. |
| D | Do citations prevent hallucinations? | We check source membership and place identity. We do not automatically prove every claim follows from its source. |
| E | Why uv and Docker? | uv locks Python dependencies. Docker packages the runtime. Compose controls service order. |
| E | How does cloud authentication work? | The service uses its attached runtime service account. No private key is embedded in the image. |
| All | What did you personally do? | Describe work you actually ran, reviewed or changed. Point to evidence. Explain AI assistance and your checks. |

## Final preparation

1. Assign names. Each person runs their component and records one observed issue or verified behavior.
2. Complete cross-reviews. Update slides and evidence together. Keep v1 integration results distinct from v2 checks.
3. Rehearse the 13-minute talk. Give each person 3–4 questions, including one outside their ownership.
4. E verifies the branch and full commit hash; a second teammate checks the Canvas entry. The [MS2 deadline](https://harvard-iacs.github.io/2026-AC215/milestone2/) is October 20 at 10:00 PM ET.

Warm the demo service before presenting. If a live request fails, show a saved response or recording and identify it as a recorded run. Local Ollama is an alternative, but its response quality has not been evaluated in this release. Avoid an untested model switch during the presentation.
