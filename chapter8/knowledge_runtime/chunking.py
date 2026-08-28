from __future__ import annotations

import re

from chapter8.knowledge_runtime.contracts import Chunk, KnowledgeDocument


_HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*$")


def fixed_character_chunks(
    document: KnowledgeDocument,
    max_chars: int,
    overlap_chars: int,
) -> tuple[Chunk, ...]:
    if max_chars <= 0:
        raise ValueError("non_positive_max_chars")
    if overlap_chars < 0 or overlap_chars >= max_chars:
        raise ValueError("invalid_overlap_chars")
    chunks: list[Chunk] = []
    start = 0
    while start < len(document.content):
        end = min(len(document.content), start + max_chars)
        chunks.append(
            Chunk.from_document(
                document,
                ordinal=len(chunks),
                heading_path=(),
                content=document.content[start:end],
            )
        )
        if end == len(document.content):
            break
        start = end - overlap_chars
    return tuple(chunks)


def _markdown_sections(markdown: str) -> tuple[tuple[tuple[str, ...], str], ...]:
    headings: list[str] = []
    active_path: tuple[str, ...] = ()
    body: list[str] = []
    sections: list[tuple[tuple[str, ...], str]] = []
    in_fence = False
    fence_marker = ""

    def flush() -> None:
        content = "\n".join(body).strip()
        if content:
            sections.append((active_path, content))
        body.clear()

    for line in markdown.splitlines():
        stripped = line.lstrip()
        if stripped.startswith(("```", "~~~")):
            marker = stripped[:3]
            if not in_fence:
                in_fence = True
                fence_marker = marker
            elif marker == fence_marker:
                in_fence = False
                fence_marker = ""
            body.append(line)
            continue
        match = None if in_fence else _HEADING.match(line)
        if match is None:
            body.append(line)
            continue
        flush()
        level = len(match.group(1))
        title = match.group(2).strip()
        headings[:] = headings[: level - 1]
        while len(headings) < level - 1:
            headings.append("")
        headings.append(title)
        active_path = tuple(item for item in headings if item)
    flush()
    return tuple(sections)


def _atomic_blocks(content: str) -> tuple[str, ...]:
    blocks: list[str] = []
    current: list[str] = []
    in_fence = False
    fence_marker = ""

    def flush() -> None:
        block = "\n".join(current).strip()
        if block:
            blocks.append(block)
        current.clear()

    for line in content.splitlines():
        stripped = line.lstrip()
        if stripped.startswith(("```", "~~~")):
            marker = stripped[:3]
            if not in_fence:
                in_fence = True
                fence_marker = marker
            elif marker == fence_marker:
                in_fence = False
                fence_marker = ""
            current.append(line)
            continue
        if not in_fence and not line.strip():
            flush()
            continue
        current.append(line)
    flush()
    return tuple(blocks)


def _pack_section(content: str, max_chars: int) -> tuple[str, ...]:
    packed: list[str] = []
    current = ""
    for block in _atomic_blocks(content):
        if len(block) > max_chars and not block.lstrip().startswith(("```", "|")):
            pieces = tuple(block[index : index + max_chars] for index in range(0, len(block), max_chars))
        else:
            pieces = (block,)
        for piece in pieces:
            candidate = piece if not current else f"{current}\n\n{piece}"
            if current and len(candidate) > max_chars:
                packed.append(current)
                current = piece
            else:
                current = candidate
    if current:
        packed.append(current)
    return tuple(packed)


def structure_aware_chunks(document: KnowledgeDocument, max_chars: int) -> tuple[Chunk, ...]:
    if max_chars <= 0:
        raise ValueError("non_positive_max_chars")
    chunks: list[Chunk] = []
    for heading_path, content in _markdown_sections(document.content):
        for piece in _pack_section(content, max_chars):
            chunks.append(
                Chunk.from_document(
                    document,
                    ordinal=len(chunks),
                    heading_path=heading_path,
                    content=piece,
                )
            )
    return tuple(chunks)


def contextualize_chunks(
    document: KnowledgeDocument,
    chunks: tuple[Chunk, ...],
) -> tuple[Chunk, ...]:
    version = document.version_min
    if document.version_max is not None and document.version_max != document.version_min:
        version = f"{document.version_min}–{document.version_max}"
    contextual: list[Chunk] = []
    for chunk in chunks:
        section = " > ".join(chunk.heading_path) if chunk.heading_path else "正文"
        prefix = f"文档：{document.title}；版本：{version}；章节：{section}"
        contextual.append(
            Chunk.from_document(
                document,
                ordinal=chunk.ordinal,
                heading_path=chunk.heading_path,
                content=chunk.content,
                context_prefix=prefix,
            )
        )
    return tuple(contextual)
