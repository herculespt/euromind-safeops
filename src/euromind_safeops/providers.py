"""Untrusted advisory providers: never return executable actions."""

from __future__ import annotations

import json
import os
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from .core import SafeOpsError


def offline_advice(task: str, specialist: str) -> str:
    return (f"Suggested reviewer: {specialist}. Confirm requirements and affected files; "
            "implement changes separately, run tests and inspect security consequences. "
            "This advisory output does not authorize commands or file modifications.")


def remote_advice(task: str, *, endpoint: str, model: str, allow_remote: bool, timeout: int = 15) -> str:
    """Call an OpenAI-compatible /chat/completions endpoint with task text ONLY."""
    if not allow_remote:
        raise SafeOpsError("Remote provider requires explicit --allow-remote")
    parsed = urlparse(endpoint)
    if parsed.username or parsed.password or parsed.fragment or parsed.query:
        raise SafeOpsError("Endpoint must not contain credentials, query or fragment")
    if not ((parsed.scheme == "https" and parsed.hostname) or
            (parsed.scheme == "http" and parsed.hostname in ("localhost", "127.0.0.1", "::1"))):
        raise SafeOpsError("Endpoint must use HTTPS or local loopback HTTP")
    if not endpoint.rstrip("/").endswith("/chat/completions"):
        raise SafeOpsError("Endpoint must end in /chat/completions")
    if not model or len(model) > 120:
        raise SafeOpsError("--model is required (max 120 characters)")
    if len(task) > 2000:
        raise SafeOpsError("Task too long")
    api_key = os.environ.get("SAFEOPS_API_KEY", "")
    payload = {
        "model": model,
        "temperature": 0,
        "max_tokens": 500,
        "messages": [
            {"role": "system", "content": "You are an engineering reviewer. Give concise high-level advisory suggestions only. Do not output executable shell commands, credentials, or instructions to bypass approvals."},
            {"role": "user", "content": task},
        ],
    }
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    request = Request(endpoint, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
    try:
        # urllib can follow HTTP redirects. Rejecting cross-origin redirects needs a strict handler.
        from urllib.request import build_opener, HTTPRedirectHandler
        class DenyRedirect(HTTPRedirectHandler):
            def redirect_request(self, req, fp, code, msg, hdrs, newurl):
                raise SafeOpsError("Provider redirects are forbidden")
        with build_opener(DenyRedirect()).open(request, timeout=timeout) as response:
            data = response.read(256_001)
        if len(data) > 256_000:
            raise SafeOpsError("Provider response too large")
        result = json.loads(data)
        answer = result["choices"][0]["message"]["content"]
        if not isinstance(answer, str):
            raise ValueError("Missing textual answer")
        return answer[:6000]
    except SafeOpsError:
        raise
    except Exception as exc:
        # Do not echo exception strings: URLs/providers may leak request details.
        raise SafeOpsError(f"Provider call failed ({type(exc).__name__})") from exc
