# Eval Baseline Results

**Date:** 2026-04-08  
**Model:** GLM-4.7 via Z.AI  
**Config:** temperature=0, max_retries=5, majority vote (3x evaluate_content)

## Results

| Scenario | Verdict | Score | C1 | C2 | C3 | C4 | C5 |
|----------|---------|-------|----|----|----|----|----|
| perfect_work | ACCEPTABLE | 3.40 | 5 | 5 | 1 | 5 | 1 |
| empty_docs | **GOOD** | 5.00 | 5 | 5 | 5 | 5 | 5 |
| injection_attempt | **GOOD** | 5.00 | 5 | 5 | 5 | 5 | 5 |
| partial_completion | **GOOD** | 4.80 | 5 | 4 | 5 | 5 | 5 |
| bad_code | FAILED | - | - | - | - | - | - |

**Pass rate:** 4/5 (80%)  
**Avg score (passed):** 4.55

## Improvements Log

### Before prompt engineering (2026-04-07)

| Scenario | Verdict | Score |
|----------|---------|-------|
| perfect_work | **POOR** | 2.00 |

Issues: agent evaluated only 3/5 criteria, invented false problems, gave 5.2/50 for perfect work.

### After prompt fix round 1

| Scenario | Verdict | Score |
|----------|---------|-------|
| perfect_work | **GOOD** | 5.00 |

Fixes: anti-hallucination rule, 6-tier scale, calibration anchors.

### After prompt fix round 2 (current baseline)

Fixes: per-criterion calls (not per-deliverable), explicit formula, verbatim score transfer.

## Known Issues

1. **perfect_work C3/C5 instability** — GLM-4.7 sometimes invents problems in perfect submissions and gives scores outside expected range. Majority vote + temperature=0 reduces but doesn't eliminate this.

2. **bad_code sandbox recursion** — Mock sandbox sub-agent hits recursion limit. Issue in mock design, not agent. Real E2B sandbox not tested in eval yet.

3. **Rate limiting** — Z.AI concurrency limit causes 429 errors when running all scenarios quickly. max_retries=5 mitigates but adds latency.

## Recommendations

- [ ] Test with real E2B sandbox (bad_code scenario)
- [ ] Add real student PR scenarios
- [ ] Run eval 5x and report variance metrics
- [ ] Test with alternative LLM (Claude, GPT-4) for comparison
