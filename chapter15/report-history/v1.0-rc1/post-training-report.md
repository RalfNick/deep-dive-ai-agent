# Chapter 15 deterministic post-training report

> 有限动作、固定夹具、无 GPU 教学实验；不代表真实大模型训练效果。

## Data audit

- Raw trajectories: `24`
- Eligible trajectories: `12`
- Quarantined trajectories: `12`
- Train-only SFT examples: `5`

## Reward variants

| Variant | Outcome rate | Safety violations | Protected writes | Mean steps |
| --- | ---: | ---: | ---: | ---: |
| outcome_only | 1.000000 | 200 | 200 | 1.000000 |
| scalar_penalty | 1.000000 | 200 | 200 | 1.000000 |
| hard_gate | 1.000000 | 0 | 0 | 4.000000 |

## Release

- Final decision: `pass`
- Unsafe candidate: `fail`
- Stable schema: `chapter15.post-training.v1`

## Evidence limits

- `finite_policy_not_llm_training`
- `fixed_fixture_not_production_distribution`
- `no_provider_conformance_claim`
- `no_gpu_training_performed`
