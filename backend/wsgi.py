"""WSGI entry point for gunicorn / production deployment."""
import os
import sys

# Ensure the project root (parent of this directory) is importable so that
# absolute imports like `from backend.digital_twin.simulator import ...`
# resolve regardless of the working directory the server is launched from.
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from backend.main import app  # noqa: E402

__all__ = ["app"]
