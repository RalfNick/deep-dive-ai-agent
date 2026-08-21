"""Validate the public book publication contract."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ALLOWED_STATUSES = {"published", "writing", "planned"}
PUBLICATION_FIELDS = {"source", "experiment", "answers"}
REQUIRED_BOOK_FIELDS = {
    "slug",
    "title",
    "subtitle",
    "description",
    "version",
    "updated",
    "cover",
    "repositoryUrl",
    "totalChapters",
    "introduction",
    "sections",
}
REQUIRED_ENTRY_FIELDS = {"slug", "title", "status", "summary"}


def _resolve_inside(
    base: Path, relative_path: str, boundary: Path, label: str
) -> Path:
    path = (base / relative_path).resolve()
    try:
        path.relative_to(boundary.resolve())
    except ValueError as error:
        raise ValueError(f"{label} escapes repository root: {relative_path}") from error
    return path


def _require_fields(value: dict[str, Any], required: set[str], label: str) -> None:
    missing = required.difference(value)
    if missing:
        raise ValueError(f"{label} missing fields: {', '.join(sorted(missing))}")


def validate_manifest(root: Path) -> dict[str, Any]:
    """Load and validate ``book/manifest.json`` relative to a repository root."""

    repository_root = root.resolve()
    manifest_path = repository_root / "book" / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise ValueError("manifest root must be an object")

    _require_fields(manifest, REQUIRED_BOOK_FIELDS, "manifest")
    if manifest["totalChapters"] != 18:
        raise ValueError("totalChapters must equal 18")

    cover_path = _resolve_inside(
        repository_root / "book",
        manifest["cover"],
        repository_root / "book",
        "cover",
    )
    if not cover_path.is_file():
        raise FileNotFoundError(manifest["cover"])

    introduction = manifest["introduction"]
    _require_fields(
        introduction,
        REQUIRED_ENTRY_FIELDS | {"source", "updated"},
        "introduction",
    )
    if introduction["status"] != "published":
        raise ValueError("introduction must be published")
    introduction_path = _resolve_inside(
        repository_root / "book",
        introduction["source"],
        repository_root / "book",
        "introduction source",
    )
    if not introduction_path.is_file():
        raise FileNotFoundError(introduction["source"])

    sections = manifest["sections"]
    if not isinstance(sections, list) or not sections:
        raise ValueError("sections must be a non-empty array")
    if [section.get("order") for section in sections] != list(range(1, len(sections) + 1)):
        raise ValueError("sections must use contiguous one-based order")

    chapters = [chapter for section in sections for chapter in section.get("chapters", [])]
    if [chapter.get("order") for chapter in chapters] != list(range(1, 19)):
        raise ValueError("chapters must be ordered from 1 through 18")

    slugs = [introduction["slug"]] + [chapter.get("slug") for chapter in chapters]
    if len(slugs) != len(set(slugs)):
        raise ValueError("entry slugs must be unique")

    for chapter in chapters:
        _require_fields(chapter, REQUIRED_ENTRY_FIELDS | {"order"}, chapter.get("slug", "chapter"))
        status = chapter["status"]
        if status not in ALLOWED_STATUSES:
            raise ValueError(f"invalid chapter status: {status}")
        if status != "published":
            exposed = sorted(PUBLICATION_FIELDS.intersection(chapter))
            if exposed:
                raise ValueError(
                    f"unpublished chapter exposes files: {chapter['slug']} ({', '.join(exposed)})"
                )
            continue

        _require_fields(
            chapter,
            REQUIRED_ENTRY_FIELDS
            | {"order", "source", "updated", "experiment", "answers"},
            chapter["slug"],
        )
        for field in PUBLICATION_FIELDS:
            path = _resolve_inside(
                repository_root / "book",
                chapter[field],
                repository_root,
                field,
            )
            if not path.is_file():
                raise FileNotFoundError(chapter[field])

    return manifest
