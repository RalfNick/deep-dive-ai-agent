# Chapter 15 deterministic post-training report

> 有限动作、固定夹具、无 GPU 教学实验；不代表真实大模型训练效果。

## Data audit

- Raw trajectories: `24`
- Eligible trajectories: `12`
- Quarantined trajectories: `12`
- Train-only SFT examples: `5`

## Static reward replay (not training)

| Variant | Outcome rate | Safety violations | Protected writes | Mean steps |
| --- | ---: | ---: | ---: | ---: |
| outcome_only | 1.000000 | 200 | 200 | 1.000000 |
| scalar_penalty | 1.000000 | 200 | 200 | 1.000000 |
| hard_gate | 1.000000 | 0 | 0 | 4.000000 |

## Reward-driven policy updates

One-state bandit, categorical sampling, REINFORCE without baseline; no tools executed.

| Variant | Updates | P(edit) after | P(modify_tests) after | Exploration safety events | Steps |
| --- | ---: | ---: | ---: | ---: | ---: |
| outcome_only | 200 | 0.005936 | 0.990626 | 191 | 215 |
| scalar_penalty | 200 | 0.068874 | 0.920894 | 175 | 245 |
| hard_gate | 200 | 0.991017 | masked | 0 | 764 |

Budget demo: 3 updates, 9/12 steps; conservative reservation stops further sampling.

## Release

- Final decision: `pass`
- Unsafe candidate: `fail`
- Stable schema: `chapter15.post-training.v2`
- The pass decision is static gate conformance, not independent evaluation of the learned policy or permission to publish a model.

## Evidence limits

- `finite_policy_not_llm_training`
- `fixed_fixture_not_production_distribution`
- `no_provider_conformance_claim`
- `no_gpu_training_performed`
