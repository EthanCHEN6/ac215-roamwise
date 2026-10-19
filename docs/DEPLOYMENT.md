# Deploy to Cloud Run

Cloud Run serves the complete website and API at one HTTPS URL. The owner's laptop can be off. Idle instances scale to zero; the next visit may wait for startup.

1. Run the pipeline and container tests.
2. Export the verified snapshot: `pwsh scripts/export_snapshot.ps1`.
3. Sign in with Google Cloud CLI. Use a project with billing and deployment permission.
4. From the repository root, run:

```powershell
pwsh deploy/cloud-run.ps1 -ProjectId YOUR_PROJECT_ID
```

The script enables APIs, creates an Artifact Registry repository and runtime service account, builds an image in Cloud Build, and deploys a public service. The build recreates the index from the verified snapshot. New source data requires a new snapshot and image.

The default model is `gemini-3.1-flash-lite` on Vertex AI's global endpoint. Check availability and pricing for your project. Runtime authentication uses the attached service account, not a downloaded key.

## Costs and controls

Configuration: 1 CPU, 2 GiB memory, minimum 0 instances, maximum 1, concurrency 8 and a 300-second HTTP timeout. The app permits two expensive requests at once and 60 per process per hour. Restarts reset that counter.

Cloud Run, Cloud Build, Artifact Registry, Vertex AI and optional Places requests can incur charges. Course credits apply only if the billing account provides them. These limits do not impose a hard spending cap. Set a billing alert and review usage after sharing.

To stop public access, remove the service's `allUsers` Cloud Run Invoker binding. To stop the service, delete only `roamwise-rag` after confirming its project and region. Stored images and build artifacts can still incur charges.

## Verify and maintain

Check `/api/health` and `/api/status`, load the static pages, then run recommendations and generate an itinerary. Inspect sources and validation results. A health check alone does not test model access.

Mount local test credentials read-only outside the image. Never copy ADC files, API keys or CLI configuration into the build context. The ignore files exclude unnecessary data and local evidence.

A separately hosted frontend sets `frontend/config.js` to the Cloud Run URL. Add its exact origin to `CORS_ORIGINS`. Same-origin Cloud Run hosting uses an empty `apiBase`.
