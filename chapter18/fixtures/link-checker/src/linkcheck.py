"""Trusted teaching fixture, deliberately missing nested-relative resolution."""
import posixpath
from urllib.parse import urlsplit
from policy import EXTERNAL_SCHEMES


def resolve_link(document: str, target: str) -> str | None:
    if not target:
        return None
    parsed = urlsplit(target)
    if parsed.scheme in EXTERNAL_SCHEMES:
        return None
    path = parsed.path
    if path.startswith("/"):
        return path.lstrip("/")
    return path
