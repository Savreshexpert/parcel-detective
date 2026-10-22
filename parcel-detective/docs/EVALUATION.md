# Evaluation protocol

The first version has **20 separate fictional development cases**. Expected answers live in `evaluation/ground_truth.json`. The runtime reads only `data/cases.json`; expected answers are never included in a Decider state or Bedrock prompt.

The cases exercise seven missed-scan scenarios, seven wrong-bag scenarios and six incomplete/contradictory scenarios. These fixtures were used to build the rules. They do not establish real-world accuracy or held-out model generalisation.

## Measurements

| Metric | Definition |
| --- | --- |
| Accuracy | Correct outcome **and** physical-check flag **and** required location text, divided by all attempted cases. Provider failures count as incorrect. |
| Response time | `perf_counter` wall time from case load through source selection, evidence assessment and explanation validation. Excludes browser/network transit. |
| Median / p95 | Median and nearest-rank 95th percentile of successfully completed runs; error count is shown separately. |
| Evidence tool calls | Number of source reads actually completed. In v0.1 this is three per successful case. |
| Decider calls | Actual attempted selections on successful live traces, excluding single-option host steps. |
| Bedrock calls | One per nonempty live explanation; zero for empty-record host messages. |
| Citation IDs valid | Every displayed citation is an allowed retrieved supporting record ID. This does not prove the generated wording is factually entailed. |

The current evaluator reports call counts and duration as unknown for failures. It does not estimate billable usage for a partly completed failed run. Inspect provider/server logs for those calls. Do not interpret unknown as zero.

## Local results

`results-demo.json` and `.csv` are real measurements of the demo rules and templates. They passed all twenty current fixtures. Those measurements are **not** Decider or Bedrock results and should not be presented as AI accuracy or model latency.

## Live procedure

1. Run `scripts/preflight.py` on the AWS machine and retain successful output without account identifiers.
2. Record instance type, Region, model name/revision and `runtime/installed-requirements.txt`.
3. Stop interactive dashboard requests while running the CLI evaluation.
4. Run `--mode aws --repeats 3` for sixty attempts over twenty unique cases.
5. Keep the first cold attempt and label it. If reporting warm-only measurements, calculate them separately and explain the exclusion.
6. Read the three main scenarios' Bedrock explanations manually, then review every remaining explanation before publishing a semantic-correctness claim. ID membership validation alone is insufficient.
7. Save failures. Fixing a prompt and rerunning creates a new experiment; preserve both runs with distinct filenames.

## What is not measured yet

- Decider's choice quality against human-labelled next-tool decisions.
- Semantic entailment of all Bedrock sentences.
- Real warehouse performance or impact on workers.
- Improvement over an LLM-based selector or a fixed read order.
- Concurrency, public load or production security.

Do not claim performance or cost savings without a matched baseline. A useful next experiment is a separate held-out set with human-labelled preferred first tools and adversarial contradictory records.
