# AWS setup in simple steps

This deployment is prepared but has **not** been executed in your account. No AWS account access is available in the current build environment. Package installation, the live Decider response contract, instance capacity and Bedrock access must pass the checks below.

## What the services mean

- **EC2:** the rented AWS computer that runs the dashboard, Python agent and Decider.
- **Bedrock:** the AWS service that writes the explanation from retrieved evidence.
- **IAM role:** gives that AWS computer permission to call Bedrock without storing access keys.
- **S3:** a private place to upload the project ZIP for installation.
- **Session Manager:** a secure connection to the AWS computer without opening SSH or web ports to everyone.

## 1. Confirm the account and model

Open the AWS Console. Select `us-east-1` (N. Virginia), then Amazon Bedrock → model catalogue → Amazon Nova Lite → playground. Send a short test message. The prepared code uses `amazon.nova-lite-v1:0` and the Converse API.

The current Bedrock documentation says many models can be used directly from the catalogue/playground when permissions are sufficient. Do not depend on an old “request model access” screen being present. An access error can still involve IAM, account restrictions, Region support or provider prerequisites.

If a different model or an inference profile is needed, change both `BEDROCK_MODEL_ID` and the IAM resource permissions deliberately. The included role permits only the direct Nova Lite model in this Region; it does not grant arbitrary model access.

## 2. Review cost before launching

The template creates an EC2 instance, a 50 GiB encrypted disk and a public IPv4 address used for outbound downloads. Bedrock requests also incur charges. This is **not promised to be free tier**. Review the current EC2, EBS, IPv4 and Bedrock estimates in your account, and set a small AWS Budget alert. Budget alerts notify you; they do not automatically stop spending.

The CPU configuration starts with `m7i.xlarge` (4 vCPUs, 16 GiB). It avoids a GPU quota dependency but may be slow. The Decider model downloads several gigabytes on first start. If installation or inference runs out of memory, inspect logs before choosing a larger allowed instance and reviewing its cost. No latency claim has been made for this host.

## 3. Upload the source ZIP privately

In S3, create a private bucket in `us-east-1` with a unique name. Keep **Block all public access** enabled. For this prototype, use the default S3-managed encryption; a customer-managed KMS key would need extra role permissions.

Upload `Parcel-Detective-Reviewed.zip`. The ZIP must contain a top-level `parcel-detective/` folder. Copy the bucket name and object key.

## 4. Create the demo host

In CloudFormation → Create stack → Upload a template file, upload `infra/ec2.yaml` from the extracted project.

- Stack name: `parcel-detective-demo`
- SourceBucket: the private bucket name from step 3
- SourceKey: `Parcel-Detective-Reviewed.zip` (or the exact uploaded name)
- InstanceType: review the default and its cost

Review the resources and IAM role. The role allows Session Manager, retrieval of this one ZIP, and invocation of the selected Bedrock model. Create the stack after that review.

The template does **not** open public inbound ports. It creates its own VPC and outbound internet route for package/model downloads. After the stack finishes, its Outputs tab shows the instance ID. `CREATE_COMPLETE` alone does not mean the model has downloaded or the app works.

## 5. Check installation

In EC2, select the instance → Connect → Session Manager. In the terminal, run:

```sh
sudo tail -n 60 /var/log/cloud-init-output.log
sudo systemctl status parcel-decider parcel-detective --no-pager
sudo journalctl -u parcel-decider -n 60 --no-pager
```

Wait for model download and loading to finish. If the installer failed, fix the stated dependency error before rerunning it. It uses current official Decider source because the October reference model is newer than the initial PyPI release. The exact installed source commit and dependencies are recorded in `runtime/installed-requirements.txt`. Preserve this file for reproducibility.

Now test the actual providers:

```sh
sudo -u ec2-user bash
cd /opt/parcel-detective
set -a
source .env
set +a
.venv/bin/python scripts/preflight.py
```

Preflight verifies AWS credentials, sends one small Bedrock request, checks Decider health, and sends a real typed-choice request. It must report `ready: true`. If it fails, retain the error. The included mocked tests cannot prove live compatibility.

## 6. Open the AWS dashboard privately

On your laptop, install the official AWS CLI v2 and Session Manager plugin. Sign in using your normal AWS CLI profile/SSO. Do not paste credentials into project files.

Run this after replacing `YOUR_INSTANCE_ID` with the CloudFormation output:

```sh
aws ssm start-session --target YOUR_INSTANCE_ID --document-name AWS-StartPortForwardingSession --parameters '{"portNumber":["8080"],"localPortNumber":["8080"]}' --region us-east-1
```

PowerShell accepts the single-quoted JSON above. Keep this terminal open, then open `http://127.0.0.1:8080` in your laptop browser. The page is now served by **EC2 through the secure tunnel**. Its address being localhost does not mean the agent runs on your laptop.

The person opening this tunnel needs IAM permission for Session Manager on this instance. Do not add broad administrator permissions just to resolve a missing permission.

## 7. Verify the real investigation

Run P104, P105 and P106. Check the Decision trace:

- The first two selections should say **Strands Decider 2B**, with the actual model identifier.
- The final remaining source and terminal step should say **Host evidence policy**.
- The explanation should say **Amazon Bedrock**, except a case with no records to cite.
- Record-ID buttons should open real timeline entries.

Then run the live evaluation on EC2:

```sh
cd /opt/parcel-detective
set -a
source .env
set +a
.venv/bin/python -m parcel_detective.evaluate --mode aws --repeats 3 --output evaluation/results-aws.json
```

Do not run the CLI evaluator and dashboard investigations simultaneously. The web server serialises its own model requests; a separate CLI process is outside that lock. The dashboard's Evaluation lab runs the same suite once and can download the results.

## 8. Record, then shut down

Record the demo while the real AWS mode is working. Keep the public video shorter than three minutes. The hackathon requires a public video, not necessarily a public unauthenticated dashboard. This private tunnel keeps the model and the prototype server off the public internet.

When you finish using the host, stop it to reduce compute charges. Storage can still be billed while stopped. When the demonstration is no longer needed, delete the CloudFormation stack; the template deletes its root disk on instance termination. The separately created S3 bucket remains and must be cleaned up separately. Save your results before deleting anything.

## Common issues

| Message | Next step |
| --- | --- |
| Unable to locate credentials | Confirm the EC2 instance profile or sign in to the local AWS CLI. |
| AccessDeniedException | Check the caller's IAM role, supported Region and model access. A successful personal playground test does not grant permissions to the EC2 role. |
| Connection refused on port 8000 | Read the Decider service log; downloading/loading may still be in progress. |
| Invalid choice/model response | Save the provider response locally and compare with the installed official API. Do not replace the real response with a fake success. |
| Bedrock cites unsupported IDs | Inspect the generated explanation; adjust its prompt or validation, then rerun. It is a real failure. |
| 422 context window error | Reduce clue length; `--strict-window` deliberately rejects silently truncated evidence. |
| No Session Manager connection | Check instance boot logs, SSM role, internet route and agent status. |

For public hosting later, add HTTPS, authentication, rate limits, deployment hardening and a production server. The standard-library HTTP server here is scoped to the private hackathon demonstration.
