# Parcel Detective: following the evidence behind a missing-parcel alert

**Draft — complete the live AWS deployment, results and links before publishing.**

Tags: **#strands-decider-2b #tool-selection**

A missing-parcel alert leaves a worker with a practical question: where should I look next? A scanner log, a loading sheet and a shift note may each contain only part of the answer.

I am building Parcel Detective to turn those records into a traceable investigation. The demonstration uses fictional warehouse data. Its output is a provisional finding with supporting record IDs and a suggested location to check. If evidence is missing or contradictory, it prepares a physical-check request.

## The decision I handed to Decider

Strands Decider 2B chooses the next evidence-source tool. It receives the case report, records already retrieved and a typed set of available options: scan history, dispatch records and handover notes.

The host validates the selected name against an allowlist and runs the corresponding function. Each result adds real record IDs to the evidence timeline. Already-used sources are removed from the option set. When only one source remains, the host executes it without attributing that step to the model.

The first version requires all three sources before concluding. That is deliberate: an unread handover note might contradict a loading record. Decider therefore controls source order, while the host controls evidence completeness. I am not claiming fewer source reads or a model latency improvement. The local code optimization measurement in `docs/PERFORMANCE_REVIEW.md` is separate from model performance.

## Why Bedrock has a separate job

Python rules compare actual and expected bags, look for a missing dispatch scan, and identify insufficient or conflicting records. Amazon Bedrock then writes a short explanation using those findings and their supporting evidence.

The response must preserve the outcome and cite permitted record IDs. The host rejects missing or invented citations. This validates the citation references; a worker still needs to check whether every generated sentence is justified by the records.

## Three useful examples

In P104, the dispatch record contains the parcel in the expected bag, but there is no matching dispatch scan. The suggested next step is to inspect that bag.

In P105, the actual bag differs from the expected bag. The investigation points to the actual loading record and names the bag to check.

In P106, the dispatch record is missing. The application explains the gap and prepares a physical check instead of asserting a location.

The dashboard also allows a viewer to edit a clue. Removing P104's loading record changes its outcome from a suspected missed scan to insufficient evidence. Original fixtures remain unchanged so the experiment is repeatable.

## Deployment and measurements

The prepared deployment runs the dashboard, agent and Decider on an EC2 CPU instance. Bedrock is called with the instance role. Session Manager provides private access for recording the demonstration, with no public model port or stored AWS access keys.

**Complete after live verification:** Region, instance type, exact source/model revision, preflight result, live outcome accuracy, median/p95 response time, failure count and mean tool calls.

The included twenty synthetic development cases currently pass with the local rule-based router. That is a software regression result, not a measurement of the real models. The live evaluator uses the same cases and includes provider errors in the accuracy denominator. The source records and expected results are stored separately.

## A pattern others can reuse

The repository includes a standalone typed-choice client, a bounded tool registry, option filtering and execution tracing. Another builder can replace the warehouse tools with their own evidence sources while keeping the same select–validate–execute loop.

The lesson so far is that a small decision model can have a precise job inside an agent without being asked to invent a narrative. Keeping the evidence rules, source decisions and explanation separate makes each part easier to inspect.

**Before publishing:** replace this draft status; add the verified public repository URL, public video URL and genuine AWS measurements. Preserve the limitations above.
