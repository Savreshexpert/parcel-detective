# Parcel Detective

An evidence-first investigator for warehouse parcels marked missing.

**Project owner:** Sarvesh Yadav. **Data:** entirely fictional. **Stage:** working local prototype; real AWS deployment and model calls are pending verification.

The dashboard collects scan history, dispatch records and shift handover notes. It shows a provisional finding, a record timeline, the tool-selection trace and the next place a worker should check. Incomplete or contradictory evidence prepares a physical-check request. It does not send that request or claim to have found the parcel.

## Start on your laptop

1. Install Python 3.10 or newer if you do not already have it.
2. Right-click the ZIP and choose **Extract All**. Open the `parcel-detective` folder in VS Code.
3. Open **Terminal → New Terminal** and run:

```sh
python app.py
```

On Windows, use `py app.py` if `python` is unavailable. You can also double-click **START_WINDOWS.bat**. On macOS/Linux, use `python3 app.py`. Keep the terminal open while using the app; press Ctrl+C to stop it.

4. Open **http://127.0.0.1:8080** in your browser.
5. Choose P104 and click **Investigate parcel**.

Local demo mode needs no packages, cloud account or API key. It uses clearly labelled rules and templates. It does **not** satisfy the live-model hackathon requirement.

Use this Python server rather than opening `web/index.html` directly: the page needs its API. If port 8080 is busy, run `python app.py --port 8081` and open that port instead. The module command `python -m parcel_detective.server` also remains supported.

## First demonstration

| Parcel | What to show |
| --- | --- |
| P104 | Loading record with no matching dispatch scan; show the linked record IDs. |
| P105 | Loaded bag differs from expected bag. |
| P106 | Missing dispatch record leads to a physical check. |
| P104 again | Open Change a clue, remove the dispatch record, click Apply & investigate. The result changes to a physical check. Restore original to reset. |

The queue contains twenty distinct synthetic scenarios, including stale records, an unverified handover, a conflicting later note, cancelled loading, two simultaneous bags and an adversarial note.

## What actually runs

| Component | Local demo | AWS mode |
| --- | --- | --- |
| Next evidence tool | Explicit demo rules | Real Strands Decider 2B typed-choice HTTP request |
| Source reads | Fictional JSON records | The same fictional JSON records on EC2 |
| Evidence assessment | Conservative Python rules | The same conservative rules |
| Explanation | Template with real record IDs | Amazon Bedrock Converse response with checked record IDs |
| Physical check | Prepared on screen | Prepared on screen |

In v0.1 the model chooses the order of the first two evidence-source calls. The host chooses the last remaining source and requires all three sources before producing a finding. This ensures a later conflicting note is not skipped. We do not claim reduced tool calls, an adaptive early exit, or an AI-derived diagnosis. Confidence describes a **tool choice**, not the probability that a parcel is physically at a location.

AWS mode never silently switches to the demo router if a provider fails. A zero-record case uses a labelled host message, because there is nothing for Bedrock to cite.

## Run the checks

```sh
python -m unittest discover -s tests -v
python -m parcel_detective.evaluate --mode demo
```

The included run passed **20/20 development cases** and the additional automated checks. Read `evaluation/results-demo.json` and `.csv` for measured response times and counts. Those very small local timings measure Python rules, not Decider or Bedrock latency. The fixtures helped design the rules, so they are not a held-out benchmark.

After AWS preflight succeeds, run:

```sh
python -m parcel_detective.evaluate --mode aws --repeats 3 --output evaluation/results-aws.json
```

This makes real model calls. Preserve failures, the first cold run, hardware details and model revisions. Compare only equivalent workloads. See `docs/EVALUATION.md`.

## Continue the project

- `docs/START_HERE.md`: plain-English next steps and target schedule.
- `docs/HACKATHON_REVIEW.md`: official requirements mapped to the code and outstanding submission work.
- `docs/PERFORMANCE_REVIEW.md`: measured local improvements and the loops that remain necessary.
- `docs/AWS_SETUP.md`: AWS access check and private deployment.
- `docs/DECIDER_PATTERN.md`: reusable tool-selection pattern.
- `docs/BUILDER_ARTICLE_DRAFT.md`: article draft; complete live results before publishing.
- `docs/VIDEO_SCRIPT.md`: 2 minute 45 second recording plan.
- `PROJECT_STATUS.md`: completed work, remaining work and known limits.

## Project layout

| Path | Purpose |
| --- | --- |
| `app.py` / `START_WINDOWS.bat` | Start the complete local dashboard and API |
| `START_HERE.txt` | Short Windows and VS Code instructions |
| `parcel_detective/selector.py` | Typed question, option allowlist and real Decider HTTP client |
| `parcel_detective/agent.py` | Bounded investigation loop and complete trace |
| `parcel_detective/evidence.py` | Rules for missing scans, wrong bags and insufficient evidence |
| `parcel_detective/explainer.py` | Bedrock Converse and record-ID validation |
| `parcel_detective/server.py` | Private HTTP dashboard/API server |
| `web/` | Responsive dashboard; no frontend packages |
| `data/cases.json` | Fictional records; no expected answers |
| `evaluation/ground_truth.json` | Expected results; read only by the evaluator |
| `infra/` | EC2 CloudFormation template and service definitions |
| `tests/` | Behaviour and mocked-provider tests |

## Submission

Tags: **#strands-decider-2b #tool-selection**.

The official event closes on **24 October 2026 at 12:29 PM IST** (23 October at 11:59 PM PDT). Our target is **23 October evening IST**. Submission needs an AWS-running agent, real Decider and Bedrock use, a public source repository, a Builder Center article, and a public demo video shorter than three minutes.

Official event: https://builder.aws.com/build/hackathons/4f50957c-1d08-37ab-b11c-97516b9adeb4/agent-experience-hackathon-strands-decider

Sources checked on 21 October 2026 are listed in `docs/SOURCES.md`.

The guidelines and performance review was updated on 22 October 2026 (IST). The code uses Python's standard library for the demo, with plain HTML, CSS and JavaScript for the dashboard. Provider clients are reused; restart the server after changing AWS configuration. Optional JavaScript checks run with `node --test tests/test_dashboard.cjs`.
