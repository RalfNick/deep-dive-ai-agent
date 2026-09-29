"""Expand explicit fixture defaults; neither the agent nor lessons receive truth."""
import json
from pathlib import Path
from .contracts import (CLOCK, AgentInput, Document, FeedbackRecord, FixtureSet,
                        ReplayCase, Scope, SourceAuthority, SuccessCondition, TaskSpec)

def validate_fixtures(lab):
    dev = {t.family_id for t in lab.tasks if t.split == "development"}
    hold = {t.family_id for t in lab.tasks if t.split == "holdout"}
    if dev & hold:
        raise ValueError("family crosses discovery/holdout boundary")
    for group, key in ((lab.feedback, "feedback_id"), (lab.sources, "source_id"),
                       (lab.documents, "document_id"), (lab.tasks, "task_id"), (lab.truth, "success_ref")):
        ids = [getattr(x, key) for x in group]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate fixture ID")
    refs = {x.success_ref for x in lab.truth}
    if any(t.success_ref not in refs for t in lab.tasks):
        raise ValueError("missing truth reference")
    return lab

def load_fixtures(directory: Path | None = None) -> FixtureSet:
    directory = directory or Path(__file__).with_name("fixtures")
    def read(name):
        return json.loads((directory / (name + ".json")).read_text(encoding="utf-8"),
                          parse_constant=lambda v: (_ for _ in ()).throw(ValueError(v)))
    sources = tuple(SourceAuthority(r["id"], r["role"], ("discovery",),
                   Scope("A", r["user"], r["domain"], "current"), True, False) for r in read("sources"))
    roles = {r.source_id: r.role for r in sources}
    feedback = tuple(FeedbackRecord(r["id"], r["source"], roles[r["source"]], r.get("purpose", "discovery"),
                     r["family"], Scope("A", r.get("user"), r["domain"], "current"), "run-" + r["id"],
                     r["payload"], False, True, r.get("complete", True), ("receipt-" + r["id"],),
                     r.get("duplicate_of"), tuple(r.get("conflict_refs", []))) for r in read("feedback"))
    documents = tuple(Document(r["id"], r["tenant"], r["domain"], r["version"],
                      "2024-01-01T00:00:00Z", "2030-01-01T00:00:00Z", r["answer"], tuple(r["steps"]),
                      "document-owner") for r in read("documents"))
    tasks = tuple(TaskSpec(r["id"], r["family"], r.get("split", "holdout"), r["slice"],
                  AgentInput(r.get("tenant", "A"), r.get("user", "user-C"), r["domain"], r.get("version", "current"),
                             r["question"], r["operation"], tuple(r.get("receipts", ["ok"]))),
                  r["gold"], r.get("target", False), r.get("clock", CLOCK), tuple(r.get("revoked", []))) for r in read("tasks"))
    truth = tuple(SuccessCondition(r["ref"], r["doc"], tuple(r.get("steps", [])), r.get("style", "normal"),
                  r.get("refusal"), Scope(r["tenant"], r.get("user"), r["domain"], r.get("version", "current")),
                  "atlas-truth-v1") for r in read("truth"))
    index = {t.task_id: t for t in tasks}
    replays = tuple(ReplayCase(r["id"], index[r["task"]].agent_input, documents, tuple(r["tape"]),
                   ("tenant-A",), "deterministic-agent-v1", CLOCK, index[r["task"]].success_ref,
                   r.get("family", index[r["task"]].family_id), tuple(r["missing"])) for r in read("replays"))
    return validate_fixtures(FixtureSet(feedback, sources, documents, tasks, truth, replays))
