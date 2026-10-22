# Demo video plan — target 2 minutes 45 seconds

Record this after real AWS mode and preflight work. Use your own screen recording and narration. Do not present local demo rules as Decider or Bedrock.

| Time | On screen | Say |
| --- | --- | --- |
| 0:00–0:15 | Dashboard, fictional-data label | “I'm Sarvesh. Parcel Detective helps a warehouse worker investigate a parcel marked missing, using evidence from scans, dispatch records and shift notes.” |
| 0:15–0:40 | Run P104; open Decision trace | “Strands Decider 2B chooses which evidence tool to use next. These steps show its actual choices, options and confidence. Single remaining options are handled by the host.” |
| 0:40–1:05 | P104 finding and clickable record IDs | “The loading record places this parcel in the expected bag, but the dispatch scan is absent. Bedrock explains that finding using these record IDs. We recommend a place to check; we don't claim the parcel has been found.” |
| 1:05–1:25 | Run P105 | “Here the actual dispatch bag differs from the expected bag. The record trail points the worker to the bag that was actually recorded.” |
| 1:25–1:55 | P104 → Change a clue → remove dispatch record → rerun | “Now I remove one clue and rerun the same case. The evidence is no longer sufficient, so Parcel Detective asks for a physical check.” |
| 1:55–2:15 | Actual completed AWS evaluation results | “These are twenty synthetic development cases. We measured outcome and location accuracy, response time and tool calls. These numbers come from the live AWS run.” Use the actual values and mention failures. |
| 2:15–2:35 | Brief architecture/readiness proof and source code | “The agent and Decider run on EC2. Bedrock is accessed through the instance role. The repository includes the reusable typed-choice selection pattern and its tests.” |
| 2:35–2:45 | Closing frame with title and tags | “The goal is a useful next step with evidence a worker can inspect. Parcel Detective: follow the records, keep the uncertainty.” |

Record in landscape. Hide account numbers, billing screens, personal information and credentials. Keep the exported video below 3:00; aim for 2:45. Long model waits can be cut, but label the cut and show actual measured duration. Do not manufacture a fast response.

Publish the final recording publicly on YouTube and add its URL to the submission. The Rules also list Vimeo, Facebook Video and Youku. Use your own narration and material, with no unlicensed music or third-party branding. The final public video has not been recorded or published yet.
