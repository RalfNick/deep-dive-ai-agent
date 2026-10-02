"""Only eligible, task-needed fragments enter a worker's context."""
from hashlib import sha256
import json

from .contracts import ContextSnapshot, SourceDoc, TaskPacket, validate_packet


def eligible(packet: TaskPacket, source: SourceDoc) -> bool:
    return (source.source_id in packet.allowed_sources and packet.principal in source.principals
            and source.eligible and source.version == packet.target_version)


def assemble_context(packet: TaskPacket, sources: tuple[SourceDoc, ...]) -> ContextSnapshot:
    validate_packet(packet)
    sent, digests = [], []
    for source in sorted(sources, key=lambda s: s.source_id):
        if not eligible(packet, source):
            continue
        values = [value for key, value in source.facts if key in packet.input_refs]
        lines = tuple(line for line in source.text.splitlines() if line and not line.startswith("#")
                      and any(value in line for value in values))
        if lines:
            sent.append((source.source_id, "\n".join(lines)))
            digests.append((source.source_id, source.digest))
    payload = json.dumps(sent, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return ContextSnapshot(packet.task_id, packet.principal, packet.target_version, tuple(sent),
                           sha256(payload).hexdigest(), tuple(digests))
