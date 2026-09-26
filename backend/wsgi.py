"""WSGI entry point that bridges gunicorn (WSGI) to the FastAPI (ASGI) app.

Render's existing service runs:
    gunicorn ... wsgi:app
gunicorn is a WSGI server, but FastAPI is an ASGI application, so we wrap it
here with a small synchronous WSGI -> ASGI bridge. This lets the current
start command work without changing the Render dashboard settings.
"""
import asyncio
import os
import sys

# Ensure the project root is importable so absolute imports
# (e.g. `from backend.digital_twin.simulator import ...`) resolve regardless
# of the working directory the server is launched from.
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from backend.main import app as _asgi_app  # noqa: E402


def _build_scope(environ: dict) -> dict:
    """Convert a WSGI environ into an ASGI HTTP scope."""
    headers = []
    for key, value in environ.items():
        if key.startswith("HTTP_"):
            headers.append((key[5:].lower().replace("_", "-"), value))
        elif key in ("CONTENT_TYPE", "CONTENT_LENGTH"):
            headers.append((key.lower().replace("_", "-"), value))

    return {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.1"},
        "http_version": "1.1",
        "method": environ["REQUEST_METHOD"],
        "scheme": environ.get("wsgi.url_scheme", "http"),
        "path": environ["PATH_INFO"],
        "query_string": environ["QUERY_STRING"].encode("latin-1"),
        "headers": [
            (k.lower().encode("latin-1"), v.encode("latin-1")) for k, v in headers
        ],
        "client": (environ.get("REMOTE_ADDR", ""), 0),
        "server": (environ.get("SERVER_NAME", ""), int(environ.get("SERVER_PORT", 80))),
        "root_path": environ.get("SCRIPT_NAME", ""),
    }


def app(environ, start_response):
    """WSGI callable that runs the ASGI app synchronously."""
    scope = _build_scope(environ)
    stream = environ.get("wsgi.input")

    async def receive():
        body = stream.read(65536) if stream is not None else b""
        return {"type": "http.request", "body": body, "more_body": False}

    body_chunks = []
    response = {"status": 500, "headers": []}

    async def send(message):
        if message["type"] == "http.response.start":
            response["status"] = message["status"]
            response["headers"] = message.get("headers", [])
        elif message["type"] == "http.response.body":
            body_chunks.append(message.get("body", b""))

    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(_asgi_app(scope, receive, send))
    finally:
        loop.close()

    header_list = [
        (k.decode("latin-1"), v.decode("latin-1")) for k, v in response["headers"]
    ]
    start_response(f"{response['status']} {response['status']}", header_list)
    return body_chunks


__all__ = ["app"]