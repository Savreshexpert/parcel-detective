# Validation — 22 October 2026 (IST)

## Passed

- Twenty separate fictional development cases: 20 correct, zero errors.
- Eighteen Python checks: edited clues, cache isolation and refresh, every source ordering on representative cases, conflicting records, invalid inputs, provider failures and mocked provider contracts.
- Four JavaScript logic checks: queue preservation, immediate completed-job display, polling backoff and stale-job handling, and preventing overlapping case loads/investigations.
- JavaScript syntax, Python source parsing and shell script syntax checks.
- Extracted-package HTTP checks: start with `python app.py`; load dashboard assets and case APIs; run the three outcomes, edited-clue rerun and twenty-case evaluation.
- Before/after local computation benchmark with identical fixtures and seven rounds of 1,000 investigations per version. See `evaluation/performance-comparison.json`.
- Official event overview and embedded Rules text checked against included files. See `HACKATHON_REVIEW.md`.

The checks ran on Linux with Python 3.12.14. JavaScript logic tests use small DOM stubs; they do not render the dashboard. Windows launcher execution and Python 3.14 execution were not available in this environment.

Demo metrics measure the local router, rules and templates. They do not establish Decider decision accuracy or Bedrock explanation quality. Provider contract tests use mocks. The official Decider server and response tests were source-reviewed in the earlier package; live calls are still required.

## Still unverified

- Full desktop/mobile visual layout and browser interaction: the preview browser was blocked by the environment's browser policy; no alternate browser workaround was used.
- AWS infrastructure launch, dependency installation, model download and account permissions.
- Actual Decider checkpoint identity and predictions, and actual Bedrock responses.
- Live inference latency, cost and explanation correctness.
- Publication of the public repository, Builder Center article and public video.

Run AWS preflight, the live twenty-case suite and a manual dashboard check before submitting. A local test pass is not proof of AWS deployment or hackathon eligibility.
