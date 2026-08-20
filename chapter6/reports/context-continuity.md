# Chapter 6 deterministic context-continuity report

Scope: deterministic semantic-continuity contract; not model or product ranking

All rows use `sample_count=1`. Byte columns are canonical UTF-8 bytes, not provider tokens.

| Experiment | Variant | Sample count | Bytes before | Bytes after | Goal | Acceptance | Constraint | Negative constraint | Open issue | Rejected hypothesis | Locator integrity | Resume | Duplicate work | False completion | Packet | Trace | Decision |
| --- | --- | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- | --- | --- | --- |
| checkpoint_vs_rehydration | checkpoint-only-v1 | 1 | 12108 | 583 | true | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | — | — | — | false | — | true | unsafe_signature_change |
| checkpoint_vs_rehydration | rehydrated-context-v1 | 1 | 12108 | 3447 | true | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | true | 0 | false | true | true | apply_legacy_compatible_patch |
| context_growth | append-all-cursor-08 | 1 | 3950 | 3950 | true | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | — | — | — | false | — | true | — |
| context_growth | append-all-cursor-24 | 1 | 12108 | 12108 | true | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | — | — | — | false | — | true | apply_legacy_compatible_patch |
| failure_matrix | corrupt-artifact-source-digest | 1 | 12108 | 7217 | false | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | — | — | — | false | — | true | rejected_artifact_source_digest_mismatch |
| failure_matrix | early-constraint-loss | 1 | 12108 | 4337 | true | 0.000 | 0.500 | 0.000 | 0.000 | 1.000 | — | — | — | false | — | true | unsafe_signature_change |
| failure_matrix | omitted-open-failure | 1 | 12108 | 3579 | true | 1.000 | 1.000 | 1.000 | 0.000 | 1.000 | — | — | — | true | — | true | injected_summary_claims_complete |
| failure_matrix | unsupported-artifact-schema | 1 | 12108 | 7272 | false | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | — | — | — | false | — | true | rejected_artifact_schema |
| failure_matrix | workspace-digest-mismatch | 1 | 12108 | 3579 | false | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | — | — | — | false | — | true | rejected_stale_workspace_digest |
| generational_drift | structured-regenerated-v1 | 1 | 12108 | 3579 | true | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | — | — | false | — | true | apply_legacy_compatible_patch |
| generational_drift | summary-generation-1 | 1 | 12108 | 843 | true | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | — | — | — | false | — | true | unsafe_signature_change |
| generational_drift | summary-generation-2 | 1 | 843 | 16 | true | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | — | — | — | false | — | true | unsafe_signature_change |
| sliding_window | sliding-window-8-events | 1 | 12108 | 4337 | true | 0.000 | 0.500 | 0.000 | 0.000 | 1.000 | — | — | — | false | — | true | unsafe_signature_change |
| summary_vs_structured | structured-compaction-v1 | 1 | 12108 | 3579 | true | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | — | — | false | — | true | apply_legacy_compatible_patch |
| summary_vs_structured | summary-only-v1 | 1 | 12108 | 843 | true | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | — | — | — | false | — | true | unsafe_signature_change |

Run status: `passed`
