# Chapter 14 deterministic production-diagnostics report

> Offline teaching fixture. Cost units are not provider prices; Tail samples are not population denominators.

## Release comparison

| Release | Outcome | p95 latency (ms) | Cost units | Retry amplification | Telemetry completeness |
| --- | ---: | ---: | ---: | ---: | ---: |
| stable | 0.958333 | 432 | 16.030000 | 1.312500 | 0.958333 |
| incident | 0.958333 | 612 | 17.740000 | 1.437500 | 0.958333 |
| fixed | 0.958333 | 432 | 16.030000 | 1.312500 | 0.958333 |

## Incident conclusion

- Conclusion: `confirmed`
- Root cause: `retry_policy`
- Data completeness: `0.958333`
- Supporting traces: `3`
- Counterevidence traces: `4`

## Stable artifact contract

- Schema: `chapter14.diagnostics.v1`
- Scored traces: `72`
- Experiment groups: `5`
