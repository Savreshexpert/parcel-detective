# Parcel Detective — project checkpoint

Updated: 22 October 2026 (IST). Owner: Sarvesh Yadav.

## Keep these decisions

- Selected idea: AI investigator for warehouse parcels marked missing.
- Real Strands Decider **2B** selects the next investigation source in AWS mode.
- Amazon Bedrock explains findings with supporting record IDs.
- Working agent must run on AWS. All demonstration records are fictional.
- Three core outcomes: suspected missed scan, suspected wrong bag, insufficient evidence requiring a physical check.
- Dashboard includes an evidence timeline, decision trace and editable clues.
- Twenty distinct cases measure accuracy, response time and tool calls.
- Submission: public source repository and reusable pattern, Builder Center article, public video under three minutes.
- Tags: #strands-decider-2b and #tool-selection.
- Target: 23 October 2026 evening IST. Official deadline: 24 October, 12:29 PM IST.

## Completed in v0.1

- Python investigation engine and working local HTTP dashboard.
- Responsive frontend layout, case queue, timeline, citations, decision trace, clue editor and JSON downloads.
- Twenty synthetic scenarios with separate expected answers and measured local JSON/CSV results.
- Eighteen Python checks and four JavaScript logic checks covering case isolation, tool order, conflicting evidence, provider contracts and dashboard loading/polling.
- Bedrock Converse adapter, real Decider HTTP adapter, explicit live failures and no automatic demo fallback.
- Private EC2 deployment template, service files, installer and actual-access preflight command.
- Simple setup guide, reusable-pattern documentation, article draft and video plan.
- Complete source ZIP with a root `app.py`, Windows start file and short VS Code instructions. Frontend source is formatted for reading and editing.

## Changes in v0.1.1

- Cached and indexed fictional records with automatic refresh after a file edit.
- One final evidence assessment per run; all three sources remain mandatory.
- Reused provider clients, fewer queue redraws and slower polling during long evaluations.
- Clearer source formatting and removal of unused state and the unnecessary npm manifest.
- Later generic notes cannot erase an unresolved verified hold; tied conflicting dispatch updates require a check.
- Measured local computation comparison is in `docs/PERFORMANCE_REVIEW.md`. No AWS inference speedup is claimed.

## Remaining before submission

1. Confirm Sarvesh's AWS Console and Bedrock playground access.
2. Review the deployment's AWS costs and launch the private EC2 host.
3. Verify package installation, real Decider response fields/model identity and Bedrock permissions with preflight.
4. Check the complete dashboard in a browser on desktop and phone; visual QA was blocked by the build environment's browser policy.
5. Run live investigations, inspect generated explanations, and save the twenty-case live evaluation.
6. Freeze successful dependencies and upstream model/source revisions.
7. Publish the public GitHub repository. The GitHub integration has been suggested but its connection is not confirmed.
8. Complete and publish the Builder Center article with actual results.
9. Record and publish a real AWS demo under three minutes, then submit links and tags.

## Known limits

- Local 20/20 accuracy is a regression result for development fixtures, not AI accuracy.
- All three sources are required in v0.1; Decider chooses order. No tool-count saving is claimed.
- Bedrock citation validation checks record IDs and outcome consistency, not complete semantic entailment.
- Confidence is about the selected tool, not parcel location.
- Physical-check requests are prepared on screen, not sent to workers.
- Cloud deployment is prepared, not completed. The local API server is intended for private demonstration.
- Data and clue edits are not a production warehouse integration; edits are scoped to one run/browser session.
