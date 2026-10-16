# Run evidence

These files record a local Docker/CPU run on 2026-10-16. They are observations, not expected/example results invented for the report.

- `source-manifest.json`: exact source URLs, sizes and SHA-256 values.
- `dataset-manifest.json`: actual selection counts, dataset ID and processed-file hashes.
- `index-manifest.json`: model archive checksum, index version, chunk count and first indexing duration.
- `sample-input.json` / `sample-output.json`: one successful retrieval request; saved source excerpts are shortened to 25 words each.
- `evaluation.json`: 20 fixed queries for each method, per-case results and measured HTTP latency.
- `tests.txt`: 18 tests passed inside the test container.
- `initial-download.txt`: first source download from UCSD.
- `compose-up.txt` / `pipeline-run.txt`: final one-command replay with verified cached data/index.
- `containers.json` / `containers.txt`: actual Docker Compose service state. Batch stages exit with code 0; API and web remain running.
- `app-overview.png`, `app-search.png`, `app-sources.png`, `app-boston-filter.png`, `api-running.png`: browser captures of the running local app/API.

Browser checks covered semantic search, Boston/Cambridge city and category filters, source details, baseline switching, saved-place persistence across reload, and shortlist download. No automated browser-test coverage is claimed. Docker Desktop's native screenshot could not be captured; the CLI state and running API/app screenshots are supplied instead.

Timing varies by machine and load. Re-running the pipeline regenerates JSON evidence; refresh screenshots after UI changes. Captured text logs have normalized line endings/trailing whitespace. The container JSON retains service state and ports, omitting Docker labels with local paths.
