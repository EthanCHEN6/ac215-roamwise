# Share the MS2 demo

**Public entry:** https://ethan-roamwise-ms2.thomaslinnn.chatgpt.site

The entry page contains three recorded API queries, method switching, source excerpts, slides and repository downloads. It is a static site, so these remain available when the demo computer is off. Recorded results are labeled; the page does not run live inference.

**Live search:** use the entry page's “Open live search” button. A Cloudflare Quick Tunnel forwards requests to the Docker web service. The Python API, model and index continue to run in their containers on the demo computer. Visitors need no account or installation.

The computer must stay awake, connected to the internet, with Docker and the tunnel running. Locking the screen is fine; sleeping, shutting down or stopping Docker interrupts live search. The public URL changes when a new tunnel is created. This is a temporary classroom demo, with no uptime guarantee, not a cloud backend deployment. [Cloudflare Quick Tunnel documentation](https://developers.cloudflare.com/tunnel/get-started/quick-tunnels/).

## Start or stop live sharing

First start the normal pipeline and wait until its API is healthy:

```powershell
docker compose up --build -d
.\scripts\share.ps1
```

The script starts the optional tunnel container, prints its address and updates `share/live.json`. It does not publish Git changes. If the address changed, send the new address directly, or commit and push `share/live.json` to `main`; the static entry reads that public link record. A failed link-record fetch falls back to the address embedded in the static page.

Stop public access while keeping the local app running:

```powershell
.\scripts\share.ps1 -Stop
```

On other operating systems, use `docker compose --profile share up -d --no-deps tunnel`, then `docker compose logs tunnel` to find the URL. Stop with `docker compose --profile share stop tunnel`.

## Refresh the recorded examples

With the existing containers running, execute the export inside the uv evaluation image:

```bash
docker compose run --rm --no-deps -v ./scripts:/scripts:ro -v ./share:/export evaluate uv run --frozen --no-sync python /scripts/export_share_examples.py
```

The script records three queries using both methods, with three places per query and source excerpts capped at 25 words. `share/site/` contains the static showcase source and assets; deploy updated static assets through Sites when the examples or presentation change.

The shared web proxy caps request bodies and limits search bursts. Sharing exposes the RoamWise website/API, not a filesystem server. Source data is historical; this is not a live travel directory.
