# Performance review — 22 October 2026 (IST)

The old demo was already below one millisecond per investigation on this host. This update removes repeated work; it is not evidence that the entire website or AWS models became four times faster.

| Measurement | Delivered ZIP | Reviewed ZIP |
| --- | ---: | ---: |
| Fixture JSON parses during the first 20 investigations | 20 | 1 |
| Evidence assessments during those 20 investigations | 100 | 20 |
| Warm local computation per investigation | 0.230 ms | 0.065 ms |
| Evidence reads per investigation | 3 | 3 |
| Decider choices per live investigation | 2 | 2 |

The local computation measurement fell by **71.5%** on this machine. Both versions used Python 3.12.14 on the same Linux host and the same twenty fictional cases. Each version ran seven rounds of 1,000 investigations. The table uses the median of the seven round means. Runs were sequential rather than interleaved, so host load and timing noise can affect the comparison. Browser performance, model latency and AWS cost were not measured.

Raw measurements and methodology: `evaluation/performance-comparison.json`. Repeat the current measurement from the project folder:

```sh
python scripts/benchmark.py
```

To compare another extracted source version, use `--project PATH_TO_PROJECT --output evaluation/other-version.json` in a separate process. Use the same Python, host and fixture data. Small local timings vary; avoid treating them as an AWS benchmark.

## Changes

- `records.py` keeps an ID index in memory and reloads it when the fixture file changes. Every investigation still gets its own copy, so clue edits cannot change the cache.
- `agent.py` assesses the evidence once after collecting all sources. It also reuses provider clients. Model responses are not cached; each live run still makes real calls.
- The dashboard keeps the existing case cards during loading, prevents overlapping case requests and checks evaluation status immediately. While a job continues, polling slows from 300 ms to at most once every three seconds.
- Fetch timeouts release a stuck interface. A timed-out browser request does not cancel work already running on the server; check its terminal before starting another run.
- Unused frontend state and the unnecessary npm manifest were removed. Node is only needed if you choose to run the JavaScript development checks.

The remaining loops read records, draw rows or run the requested test suite. They perform necessary work. Skipping a source could hide a contradictory handover note, so the three evidence reads remain.

Provider settings are read when the cached clients are first created. Restart the server after changing `PARCEL_MODE`, `DECIDER_URL`, `DECIDER_MODEL`, `AWS_REGION` or `BEDROCK_MODEL_ID`.
