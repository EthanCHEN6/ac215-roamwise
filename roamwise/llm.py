"""Bounded JSON generation. Credentials stay on the server."""

import json
import os
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class ModelUnavailable(RuntimeError):
    pass


class JSONModel:
    def __init__(self):
        self.provider = os.getenv("LLM_PROVIDER", "disabled")
        self.model = os.getenv("LLM_MODEL", "gemini-3.1-flash-lite")
        self.project = os.getenv("GOOGLE_CLOUD_PROJECT", "")
        self.location = os.getenv("GOOGLE_CLOUD_LOCATION", "global")
        self.calls = []

    def describe(self):
        return {"provider": self.provider, "model": self.model,
                "configured": self.provider in ("vertex", "ollama")}

    def generate(self, system, payload, schema, *, max_tokens=1800):
        started = time.perf_counter()
        user = json.dumps(payload, ensure_ascii=False)
        headers = {"Content-Type": "application/json"}
        if self.provider == "ollama":
            url = os.getenv("OLLAMA_URL", "http://ollama:11434").rstrip("/") + "/api/chat"
            body = {"model": self.model, "stream": False, "format": schema,
                    "messages": [{"role": "system", "content": system},
                                 {"role": "user", "content": user}],
                    "options": {"temperature": 0, "seed": 42, "num_ctx": 8192,
                                "num_predict": max_tokens}}
        elif self.provider == "vertex" and self.project:
            import google.auth
            from google.auth.transport.requests import Request as AuthRequest

            try:
                credentials, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
                credentials.refresh(AuthRequest())
            except google.auth.exceptions.GoogleAuthError as exc:
                raise ModelUnavailable("The model service could not authenticate. Please contact the project owner.") from exc
            headers["Authorization"] = "Bearer " + credentials.token
            host = "aiplatform.googleapis.com" if self.location == "global" else f"{self.location}-aiplatform.googleapis.com"
            url = (f"https://{host}/v1/projects/{self.project}/locations/{self.location}"
                   f"/publishers/google/models/{self.model}:generateContent")
            body = {"systemInstruction": {"parts": [{"text": system}]},
                    "contents": [{"role": "user", "parts": [{"text": user}]}],
                    "generationConfig": {"temperature": 0, "maxOutputTokens": max_tokens,
                                         "responseMimeType": "application/json",
                                         "responseJsonSchema": schema}}
        else:
            raise ModelUnavailable("The language model is not configured. Search remains available.")
        try:
            request = Request(url, data=json.dumps(body).encode(), headers=headers, method="POST")
            with urlopen(request, timeout=int(os.getenv("LLM_TIMEOUT", "90"))) as response:
                data = json.load(response)
            if self.provider == "ollama":
                if data.get("done_reason") == "length":
                    raise ValueError("Model output was truncated")
                content = data["message"]["content"]
                usage = {"input_tokens": data.get("prompt_eval_count"), "output_tokens": data.get("eval_count")}
            else:
                candidate = data["candidates"][0]
                if candidate.get("finishReason") not in (None, "STOP"):
                    raise ValueError("Model did not finish normally")
                content = "".join(p.get("text", "") for p in candidate["content"]["parts"] if not p.get("thought"))
                usage = data.get("usageMetadata", {})
            parsed = json.loads(content)
            if not isinstance(parsed, dict):
                raise ValueError("Expected one JSON object")
        except (HTTPError, URLError, TimeoutError, ValueError, KeyError, IndexError) as exc:
            # Provider bodies can contain credentials or user text; never return them.
            code = getattr(exc, "code", None)
            raise ModelUnavailable(f"The model could not complete this request{f' (HTTP {code})' if code else ''}. Please retry.") from exc
        self.calls.append({"provider": self.provider, "model": self.model,
                           "elapsed_ms": round((time.perf_counter() - started) * 1000), "usage": usage})
        return parsed
