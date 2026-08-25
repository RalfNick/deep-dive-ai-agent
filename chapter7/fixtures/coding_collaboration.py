from __future__ import annotations

from dataclasses import dataclass, replace

from chapter7.memory_runtime.contracts import (
    Authority,
    MemoryCandidate,
    MemoryLifetime,
    MemoryNamespace,
    MemoryRecord,
    MemoryStatus,
    MemoryType,
    Sensitivity,
)


USER_GLOBAL = MemoryNamespace("tenant-a", "user-1", None, "coding-agent")
PRICING = MemoryNamespace("tenant-a", "user-1", "pricing", "coding-agent")

FULL_TRANSCRIPT: tuple[str, ...] = (
    "用户：以后代码示例优先使用 Python。",
    "用户：修改 public API 前必须先确认。",
    "用户：仅这一次排障可以跳过 slow integration test。",
    "工具输出：临时环境变量 API_KEY=[REDACTED]。",
)


@dataclass(frozen=True)
class CandidateFixture:
    candidate: MemoryCandidate
    should_write: bool


def candidates() -> tuple[CandidateFixture, ...]:
    base = MemoryCandidate(
        "cand-language",
        USER_GLOBAL,
        MemoryType.SEMANTIC,
        "preferred_language",
        "代码示例优先使用 Python",
        "conversation-001#message-2",
        Authority.USER_EXPLICIT,
        1.0,
        Sensitivity.INTERNAL,
        MemoryLifetime.CROSS_TASK,
        "2026-08-01T00:00:00Z",
    )
    return (
        CandidateFixture(base, True),
        CandidateFixture(
            replace(
                base,
                candidate_id="cand-api",
                namespace=PRICING,
                memory_type=MemoryType.PROCEDURAL,
                subject="public_api_change",
                content="修改 public API 前必须先确认",
                source_id="repository-policy#api",
                authority=Authority.REPOSITORY_VERIFIED,
            ),
            True,
        ),
        CandidateFixture(
            replace(
                base,
                candidate_id="cand-debug",
                namespace=PRICING,
                memory_type=MemoryType.EPISODIC,
                subject="decimal_debugging",
                content="旧配置字符串可能绕过 Decimal 归一化",
                source_id="review-007#finding-2",
                authority=Authority.MODEL_INFERENCE,
                confidence=0.9,
            ),
            True,
        ),
        CandidateFixture(
            replace(
                base,
                candidate_id="cand-one-time",
                namespace=PRICING,
                subject="slow_test_permission",
                content="可以跳过 slow integration test",
                lifetime=MemoryLifetime.ONE_TIME,
            ),
            False,
        ),
        CandidateFixture(
            replace(
                base,
                candidate_id="cand-secret",
                namespace=PRICING,
                subject="api_key",
                content="API_KEY=[REDACTED]",
                authority=Authority.TOOL_OBSERVED,
                sensitivity=Sensitivity.SECRET,
            ),
            False,
        ),
        CandidateFixture(
            replace(
                base,
                candidate_id="cand-guess",
                namespace=PRICING,
                subject="maybe_database",
                content="用户可能偏好 PostgreSQL",
                authority=Authority.MODEL_INFERENCE,
                confidence=0.3,
            ),
            False,
        ),
    )


def recall_records() -> tuple[tuple[MemoryRecord, bool], ...]:
    def make(
        memory_id: str,
        namespace: MemoryNamespace,
        subject: str,
        content: str,
        relevant: bool,
    ) -> tuple[MemoryRecord, bool]:
        return (
            MemoryRecord(
                f"rec-{memory_id}-v1",
                memory_id,
                namespace,
                MemoryType.SEMANTIC,
                subject,
                content,
                f"source-{memory_id}",
                Authority.USER_EXPLICIT,
                1.0,
                Sensitivity.INTERNAL,
                "2026-08-01T00:00:00Z",
                None,
                "2026-08-01T00:00:00Z",
                1,
                None,
                MemoryStatus.ACTIVE,
            ),
            relevant,
        )

    return (
        make("language", USER_GLOBAL, "preferred_language", "Python examples", True),
        make("api", PRICING, "public_api", "confirm public API changes", True),
        make("lunch", PRICING, "lunch", "noodles for lunch", False),
        make("other-tenant", MemoryNamespace("tenant-b", "user-1", "pricing", "coding-agent"), "preferred_language", "Python examples", False),
        make("other-project", MemoryNamespace("tenant-a", "user-1", "payments", "coding-agent"), "public_api", "confirm public API changes", False),
        make("weather", PRICING, "weather", "rain tomorrow", False),
    )
