# Chapter 14 Benchmark, Tracing, and Production Diagnosis Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver a local `v1.0-rc1` Chapter 14 candidate that teaches benchmark interpretation, structured tracing, sampling, privacy, and production diagnosis through a deterministic 72-trace incident lab.

**Architecture:** A standard-library Python package generates three releases of synthetic Agent traces, validates a versioned trace contract, computes benchmark/production metrics, applies privacy-safe sampling, and runs deterministic ablations into a stable incident report. The manuscript, seven vector diagrams, exercises, preview, review, and version record consume the same canonical evidence.

**Tech Stack:** Python 3.11; standard library runtime; pytest 9.0.2; jsonschema 4.26.0; Markdown 3.10.2; SVG plus editable tldraw JSON; Playwright 1.62.1 for local visual QA.

**Spec:** `docs/superpowers/specs/2026-09-26-chapter14-benchmark-tracing-design.md`

## Global Constraints

- Work on `codex/chapter14-benchmark-tracing`, based on Chapter 13 rc2 commit `be655ca04f6449808bdbab64e5b3ee00c10a4c08`.
- Preserve Chapters 1–13. Only `CHAPTER_VERSIONS.md` and its migration-manifest integrity row may change outside new Chapter 14 files.
- Runtime experiments are offline, standard-library-only, and never read API keys.
- Generate exactly 72 scored traces: 24 each for `stable`, `incident`, `fixed`; each release has six `simple`, `retrieval`, `write`, and `recovery` traces.
- Raw credentials, user IDs, hidden answers, complete files, and hidden chain of thought never enter stable artifacts.
- Missing usage stays `null`; cost uses a versioned teaching `cost_units` rate card, never current provider prices.
- Tail samples are diagnostic, not unbiased population denominators.
- OpenTelemetry GenAI Agent conventions are recorded as Development on 2026-09-26; no conformance claim.
- Deliver 2.3–2.8 万 Chinese characters, 25–35 H2/H3 headings, five experiments, at least four failure samples, 4–6 comparison tables, seven figures, fourteen exercises, sources, review, preview, and rc1 record.
- Local candidate only: no push, tag, public navigation/allowlist change, deployment, PDF, or EPUB.

## Review Focus

1. Valid parent tree plus cyclic dependencies must fail before metrics (`test_trace_validation.py`).
2. Partial usage must preserve known totals and lower Coverage (`test_metrics.py`).
3. Tail-sampled error counts must not become population error rates (`test_sampling_privacy.py`).
4. Low telemetry completeness or competing explanations must yield `inconclusive` (`test_diagnosis.py`).
5. Same score with missing/different benchmark contracts must never be `comparable` (`test_benchmark.py`).

## File Map

- `chapter14/contracts.py`: immutable contracts and enums.
- `chapter14/benchmark.py`: Benchmark Card comparison.
- `chapter14/trace_builder.py`, `trace_validation.py`: deterministic fixture and trace invariants.
- `chapter14/metrics.py`: percentiles, critical path, usage/cost, release summaries.
- `chapter14/privacy.py`, `sampling.py`: pre-export redaction and sampling.
- `chapter14/diagnosis.py`: slices, ablations, Incident Report, regression tasks.
- `chapter14/experiments.py`: five groups, canonical report, manifest, CLI.
- `chapter14/exercise_solutions.py`, `preview.py`: reader tools.
- `chapter14/fixtures/`: Benchmark Cards, 24 scenarios, rate card.
- `chapter14/schemas/production-diagnostics-v1.schema.json`: stable Draft 2020-12 report contract.
- `chapter14/reports/`: JSON/Markdown report, five groups, exercises, manifest.
- `book/chapter14.md`, `book/sources/chapter14-sources.md`: manuscript and sources.
- `infographic/chapter14/`, `book/images/chapter14/`: editable sources and seven SVG figures.
- `book/reviews/chapter14-review-codex-v1.0-rc1.md`, `book/versions/chapter14-v1.0-rc1.md`: freeze records.

---

### Task 1: Contracts, Fixtures, and Dependency Locks

**Files:**
- Create: `chapter14/__init__.py`, `contracts.py`
- Create: `chapter14/fixtures/scenarios.json`, `rate-card.json`
- Create: `chapter14/requirements.in`, `requirements-dev.in`, `requirements-dev.txt`, `requirements-preview.txt`
- Test: `chapter14/tests/test_contracts.py`

**Interfaces:**
- Produces immutable `BenchmarkCard`, `SpanRecord`, `TraceRecord`, `SamplingDecision`, `IncidentReport`, `ValidationIssue`, each with `to_dict()`.
- Stable enums cover releases, slices, span/status kinds, sampling stages/decisions, and incident conclusions.

- [ ] **RED:** Write `test_valid_contracts_serialize_explicit_nulls` and parameterized invalid-contract tests. Pin missing IDs, invalid enums, negative time/usage, `end_ms < start_ms`, and duplicate Span IDs. Run `.venv\Scripts\python.exe -B -m pytest chapter14/tests/test_contracts.py -q`; expect import failure.
- [ ] **GREEN:** Implement only constructor validation and serialization. Cross-record parent/DAG checks stay in Task 3. Re-run the focused test to green.
- [ ] Add 24 scenario definitions and rate-card version `chapter14.cost-units.v1`; test unique scenario IDs, four balanced slices, and absence of raw sensitive fields.
- [ ] Lock Python `>=3.11,<3.12`, pytest `9.0.2`, jsonschema `4.26.0`, and preview Markdown `3.10.2` using the Chapter 13 `uv pip compile --python-version 3.11 --generate-hashes` pattern.
- [ ] Commit: `feat(chapter14): define observability contracts`.

### Task 2: Benchmark Card Comparability

**Files:**
- Create: `chapter14/fixtures/benchmark-cards.json`
- Create: `chapter14/benchmark.py`
- Test: `chapter14/tests/test_benchmark.py`

**Interfaces:**
- `load_benchmark_cards(path: Path | None = None) -> tuple[BenchmarkCard, ...]`
- `compare_benchmark_cards(left: BenchmarkCard, right: BenchmarkCard) -> dict[str, object]`
- Output keys: `verdict`, `different_fields`, `missing_fields`, `reason_codes`, `limits`.

- [ ] **RED:** Add `test_exact_control_pair_is_comparable`, `test_same_score_with_harness_or_budget_changes_is_partial`, and `test_missing_or_different_task_metric_contract_is_not_comparable`. Assert equal scores never override contract differences. Run the file; expect missing module/functions.
- [ ] **GREEN:** Implement explicit critical fields (`benchmark_id`, version, subset, metric) and controlled configuration fields (Harness, environment, budgets, retry, attempts); do not scrape leaderboards.
- [ ] Add a same-score misleading pair and a true control pair to the fixture; validate all required provenance fields on load.
- [ ] Run Tasks 1–2 tests together and confirm deterministic ordering of differences/reason codes.
- [ ] Commit: `feat(chapter14): audit benchmark comparability`.

### Task 3: Trace Generation, Validation, and Metrics

**Files:**
- Create: `chapter14/trace_builder.py`, `trace_validation.py`, `metrics.py`
- Test: `chapter14/tests/test_trace_builder.py`, `test_trace_validation.py`, `test_metrics.py`

**Interfaces:**
- `build_trace_fixture() -> tuple[TraceRecord, ...]`
- `build_shuffled_log_fixture(trace: TraceRecord) -> tuple[dict[str, object], ...]`
- `validate_trace(trace: TraceRecord) -> tuple[ValidationIssue, ...]`; `require_valid_trace(trace) -> None`
- `nearest_rank(values: Sequence[float], percentile: float) -> float`
- `critical_path(trace: TraceRecord) -> dict[str, object]`
- `summarize_release(traces, rate_card) -> dict[str, object]`; `compare_releases(summaries) -> dict[str, object]`

- [ ] **RED fixture:** Assert 72 traces, 24 per release, six per release/slice, stable IDs, byte-identical double generation, and only declared release modifiers. Run `test_trace_builder.py`; expect missing functions.
- [ ] **GREEN fixture:** Generate root/container plus model, retrieval, tool, retry/approval, and verifier work spans. Include parallel work, slow requests, errors, retry, missing usage, and telemetry-incomplete examples; root/container spans never enter the dependency DAG.
- [ ] **RED validation:** Test unknown parents, parent/dependency cycles, dependency on container spans, child outside parent time, duplicate IDs, negative usage, forbidden attributes, and one valid parallel trace. Implement independent tree/DAG validation with stable issue codes.
- [ ] **RED/GREEN metrics:** Pin hand-calculable p50/p95, Span sum greater than endpoint latency, a known DAG longest path, retry amplification, and partial-usage Coverage. Implement nearest-rank exactly and aggregate only explicit usage/cost units.
- [ ] Run all Task 1–3 tests; commit `feat(chapter14): generate and measure incident traces`.

### Task 4: Privacy-Safe Sampling

**Files:**
- Create: `chapter14/privacy.py`, `sampling.py`
- Test: `chapter14/tests/test_sampling_privacy.py`

**Interfaces:**
- `redact_payload(value: object, *, salt: str) -> object`
- `validate_export_safe(value: object) -> tuple[ValidationIssue, ...]`
- `head_sample(trace, probability, policy_version) -> SamplingDecision`
- `tail_sample(trace, thresholds, policy_version) -> SamplingDecision`
- `combined_sample(...) -> SamplingDecision`; `sampling_report(...) -> dict[str, object]`

- [ ] **RED privacy:** Test nested Authorization/Cookie/API-key-like values, email/user IDs, tool arguments, stable salted hashes, and rejection of forbidden export fields.
- [ ] **RED sampling:** Test deterministic Trace-ID head sampling; tail retention of errors, slow traces, approvals/security events, incomplete telemetry, and new releases; demonstrate a rare error absent from a 10% head sample.
- [ ] **GREEN:** Redact before any buffer/sample/export representation. Preserve low-cardinality aggregate request/error counters outside the sampled trace store.
- [ ] Assert `sampling_report` separates population Metrics, diagnostic retained counts, Trace Coverage, and telemetry completeness; it must not expose a tail-sample “error rate”.
- [ ] Run focused and cumulative tests; commit `feat(chapter14): add privacy-safe trace sampling`.

### Task 5: Diagnosis, Experiment Groups, and Stable Report

**Files:**
- Create: `chapter14/diagnosis.py`, `experiments.py`
- Create: `chapter14/schemas/production-diagnostics-v1.schema.json`
- Generate: `chapter14/reports/diagnostic-report.json`, `.md`, `group-1.json` … `group-5.json`, `manifest.json`
- Test: `chapter14/tests/test_diagnosis.py`, `test_experiments.py`

**Interfaces:**
- `run_ablations(traces) -> tuple[dict[str, object], ...]`
- `diagnose_incident(...) -> IncidentReport`; `build_regression_tasks(report) -> tuple[dict[str, object], ...]`
- `build_diagnostics(directory: Path) -> dict[str, object]`; `run_group(group: int, directory: Path) -> dict[str, object]`
- CLI: `python -B -m chapter14.experiments --group {1|2|3|4|5|all} --output PATH [--replace]`.

- [ ] **RED diagnosis:** Assert incident outcome stays near stable while latency/cost/retry regress; only retry-policy ablation removes all canonical symptoms; fixed returns toward stable; report contains supporting and counterevidence IDs. Pin `inconclusive` for low completeness, tied explanations, or slice-confounded evidence.
- [ ] **GREEN diagnosis:** Represent model, Prompt, context, tool latency, and retry hypotheses explicitly. Generate regression tasks only from a conclusive result.
- [ ] **RED report:** Pin group evidence: Benchmark comparison; log-vs-tree; latency/critical path/usage; sampling/privacy; ablation/fix/regression tasks. Pin `chapter14.diagnostics.v1`, exactly 72 scored traces, no wall-clock/absolute path/raw secret, overwrite refusal, recoverable replacement, and stable bytes.
- [ ] Implement report/CLI and Draft 2020-12 Schema. Validate the real report; mutations for invalid release/conclusion, nested unknown field, negative duration, or missing completeness must fail.
- [ ] Generate two temporary `--group all` outputs and compare every stable artifact byte-for-byte; then generate canonical reports and commit `feat(chapter14): publish deterministic diagnostics report`.

### Task 6: Seven Editable Vector Diagrams

**Files:**
- Create: `infographic/chapter14/__init__.py`, `generate_diagrams.py`, `README.md`
- Generate: seven `infographic/chapter14/*.tldr`
- Generate: seven `book/images/chapter14/*.svg`
- Test: `chapter14/tests/test_diagrams.py`

**Interfaces:**
- `generate_all(source_dir: Path, image_dir: Path) -> tuple[tuple[Path, Path], ...]`
- One scene definition exports both tldraw JSON and SVG; labels, nodes, arrows, colors, and layout are not duplicated.

- [ ] **RED:** Assert seven approved name pairs; unique tldraw indexes and valid arrow bindings; XML-valid SVG with `viewBox`, approved title, and no external resources/raster data URLs.
- [ ] **GREEN:** Implement figures for evidence gap, Benchmark comparability, signal map, Session/Trace/Span, critical path, sampling/privacy, and diagnosis loop using the existing light-paper hand-drawn palette.
- [ ] Generate all outputs and run `test_diagrams.py` plus repository SVG/security checks.
- [ ] Open all SVGs at original size; correct clipped text, crossing arrows, ambiguous direction, and inconsistent spacing.
- [ ] Commit `feat(book): add chapter 14 observability diagrams`.

### Task 7: Manuscript, Sources, README, and Platform Mapping

**Files:**
- Create: `book/chapter14.md`, `book/sources/chapter14-sources.md`
- Create: `chapter14/README.md`, `chapter14/integrations.md`

**Interfaces:**
- Every numerical claim maps to a canonical report field; every changing product claim maps to a dated source-ledger anchor.

- [ ] Verify primary sources as of `2026-09-26`: SWE-bench official site/paper/Verified material; OpenTelemetry Traces/Sampling/GenAI Agent conventions; Langfuse data model/best practices/masking/evaluation loop; OpenAI Agents SDK tracing/sensitive-data/processors; primary tracing and benchmark research. Record exact claim and volatility boundary.
- [ ] Write Acts I–II: incident, short answer, boundary table, Benchmark system/Card, Experiment 14-1, SWE-bench family reading, contamination/reproducibility, public-vs-internal evaluation.
- [ ] Write Acts III–V: five signal types, trace hierarchy/dependencies/correlation, Experiments 14-2/14-3, percentiles/critical path/usage/high cardinality, sampling/privacy/no-hidden-CoT, Experiment 14-4.
- [ ] Write Acts VI–VII and close: slicing/hypotheses/counterevidence/ablation, Experiment 14-5, replay/regression, platform mapping, failure modes, Incident Report, evidence limits, summary, 14 exercises, Chapter 15 transition.
- [ ] Reconcile commands, numbers, paths, figure order, source anchors, 2.3–2.8 万 characters, and 25–35 H2/H3 headings; commit `docs(book): write chapter 14 production diagnosis`.

### Task 8: Answers, Preview, and Reader-Facing Checks

**Files:**
- Create: `chapter14/exercise_solutions.py`, `reference-answers.md`, `preview.py`
- Create: `chapter14/tests/test_reader_tools.py`
- Create: `book/check_chapter14_preview.mjs`
- Generate: `chapter14/reports/exercise-results.json`
- Local only: `chapter14/preview-pages/**`

**Interfaces:**
- `solve(number: int) -> dict[str, object]`; CLI `python -B -m chapter14.exercise_solutions --all [--output PATH]`.
- `build_preview(root: Path, *, output: Path | None = None) -> Path`.

- [ ] **RED/GREEN exercises:** Assert fourteen numbered solutions; exact nearest-rank, critical-path, retry-amplification, and sampling-Coverage calculations; rejection of an incident report lacking completeness/counterevidence. Implement runnable evidence or explicit rubrics and stable exercise output.
- [ ] **RED/GREEN reader checks:** Pin seven figures, five experiment blocks, fourteen exercises, valid local/source anchors, scrollable tables, Chapter 14-only preview paths, and canonical report numbers cited in prose.
- [ ] Adapt the Chapter 13 preview for Chapter 14. Add 1440×1000 and 390×844 Playwright checks for 7/7 image loading, fragment anchors, table containment, mobile figure scrolling, and no page-level overflow.
- [ ] Run `python -B -m chapter14.preview` and `node book/check_chapter14_preview.mjs`; inspect desktop/mobile full-page captures and all mobile figures. Screenshots remain ignored/local.
- [ ] Commit `feat(chapter14): add exercises and local preview`.

### Task 9: Review, Version, and Freeze rc1

**Files:**
- Create: `book/reviews/chapter14-review-codex-v1.0-rc1.md`
- Create: `book/versions/chapter14-v1.0-rc1.md`
- Modify: `book/versions/CHAPTER_VERSIONS.md`, `docs/MIGRATION_MANIFEST.md`

**Interfaces:**
- Produces dual-perspective findings, verification evidence, hashes, proven/unproven conclusions, and explicit no-publish status.

- [ ] Review as a first-time reader: opening tension, term order, hand-checkable examples, figure reading order, platform balance, exercise answerability. Review as an observability expert: Benchmark comparability, tree/DAG distinction, percentiles, critical path, usage Coverage, tail-sample bias, privacy ordering, telemetry-loss semantics, causality, and standards status. Fix all P0/P1.
- [ ] Run Chapter 14 tests, two complete report generations, exercises, preview, and Playwright visual QA. Require identical stable artifacts and 7/7 valid figures at both widths.
- [ ] Run full repository unit tests, `scripts.check_repository`, `scripts.build_site`, `mkdocs build --strict`, and `git diff --check`. Confirm no `site/book/chapter14/index.html`, `_web/book/chapter14.md`, or changes to public manifests/navigation.
- [ ] Write review/version files with environment, counts, commands, hashes, limitations, branch/base, and local-only status. Append rc1 to `CHAPTER_VERSIONS.md`; update only that row's size/hash and date in `MIGRATION_MANIFEST.md`.
- [ ] Remove verified local `.runs/`, caches, and preview screenshots; scan changed files for secrets and author paths; confirm Chapter 13 rc2 byte identity. Commit `docs(book): freeze chapter 14 rc1 candidate`, then require a clean worktree without push/tag/deploy.
