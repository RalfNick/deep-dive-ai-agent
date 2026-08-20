from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from .contracts import (
    ContextItem,
    ContextKind,
    InstructionAuthority,
    Provenance,
    RawSource,
    RetentionPriority,
    Scope,
    Sensitivity,
    TrustLevel,
)


@dataclass(frozen=True)
class ChannelRule:
    kind: ContextKind
    authority: InstructionAuthority
    trust: TrustLevel
    retention: RetentionPriority
    sensitivity: Sensitivity


CHANNEL_RULES: dict[str, ChannelRule] = {
    "system": ChannelRule(
        ContextKind.INSTRUCTION,
        InstructionAuthority.SYSTEM,
        TrustLevel.VERIFIED,
        RetentionPriority.REQUIRED,
        Sensitivity.INTERNAL,
    ),
    "developer": ChannelRule(
        ContextKind.INSTRUCTION,
        InstructionAuthority.DEVELOPER,
        TrustLevel.VERIFIED,
        RetentionPriority.REQUIRED,
        Sensitivity.INTERNAL,
    ),
    "repository_rule": ChannelRule(
        ContextKind.INSTRUCTION,
        InstructionAuthority.REPOSITORY,
        TrustLevel.TRUSTED_SOURCE,
        RetentionPriority.HIGH,
        Sensitivity.INTERNAL,
    ),
    "user_request": ChannelRule(
        ContextKind.TASK,
        InstructionAuthority.NONE,
        TrustLevel.TRUSTED_SOURCE,
        RetentionPriority.REQUIRED,
        Sensitivity.INTERNAL,
    ),
    "user_instruction": ChannelRule(
        ContextKind.INSTRUCTION,
        InstructionAuthority.USER,
        TrustLevel.TRUSTED_SOURCE,
        RetentionPriority.REQUIRED,
        Sensitivity.INTERNAL,
    ),
    "repository_file": ChannelRule(
        ContextKind.ARTIFACT,
        InstructionAuthority.NONE,
        TrustLevel.TRUSTED_SOURCE,
        RetentionPriority.NORMAL,
        Sensitivity.INTERNAL,
    ),
    "tool_observation": ChannelRule(
        ContextKind.OBSERVATION,
        InstructionAuthority.NONE,
        TrustLevel.VERIFIED,
        RetentionPriority.HIGH,
        Sensitivity.INTERNAL,
    ),
    "verified_fact": ChannelRule(
        ContextKind.FACT,
        InstructionAuthority.NONE,
        TrustLevel.VERIFIED,
        RetentionPriority.HIGH,
        Sensitivity.INTERNAL,
    ),
    "web_content": ChannelRule(
        ContextKind.FACT,
        InstructionAuthority.NONE,
        TrustLevel.UNVERIFIED,
        RetentionPriority.LOW,
        Sensitivity.PUBLIC,
    ),
    "tool_schema": ChannelRule(
        ContextKind.TOOL_SCHEMA,
        InstructionAuthority.NONE,
        TrustLevel.VERIFIED,
        RetentionPriority.HIGH,
        Sensitivity.INTERNAL,
    ),
    "hostile_fixture": ChannelRule(
        ContextKind.ARTIFACT,
        InstructionAuthority.NONE,
        TrustLevel.HOSTILE,
        RetentionPriority.LOW,
        Sensitivity.INTERNAL,
    ),
    "secret_fixture": ChannelRule(
        ContextKind.FACT,
        InstructionAuthority.NONE,
        TrustLevel.VERIFIED,
        RetentionPriority.REQUIRED,
        Sensitivity.SECRET,
    ),
}


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


class SourcePolicy:
    """Assign identity and policy metadata from a controlled loading channel."""

    def classify(
        self,
        raw: RawSource,
        *,
        repository: str,
        task_id: str,
        required_for: frozenset[str] = frozenset(),
    ) -> ContextItem:
        if not raw.content.strip():
            raise ValueError("blank_source_content")
        rule = CHANNEL_RULES.get(raw.channel)
        if rule is None:
            raise ValueError("unknown_source_channel")

        content_digest = _sha256_text(raw.content)
        identity = json.dumps(
            {
                "channel": raw.channel,
                "content_digest": content_digest,
                "observed_at": raw.observed_at,
                "path": raw.path,
                "repository": repository,
                "source_id": raw.source_id,
                "task_id": task_id,
                "version": raw.version,
            },
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        item_id = f"ctx-{_sha256_text(identity)[:20]}"
        return ContextItem(
            item_id=item_id,
            kind=rule.kind,
            content=raw.content,
            scope=Scope(repository=repository, path_prefix=raw.path, task_id=task_id),
            authority=rule.authority,
            trust=rule.trust,
            retention_priority=rule.retention,
            sensitivity=rule.sensitivity,
            provenance=Provenance(
                source_type=raw.channel,
                source_id=raw.source_id,
                version=raw.version,
                observed_at=raw.observed_at,
                content_digest=content_digest,
            ),
            required_for=required_for,
        )
