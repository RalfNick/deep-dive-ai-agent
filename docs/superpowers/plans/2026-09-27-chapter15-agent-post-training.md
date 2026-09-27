# Chapter 15 Agent Post-Training Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce a complete local `v1.0-rc1` candidate for Chapter 15 that teaches when and how Agent post-training applies through deterministic, no-GPU experiments without publishing the chapter.

**Architecture:** A standard-library Python lab models intervention choice, trajectory auditing, finite-action SFT/DPO mechanics, and reward-hacking countermeasures behind immutable JSON-friendly contracts. Five experiment groups generate versioned reproducible reports that the manuscript, exercises, diagrams, and reader preview cite as evidence; the public manifest and site allowlist remain frozen at Chapters 1–14.

**Tech Stack:** Python 3.11, standard library, pytest 9.0.2, jsonschema 4.26.0, Markdown 3.10.2 for local preview, editable SVG/Tldraw diagrams, MkDocs strict build.

**Spec:** `docs/superpowers/specs/2026-09-27-chapter15-agent-post-training-design.md`

## Global Constraints

- Core experiments require no GPU, API key, model weights, network access, or external service.
- Runtime uses the Python standard library; pytest/jsonschema are test-only and Markdown is preview-only.
- Fixed fixtures and fixed seeds must generate byte-identical stable reports without timestamps, UUIDs, temporary paths, or host paths.
- Teaching policy updates demonstrate mechanisms only; never label them as LLM training results or real model capability gains.
- Safety violations are hard vetoes and cannot be offset by outcome, efficiency, or reward totals.
- Product facts, supported models, parameters, and APIs must use primary sources with a `2026-09-27` verification date.
- Chapter 15 stays a local candidate: do not change `book/manifest.json`, `scripts/build_site.py`, `mkdocs.yml`, public README chapter counts, or deploy either site.
- Preserve Chapters 1–14 and every historical version/tag unchanged.
- Stage exact paths only; never use `git add .`, `git add -A`, or `git add --all`.

## Review Focus

- A successful outcome containing a protected-file write must be quarantined by `chapter15/tests/test_dataset.py::test_success_cannot_override_protected_write`.
- Near-duplicate task families crossing train/eval boundaries must be blocked by `chapter15/tests/test_dataset.py::test_cross_split_near_duplicates_are_quarantined`.
- Missing or unknown provenance must remain explicit and block training admission in `chapter15/tests/test_contracts.py::test_trajectory_requires_complete_provenance`.
- A preference pair whose alternatives come from different states must be rejected in `chapter15/tests/test_objectives.py::test_preference_pair_requires_same_state`.
- A high task reward must not compensate for a safety violation in `chapter15/tests/test_simulator.py::test_safety_veto_cannot_be_bought_with_reward`.

---

## File Responsibility Map

| File | Responsibility |
| --- | --- |
| `chapter15/contracts.py` | Immutable enums/dataclasses, validation, stable serialization |
| `chapter15/intervention.py` | Failure-to-intervention decision rules and evidence |
| `chapter15/dataset.py` | Fixture loading, normalization, redaction, deduplication, split/leakage audit, sample construction |
| `chapter15/policy.py` | Finite-action tabular policy, softmax, deterministic snapshots |
| `chapter15/objectives.py` | SFT cross-entropy/update and DPO loss/margin calculations |
| `chapter15/simulator.py` | Fixed-seed reward environment, strategy variants, release gate |
| `chapter15/audit.py` | Aggregate findings, data quality, evidence-limit reporting |
| `chapter15/experiments.py` | Five groups, atomic report writing, overwrite/replace behavior, CLI |
| `chapter15/exercise_solutions.py` | Machine-checkable solutions for 12–14 exercises |
| `chapter15/preview.py` | Local manuscript preview only |
| `chapter15/real-training-guide.md` | Explicitly unexecuted migration guidance for real SFT/DPO/GRPO workflows |
| `chapter15/fixtures/*.json` | Versioned deterministic failure, trajectory, preference, and environment inputs |
| `chapter15/schemas/post-training-report-v1.schema.json` | Stable report contract |
| `chapter15/reports/*` | Canonical generated evidence and artifact hashes |
| `infographic/chapter15/*` | Editable scene sources and deterministic diagram generator |
| `book/images/chapter15/*` | Seven reader-facing self-contained SVGs |
| `book/chapter15.md` | Authoritative Simplified Chinese manuscript |
| `book/sources/chapter15-sources.md` | Primary-source ledger and fact boundaries |
| `book/reviews/chapter15-review-codex-v1.0-rc1.md` | Reader and expert review with dispositions |
| `book/versions/chapter15-v1.0-rc1.md` | Candidate environment, commands, hashes, proved/unproved claims |

### Task 1: Contracts, Dependency Locks, and Fixture Skeleton

**Files:**
- Create: `chapter15/__init__.py`
- Create: `chapter15/contracts.py`
- Create: `chapter15/requirements.in`
- Create: `chapter15/requirements-dev.in`
- Create: `chapter15/requirements-dev.txt`
- Create: `chapter15/requirements-preview.txt`
- Create: `chapter15/fixtures/failure-cases.json`
- Create: `chapter15/tests/__init__.py`
- Create: `chapter15/tests/test_contracts.py`

**Interfaces:**
- Produces: `InterventionKind`, `DataSplit`, `FindingSeverity`, `ReleaseDecisionKind` string enums.
- Produces: frozen dataclasses `FailureObservation`, `TaskCase`, `TrajectoryStep`, `TrajectoryRecord`, `SupervisedExample`, `PreferencePair`, `RewardSpec`, `AuditFinding`, `PostTrainingReport`, each with `to_dict() -> dict[str, object]`.
- Contract constants: allowed splits are `train`, `validation`, `eval`; release decisions are `pass`, `fail`, `inconclusive`; every trajectory has non-empty `source_run_id`, `model_fingerprint`, `harness_fingerprint`, and `transform_history`.

- [ ] **Step 1: Write failing contract tests**

Add tests for stable serialization, invalid split/action/reward ranges, duplicate step numbers, absent provenance, a preference pair with different `state_id` values, and a `RewardSpec` that omits the safety-veto flag.

- [ ] **Step 2: Verify the tests fail before implementation**

Run: `python -B -m pytest chapter15/tests/test_contracts.py -q`

Expected: collection fails because `chapter15.contracts` or the named types do not exist.

- [ ] **Step 3: Implement the contracts and locks**

Use frozen dataclasses, tuple/frozen mapping conversion, explicit error codes, and JSON-safe `to_dict()` methods matching Chapters 13–14. Keep runtime empty in `requirements.in`; use `jsonschema==4.26.0` and `pytest==9.0.2` in the locked dev graph and `Markdown==3.10.2` only for preview.

Create five failure cases: `missing_knowledge`, `permission_bypass`, `ambiguous_instruction`, `model_capacity`, and `repeated_policy_bias`. Each fixture includes observed evidence and a counterfactual check.

- [ ] **Step 4: Run contract tests**

Run: `python -B -m pytest chapter15/tests/test_contracts.py -q`

Expected: PASS, including `test_trajectory_requires_complete_provenance`.

- [ ] **Step 5: Commit the contract foundation**

```bash
git add -- chapter15/__init__.py chapter15/contracts.py chapter15/requirements.in chapter15/requirements-dev.in chapter15/requirements-dev.txt chapter15/requirements-preview.txt chapter15/fixtures/failure-cases.json chapter15/tests/__init__.py chapter15/tests/test_contracts.py
git commit -m "feat(chapter15): define post-training evidence contracts"
```

### Task 2: Intervention Decision Boundary

**Files:**
- Create: `chapter15/intervention.py`
- Create: `chapter15/tests/test_intervention.py`
- Modify: `chapter15/fixtures/failure-cases.json`

**Interfaces:**
- Consumes: `FailureObservation`, `InterventionKind`, `AuditFinding` from Task 1.
- Produces: `InterventionDecision` in `contracts.py` with `recommended`, `reason_codes`, `evidence_refs`, `alternatives`, and `confidence`.
- Produces: `recommend_intervention(observation: FailureObservation) -> InterventionDecision`.
- Produces: `load_failure_cases(path: Path | None = None) -> tuple[FailureObservation, ...]`.

- [ ] **Step 1: Write failing decision tests**

Assert these fixed mappings: missing facts → `rag_context`; deterministic permission bypass → `harness`; ambiguous instruction → `prompt_skill`; verified capacity gap → `model_route`; repeated cross-task policy bias with reusable supervision → `post_training`. An observation without enough evidence must return `inconclusive`, never default to training.

- [ ] **Step 2: Run the focused tests and observe failure**

Run: `python -B -m pytest chapter15/tests/test_intervention.py -q`

Expected: FAIL because the loader and decision function are absent.

- [ ] **Step 3: Implement evidence-first rules**

Rules must require the fixture's counterfactual check to have failed before recommending post-training. Keep reason codes stable and avoid a numerical “AI confidence” claim; `confidence` is one of `low`, `medium`, `high` based on evidence completeness.

- [ ] **Step 4: Verify the intervention boundary**

Run: `python -B -m pytest chapter15/tests/test_intervention.py -q`

Expected: PASS; the ablation that routes every failure to training must be detected as wrong on four of five canonical cases.

- [ ] **Step 5: Commit**

```bash
git add -- chapter15/contracts.py chapter15/intervention.py chapter15/fixtures/failure-cases.json chapter15/tests/test_intervention.py
git commit -m "feat(chapter15): add evidence-first intervention routing"
```

### Task 3: Trajectory Dataset Audit and Leakage Protection

**Files:**
- Create: `chapter15/dataset.py`
- Create: `chapter15/audit.py`
- Create: `chapter15/fixtures/trajectories.json`
- Create: `chapter15/tests/test_dataset.py`

**Interfaces:**
- Consumes: trajectory and finding contracts from Task 1.
- Produces: `load_trajectories(path: Path | None = None) -> tuple[TrajectoryRecord, ...]`.
- Produces: `redact_record(record: TrajectoryRecord, *, salt: str) -> TrajectoryRecord`.
- Produces: `audit_dataset(records: Sequence[TrajectoryRecord]) -> DatasetAudit`.
- Produces: `build_supervised_examples(audit: DatasetAudit) -> tuple[SupervisedExample, ...]`.
- `DatasetAudit` exposes `raw_count`, `eligible_ids`, `quarantined_ids`, `findings`, `split_counts`, and `reason_counts`.

- [ ] **Step 1: Write failing dataset tests**

Pin a 24-record fixture with four six-record slices and raw split counts `train=12`, `validation=4`, `eval=8`. Tests must cover nested secret redaction, hidden answers, protected writes despite final success, missing tool results, unknown provenance, exact duplicates, and near-duplicate task families crossing train/eval.

- [ ] **Step 2: Verify the tests fail**

Run: `python -B -m pytest chapter15/tests/test_dataset.py -q`

Expected: FAIL because the fixture loader and audit pipeline are absent.

- [ ] **Step 3: Implement the deterministic audit pipeline**

Normalize first, redact before serialization, derive a semantic family digest from normalized task fields, then apply split/leakage checks. Quarantine records rather than silently deleting them. “Successful” records with safety findings are ineligible for both supervised and preference samples.

- [ ] **Step 4: Verify safety and leakage regressions**

Run: `python -B -m pytest chapter15/tests/test_dataset.py -q`

Expected: PASS, including `test_success_cannot_override_protected_write` and `test_cross_split_near_duplicates_are_quarantined`.

- [ ] **Step 5: Commit**

```bash
git add -- chapter15/dataset.py chapter15/audit.py chapter15/fixtures/trajectories.json chapter15/tests/test_dataset.py
git commit -m "feat(chapter15): audit trajectory data and split leakage"
```

### Task 4: Finite-Action SFT and DPO Mechanics

**Files:**
- Create: `chapter15/policy.py`
- Create: `chapter15/objectives.py`
- Create: `chapter15/fixtures/preference-pairs.json`
- Create: `chapter15/tests/test_objectives.py`

**Interfaces:**
- Consumes: `SupervisedExample` and `PreferencePair`.
- Produces: `TabularPolicy(states: Sequence[str], actions: Sequence[str], logits: Mapping[str, Mapping[str, float]])` with `probability(state: str, action: str) -> float` and `snapshot() -> dict[str, object]`.
- Produces: `cross_entropy(policy: TabularPolicy, examples: Sequence[SupervisedExample]) -> float`.
- Produces: `sft_step(policy: TabularPolicy, examples: Sequence[SupervisedExample], *, learning_rate: float) -> TabularPolicy`.
- Produces: `dpo_loss(pair: PreferencePair, *, beta: float) -> float` and `dpo_margin(pair: PreferencePair, *, beta: float) -> float`.
- Uses states `needs_facts`, `write_requested`, `tool_timeout`, `ready_to_finish` and actions `search`, `read`, `edit`, `retry`, `stop`, `modify_tests`.

- [ ] **Step 1: Write failing math and validation tests**

Assert softmax normalization, clean demonstrations increasing the demonstrated action probability, contaminated demonstrations increasing `modify_tests`, missing recovery examples leaving the timeout slice unchanged, and same-state preference validation.

Pin the hand example: candidate chosen/rejected log probabilities `-0.8/-1.2`, reference `-1.0/-1.1`, `beta=0.5`, margin `0.15`, loss approximately `0.620957`.

- [ ] **Step 2: Verify tests fail**

Run: `python -B -m pytest chapter15/tests/test_objectives.py -q`

Expected: FAIL because policy/objective functions do not exist.

- [ ] **Step 3: Implement the minimum numerical model**

Use `math.exp`, stable max-subtracted softmax, immutable returned policies, and `math.log1p`/stable sigmoid calculations. Do not add NumPy or a training framework.

- [ ] **Step 4: Verify hand calculations and bad-demo behavior**

Run: `python -B -m pytest chapter15/tests/test_objectives.py -q`

Expected: PASS with the pinned DPO loss and monotonic SFT probability assertions.

- [ ] **Step 5: Commit**

```bash
git add -- chapter15/policy.py chapter15/objectives.py chapter15/fixtures/preference-pairs.json chapter15/tests/test_objectives.py
git commit -m "feat(chapter15): model sft and dpo mechanics"
```

### Task 5: Reward-Hacking Simulator and Release Gate

**Files:**
- Create: `chapter15/simulator.py`
- Create: `chapter15/fixtures/policy-environment.json`
- Create: `chapter15/tests/test_simulator.py`

**Interfaces:**
- Consumes: `RewardSpec`, `TabularPolicy`, trajectory contracts.
- Produces: `run_policy_variant(variant: str, *, episodes: int = 200, seed: int = 1501) -> SimulationResult` for `outcome_only`, `scalar_penalty`, and `hard_gate`.
- Produces: `compare_policy_variants(results: Sequence[SimulationResult]) -> dict[str, object]`.
- Produces: `release_decision(*, baseline: PolicyMetrics, candidate: PolicyMetrics, slice_deltas: Mapping[str, float]) -> ReleaseDecision`.

- [ ] **Step 1: Write failing simulator tests**

Pin deterministic replay for seed `1501`; assert outcome-only learns the protected-test shortcut, a `-3` scalar safety penalty remains offset by a `+10` success reward, and the hard-gate variant records zero accepted safety violations. Missing evaluation coverage must yield `inconclusive`.

- [ ] **Step 2: Verify tests fail**

Run: `python -B -m pytest chapter15/tests/test_simulator.py -q`

Expected: FAIL because simulator functions are absent.

- [ ] **Step 3: Implement the finite environment and gate**

Keep environment transitions explicit and deterministic. The gate order is: environment validity → safety veto → protected-file integrity → slice regression → overall outcome → efficiency as a tiebreaker. Never sum safety into the scalar release score.

- [ ] **Step 4: Verify reward-hacking behavior**

Run: `python -B -m pytest chapter15/tests/test_simulator.py -q`

Expected: PASS, including `test_safety_veto_cannot_be_bought_with_reward`.

- [ ] **Step 5: Commit**

```bash
git add -- chapter15/simulator.py chapter15/fixtures/policy-environment.json chapter15/tests/test_simulator.py
git commit -m "feat(chapter15): simulate reward hacking and release gates"
```

### Task 6: Five Experiment Groups and Stable Reports

**Files:**
- Create: `chapter15/experiments.py`
- Create: `chapter15/schemas/post-training-report-v1.schema.json`
- Create: `chapter15/tests/test_experiments.py`
- Generate: `chapter15/reports/group-1.json` through `group-5.json`
- Generate: `chapter15/reports/post-training-report.json`
- Generate: `chapter15/reports/post-training-report.md`
- Generate: `chapter15/reports/manifest.json`

**Interfaces:**
- Consumes: Tasks 1–5 public functions only.
- Produces: `run_group(group: int, output: Path) -> dict[str, object]`.
- Produces: `build_post_training_report(output: Path) -> dict[str, object]`.
- CLI: `python -B -m chapter15.experiments --group {1,2,3,4,5,all} --output PATH [--replace]`.
- Stable report schema: `chapter15.post-training.v1`; evidence limits include `finite_policy_not_llm_training`, `fixed_fixture_not_production_distribution`, `no_provider_conformance_claim`, and `no_gpu_training_performed`.

- [ ] **Step 1: Write failing report tests and Schema mutations**

Test five named groups, stable bytes across two fresh outputs, no host/API-key leakage, refusal to overwrite non-empty output, recoverable `.previous` replacement, artifact hashes, JSON Schema validation, and rejection when evidence limits or safety findings are removed.

- [ ] **Step 2: Verify tests fail**

Run: `python -B -m pytest chapter15/tests/test_experiments.py -q`

Expected: FAIL because the CLI/report builder and Schema do not exist.

- [ ] **Step 3: Implement atomic report generation**

Follow Chapter 14's staging-directory and recoverable replacement semantics. Group mapping is fixed: intervention, dataset audit, SFT, DPO, reward/release. Report all unavailable real-model fields as `null` or explicit `not_measured`, never zero.

- [ ] **Step 4: Generate canonical reports and verify**

Run:

```powershell
python -B -m pytest chapter15/tests/test_experiments.py -q
python -B -m chapter15.experiments --group all --output chapter15/reports --replace
python -B -m pytest chapter15/tests -q
```

Expected: all tests pass; five group artifacts, two reports, and one manifest are present and stable.

- [ ] **Step 5: Commit**

```bash
git add -- chapter15/experiments.py chapter15/schemas/post-training-report-v1.schema.json chapter15/tests/test_experiments.py chapter15/reports/group-1.json chapter15/reports/group-2.json chapter15/reports/group-3.json chapter15/reports/group-4.json chapter15/reports/group-5.json chapter15/reports/post-training-report.json chapter15/reports/post-training-report.md chapter15/reports/manifest.json
git commit -m "feat(chapter15): add deterministic post-training experiments"
```

### Task 7: Seven Editable Technical Diagrams

**Files:**
- Create: `infographic/chapter15/__init__.py`
- Create: `infographic/chapter15/README.md`
- Create: `infographic/chapter15/generate_diagrams.py`
- Create: `infographic/chapter15/01-intervention-tree.tldr` through `07-training-release-loop.tldr`
- Create: `book/images/chapter15/01-intervention-tree.svg` through `07-training-release-loop.svg`
- Create: `chapter15/tests/test_diagrams.py`

**Interfaces:**
- Produces: `generate_all(output_root: Path, source_root: Path) -> tuple[Path, ...]`.
- Each scene has a title, reading-order labels, editable source, self-contained SVG, `viewBox`, accessible `<title>`, no external font/image references, and shared labels between source and render.

- [ ] **Step 1: Write failing diagram contract tests**

Assert exactly seven source/render pairs, required titles from the spec, valid arrow bindings/indexes, no clipped canvas bounds, self-contained SVG, and minimum readable font size.

- [ ] **Step 2: Verify tests fail**

Run: `python -B -m pytest chapter15/tests/test_diagrams.py -q`

Expected: FAIL because Chapter 15 diagram files do not exist.

- [ ] **Step 3: Implement and generate the diagrams**

Reuse the Chapter 14 deterministic SVG/Tldraw utilities and existing cream paper, hand-drawn navy outline, and blue/green/purple/orange section palette. Do not use generated raster text.

- [ ] **Step 4: Verify diagram artifacts**

Run:

```powershell
python -B -m infographic.chapter15.generate_diagrams
python -B -m pytest chapter15/tests/test_diagrams.py -q
```

Expected: PASS; all seven SVG files are loadable and editable sources are valid.

- [ ] **Step 5: Commit**

Stage only `infographic/chapter15/`, `book/images/chapter15/`, and `chapter15/tests/test_diagrams.py`, then commit:

```bash
git commit -m "feat(book): add chapter 15 post-training diagrams"
```

### Task 8: Primary-Source Ledger and Real-Training Migration Guide

**Files:**
- Create: `book/sources/chapter15-sources.md`
- Create: `chapter15/real-training-guide.md`
- Create: `chapter15/tests/test_sources.py`

**Interfaces:**
- Source entries contain `id`, title, primary URL, source type, verified date `2026-09-27`, used-for claim, and non-claim/expiry boundary.
- The migration guide maps local fields to chat/tool-call datasets and current official SFT/DPO/GRPO or reinforcement-fine-tuning concepts without executable claims.

- [ ] **Step 1: Write failing source-ledger tests**

Require entries for instruction tuning/RLHF, DPO, Constitutional AI or RLAIF, current OpenAI fine-tuning/graders/RFT docs, current Hugging Face Transformers/Datasets/TRL docs, one recent Agent/tool-use RL paper, reward hacking, and data contamination. Reject undated product entries and secondary-only support for product behavior.

- [ ] **Step 2: Verify tests fail**

Run: `python -B -m pytest chapter15/tests/test_sources.py -q`

Expected: FAIL because the ledger and guide are absent.

- [ ] **Step 3: Research only primary sources and write the ledger**

Browse official documentation and original papers. Record access/version dates and avoid volatile price/model matrices in the manuscript. Distinguish established methods from recent research that has not been reproduced by this repository.

- [ ] **Step 4: Write the migration guide and mark every unexecuted command**

Include data-shape mappings, license/privacy checks, hardware caveats, frozen-eval reuse, and explicit labels `示例，未在本项目执行`. Do not add TRL/Transformers dependencies to Chapter 15 runtime.

- [ ] **Step 5: Verify and commit**

Run: `python -B -m pytest chapter15/tests/test_sources.py -q`

Then:

```bash
git add -- book/sources/chapter15-sources.md chapter15/real-training-guide.md chapter15/tests/test_sources.py
git commit -m "docs(chapter15): ground post-training claims in primary sources"
```

### Task 9: Manuscript Part I — Failure Diagnosis and Data

**Files:**
- Create: `book/chapter15.md`
- Create: `chapter15/tests/test_manuscript.py`

**Interfaces:**
- Consumes: group 1–2 reports, diagrams 1–2, and source IDs from Task 8.
- Produces: the opening, reading note, short answer, intervention boundary, trace-to-dataset pipeline, audit failures, and Experiment 15-1/15-2 sections.

- [ ] **Step 1: Write failing manuscript structure tests**

Require the exact chapter title, reading note, short answer, intervention comparison table, the five non-training alternatives, Experiment 15-1/15-2 commands, diagrams 1–2, source-ledger links, and explicit statements that successful unsafe trajectories are rejected and post-training is not the default fix.

- [ ] **Step 2: Verify tests fail**

Run: `python -B -m pytest chapter15/tests/test_manuscript.py -q`

Expected: FAIL because `book/chapter15.md` does not exist.

- [ ] **Step 3: Write Part I in reader-first order**

Start from the three observed failures, let the reader diagnose each before naming methods, then walk one raw Trace through normalization, redaction, deduplication, split isolation, and sample construction. Use report values exactly; do not dump full Schemas into the prose.

- [ ] **Step 4: Verify Part I contracts**

Run: `python -B -m pytest chapter15/tests/test_manuscript.py -q`

Expected: the Part I tests pass while Part II completeness tests remain skipped with an explicit marker owned by Task 10.

- [ ] **Step 5: Commit**

```bash
git add -- book/chapter15.md chapter15/tests/test_manuscript.py
git commit -m "docs(book): write chapter 15 diagnosis and data sections"
```

### Task 10: Manuscript Part II — SFT, DPO, RL, Failure Modes, and Exercises

**Files:**
- Modify: `book/chapter15.md`
- Modify: `chapter15/tests/test_manuscript.py`

**Interfaces:**
- Consumes: group 3–5 reports, diagrams 3–7, DPO hand calculation, release gate, and source ledger.
- Produces: complete 2.2–2.8 万 Chinese-character manuscript with 20–35 headings, 4–6 tables/checklists, five experiments, at least five failure samples, 12–14 exercises, evidence boundary, Chapter 16 transition, and further reading.

- [ ] **Step 1: Activate failing Part II completeness tests**

Require SFT/DPO/RL boundaries, the `0.620957` DPO hand result, Experiment 15-3/15-4/15-5 commands, reward-hacking hard-gate comparison, all seven diagrams, at least five failure reason codes, 12–14 numbered exercises, “proved/not proved” section, and the Chapter 16 transition.

- [ ] **Step 2: Run the active tests and observe failure**

Run: `python -B -m pytest chapter15/tests/test_manuscript.py -q`

Expected: FAIL on missing Part II sections.

- [ ] **Step 3: Complete the manuscript**

Teach one numerical example before general formulas; keep PPO/GRPO as placement context, not optimizer tutorials. Explain every diagram's reading order. Use one consolidated experiment-limit section instead of repeating disclaimers after every paragraph.

- [ ] **Step 4: Verify manuscript and local links**

Run:

```powershell
python -B -m pytest chapter15/tests/test_manuscript.py -q
python -B -m pytest chapter15/tests -q
```

Expected: PASS; no unresolved local image, source, report, or experiment link.

- [ ] **Step 5: Commit**

```bash
git add -- book/chapter15.md chapter15/tests/test_manuscript.py
git commit -m "docs(book): complete chapter 15 post-training manuscript"
```

### Task 11: Reader README, Exercises, Answers, and Local Preview

**Files:**
- Create: `chapter15/README.md`
- Create: `chapter15/reference-answers.md`
- Create: `chapter15/exercise_solutions.py`
- Create: `chapter15/preview.py`
- Create: `chapter15/tests/test_reader_tools.py`
- Generate: `chapter15/reports/exercise-results.json`

**Interfaces:**
- Produces: `solve(number: int) -> dict[str, object]` for every manuscript exercise and CLI `--all [--output PATH]` that refuses overwrite.
- Produces: `build_preview(root: Path, *, output: Path | None = None) -> Path`; default output is ignored/local and never committed.
- README exposes setup, five commands, expected artifacts, failure interpretation, evidence limits, and links to manuscript, answers, guide, and source ledger.

- [ ] **Step 1: Write failing reader-tool tests**

Require one machine-checkable solution per exercise, stable output, overwrite refusal, a preview with seven images and horizontally scrollable tables, no remote runtime assets, and all README local links resolving.

- [ ] **Step 2: Verify tests fail**

Run: `python -B -m pytest chapter15/tests/test_reader_tools.py -q`

Expected: FAIL because reader tools and files are absent.

- [ ] **Step 3: Implement solutions, answers, README, and preview**

Calculation answers must contain reproducible inputs and outputs. Design answers use criteria rather than pretending there is one exact architecture. The preview builder reads only Chapter 15 manuscript/assets and refuses to write outside the repository.

- [ ] **Step 4: Generate and verify reader artifacts**

Run:

```powershell
python -B -m chapter15.exercise_solutions --all --output chapter15/reports/exercise-results.json
python -B -m pytest chapter15/tests/test_reader_tools.py -q
python -B -m chapter15.preview
```

Expected: PASS; preview opens locally when requested, but no HTML output is staged.

- [ ] **Step 5: Commit**

```bash
git add -- chapter15/README.md chapter15/reference-answers.md chapter15/exercise_solutions.py chapter15/preview.py chapter15/tests/test_reader_tools.py chapter15/reports/exercise-results.json
git commit -m "feat(chapter15): add exercises and local reader preview"
```

### Task 12: Candidate Integration, Dual Review, and v1.0-rc1 Record

**Files:**
- Modify: `.github/workflows/ci.yml`
- Modify: `tests/test_workflow_contract.py`
- Modify: `tests/test_build_site.py`
- Modify: `docs/EXPERIMENT_STATUS.md`
- Modify: `book/versions/CHAPTER_VERSIONS.md`
- Modify: `AGENTS.md`
- Create: `book/reviews/chapter15-review-codex-v1.0-rc1.md`
- Create: `book/versions/chapter15-v1.0-rc1.md`

**Interfaces:**
- CI creates `.venv-chapter15`, installs locked dev and preview requirements, and runs `pytest chapter15/tests -q` without adding Chapter 15 to the site build.
- Publication guard test creates local Chapter 15 files and asserts they are absent from `_web` while Chapters 1–14 remain present.
- Review report separates reader findings, expert findings, severity, evidence, disposition, and remaining limitations.
- Version record stores Python/dependency contract, commands, report manifest hashes, tested commit, proved claims, and unproved claims.

- [ ] **Step 1: Write failing integration/negative-publication tests**

Add workflow assertions for Chapter 15 locked tests and requirements. Extend `test_build_site.py` with a local `book/chapter15.md`, lab README, answers, reports, and image, then assert none are copied into `_web` and `book/manifest.json` still reports `0.14.0` with Chapter 15 planned.

- [ ] **Step 2: Run tests and observe the missing CI integration**

Run: `python -B -m pytest tests/test_workflow_contract.py tests/test_build_site.py tests/test_book_manifest.py -q`

Expected: FAIL only on missing Chapter 15 CI commands; publication-negative assertions already pass against the unchanged allowlist.

- [ ] **Step 3: Add candidate-only CI and documentation state**

Add a separate Chapter 15 locked environment, not the Chapter 13–14 environment. Update experiment status/version ledger/AGENTS to say “local v1.0-rc1 candidate, unpublished”; do not modify manifest/nav/allowlist/root publication counts.

- [ ] **Step 4: Perform reader and expert reviews, then fix all high-priority findings**

Review the manuscript against `book/WRITING_GUIDE.md`, the design spec, canonical reports, and primary sources. Record each finding before its disposition. Re-run focused tests after every code or number correction.

- [ ] **Step 5: Create and verify the rc1 record**

Record exact report hashes from `chapter15/reports/manifest.json`, the final validation commands, and explicit limitations: no real model, no GPU training, no vendor conformance, fixed fixture only, not published.

- [ ] **Step 6: Run full candidate verification**

Run:

```powershell
python -B -m pytest chapter15/tests -q
python -B -m chapter15.experiments --group all --output chapter15/.runs/repro-a
python -B -m chapter15.experiments --group all --output chapter15/.runs/repro-b
python -B -m chapter15.exercise_solutions --all --output chapter15/.runs/exercises.json
python -B -m pytest tests -q
npm test --prefix book
python -B scripts/check_repository.py --root . --git-history
python -B scripts/build_site.py --root . --output _web
python -B -m mkdocs build --strict
git diff --check
```

Expected: all tests/builds pass; repro-a and repro-b stable manifests match; `_web` contains Chapters 1–14 only; no API key, host path, generated preview, `.runs`, `.venv`, cache, or PDF is staged.

- [ ] **Step 7: Commit the local candidate**

```bash
git add -- .github/workflows/ci.yml tests/test_workflow_contract.py tests/test_build_site.py docs/EXPERIMENT_STATUS.md book/versions/CHAPTER_VERSIONS.md AGENTS.md book/reviews/chapter15-review-codex-v1.0-rc1.md book/versions/chapter15-v1.0-rc1.md
git commit -m "docs(book): freeze chapter 15 rc1 candidate"
```

Do not push, merge, tag, update `book/manifest.json`, publish GitHub Pages, or deploy `wlxralf.com` in this task.

## Final Evidence Checklist

- [ ] `chapter15/reports/manifest.json` hashes match regenerated artifacts.
- [ ] Two fresh experiment runs are byte-identical after excluding output-directory names.
- [ ] All 24 fixture trajectories retain provenance and explicit disposition.
- [ ] DPO hand calculation in code, report, manuscript, and answers is the same.
- [ ] Reward-hacking report shows why scalar safety penalties are insufficient.
- [ ] Every figure is cited and explained in manuscript order.
- [ ] Every current product statement has a primary source and verification date.
- [ ] Reader and expert reviews have no unresolved P0/P1 finding.
- [ ] Public manifest remains `0.14.0`; Chapter 15 remains `planned` and excluded from site output.
- [ ] Worktree is clean and all user-facing artifacts are under this repository's root.
