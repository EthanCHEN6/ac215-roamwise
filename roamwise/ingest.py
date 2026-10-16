"""Download the two upstream files; reject changed snapshots before processing."""

import time
import urllib.request
from pathlib import Path

from roamwise.common import (
    DATA,
    EVIDENCE,
    ROOT,
    log,
    now,
    read_json,
    sha256,
    write_json,
)


def download(source, destination):
    expected = source.get("sha256")
    if destination.exists():
        actual = sha256(destination)
        if not expected or actual == expected:
            log(
                "download_cached",
                file=destination.name,
                bytes=destination.stat().st_size,
            )
            return actual
        raise ValueError(
            f"Cached checksum mismatch: {destination.name}. Remove the corrupt file and retry."
        )
    partial = destination.with_suffix(destination.suffix + ".partial")
    for attempt in range(3):
        try:
            request = urllib.request.Request(
                source["url"],
                headers={"User-Agent": "RoamWise-AC215/0.1 (academic project)"},
            )
            with (
                urllib.request.urlopen(request, timeout=120) as response,
                partial.open("wb") as output,
            ):
                size = 0
                next_report = 50 * 1024 * 1024
                while block := response.read(1024 * 1024):
                    output.write(block)
                    size += len(block)
                    if size >= next_report:
                        log(
                            "download_progress",
                            file=destination.name,
                            megabytes=round(size / 1e6),
                        )
                        next_report += 50 * 1024 * 1024
            actual = sha256(partial)
            if expected and actual != expected:
                raise ValueError(f"Upstream checksum mismatch: {destination.name}")
            partial.replace(destination)
            log("download_complete", file=destination.name, bytes=size, sha256=actual)
            return actual
        except (OSError, TimeoutError) as error:
            log("download_retry", attempt=attempt + 1, error=str(error))
            if attempt == 2:
                raise
            time.sleep(2**attempt)


def main():
    sources = read_json(ROOT / "config/sources.json")
    raw = DATA / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    files = []
    for source in sources["files"]:
        path = raw / source["name"]
        digest = download(source, path)
        files.append({**source, "sha256": digest, "bytes": path.stat().st_size})
    manifest = {"dataset": sources["dataset"], "checked_at": now(), "files": files}
    write_json(raw / "manifest.json", manifest)
    write_json(EVIDENCE / "source-manifest.json", manifest)
    log("ingest_complete", files=len(files))


if __name__ == "__main__":
    main()
