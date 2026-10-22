# Start here, Sarvesh

We are keeping **Parcel Detective** as the selected project.

Think of the project as three jobs:

1. **Decider chooses what to check next.** For example: scans, dispatch records or handover notes.
2. **The code reads and compares records.** Every clue keeps its record number.
3. **Bedrock explains the result.** The worker sees the evidence and a suggested place to check.

## Do this first

1. Extract the complete ZIP. Open the `parcel-detective` folder in VS Code and run `python app.py` in its terminal. Open `http://127.0.0.1:8080`. On Windows you can also double-click `START_WINDOWS.bat`. The local demo works without an AWS account or extra packages; `START_HERE.txt` explains each step.
2. Sign in to your **AWS Console**. Builder Center registration and AWS Console access are different things.
3. Select **US East (N. Virginia) / us-east-1** for this setup.
4. Search for **Amazon Bedrock**, open the model catalogue, select **Amazon Nova Lite**, and open its playground.
5. Send: `Reply with: Parcel Detective connection works.`

If the playground replies, tell us the model and Region you used. If it shows an error, share the exact error or a cropped screenshot with account IDs and personal details hidden. Do not send passwords, access keys or secret keys.

A playground reply proves your signed-in user can call that model. The EC2 role needs a separate preflight test later.

## What you can already try

- P104: a missed scan is suspected.
- P105: a wrong dispatch bag is suspected.
- P106: records are incomplete, so a physical check is requested.
- P104 → Change a clue → Remove last record → Apply & investigate: the evidence is no longer sufficient.
- Evaluation lab → Run 20 cases: see real measurements for the local rules.

## Schedule in IST

| Date | Work | Finish condition |
| --- | --- | --- |
| 21 October evening | Local prototype and AWS access check | Dashboard runs; Bedrock access status is known. |
| 22 October | Deploy on AWS, run Decider and Bedrock, fix integration failures | Preflight and all three core demonstration scenarios work on EC2. |
| 23 October morning/afternoon | Run the live 20-case evaluation, review explanations, polish demo | Genuine AWS results saved; weak cases reported honestly. |
| 23 October evening | Publish public repository, article and a video under 3 minutes | Submission page contains working links and both required tags. |
| 24 October, 12:29 PM | Official deadline | Submission must already be complete. |

The AWS account check is the immediate dependency. We should not spend the last evening solving account or model-access problems.
