"""One container serves the static interface and Python API on Cloud Run."""

from collections import deque
import os
import time

from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from roamwise.api import create_app
from roamwise.common import ROOT


class RequestLimits:
    def __init__(self, app):
        self.app = app
        self.active = 0
        self.requests = deque()

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            original_send = send
            async def secured_send(message):
                if message["type"] == "http.response.start":
                    message["headers"] = list(message.get("headers", [])) + [
                        (b"x-content-type-options", b"nosniff"),
                        (b"referrer-policy", b"strict-origin-when-cross-origin"),
                        (b"x-frame-options", b"DENY"),
                    ]
                await original_send(message)
            send = secured_send
            if scope["method"] == "POST":
                body = bytearray()
                while True:
                    message = await receive()
                    if message["type"] == "http.disconnect":
                        return
                    body.extend(message.get("body", b""))
                    if len(body) > 16384:
                        return await JSONResponse({"detail": "Request body exceeds 16 KB."}, status_code=413)(scope, receive, send)
                    if not message.get("more_body", False):
                        break
                original_receive, delivered = receive, False
                async def buffered_receive():
                    nonlocal delivered
                    if not delivered:
                        delivered = True
                        return {"type": "http.request", "body": bytes(body), "more_body": False}
                    return await original_receive()
                receive = buffered_receive
        costly = scope["type"] == "http" and (scope["path"] in ("/api/search", "/api/recommend", "/api/itinerary") or scope["path"].endswith("/live"))
        if not costly or scope["method"] == "OPTIONS":
            return await self.app(scope, receive, send)
        now = time.monotonic()
        while self.requests and now - self.requests[0] > 3600:
            self.requests.popleft()
        if self.active >= 2 or len(self.requests) >= int(os.getenv("REQUESTS_PER_HOUR", "60")):
            return await JSONResponse({"detail": "The shared demo is busy or its hourly allowance is used. Please try later."},
                                      status_code=429, headers={"Retry-After": "30"})(scope, receive, send)
        self.active += 1
        self.requests.append(now)
        try:
            return await self.app(scope, receive, send)
        finally:
            self.active -= 1


def create_cloud_app(engine=None, language_model=None):
    application = create_app(engine, language_model)
    application.add_middleware(RequestLimits)
    origins = [s.strip() for s in os.getenv("CORS_ORIGINS", "https://ethan-roamwise-ms2.thomaslinnn.chatgpt.site").split(",") if s.strip()]
    application.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=["GET", "POST"], allow_headers=["Content-Type"])
    application.mount("/", StaticFiles(directory=ROOT / "frontend", html=True), name="web")
    return application


app = create_cloud_app()
