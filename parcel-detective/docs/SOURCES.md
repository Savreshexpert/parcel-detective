# Official sources checked on 21 October 2026

- Hackathon requirements, deadline, submission tags and judging: https://builder.aws.com/build/hackathons/4f50957c-1d08-37ab-b11c-97516b9adeb4/agent-experience-hackathon-strands-decider
- Strands Decider repository and current 2B checkpoint: https://github.com/strands-labs/strands-decider
- Inference installation, typed questions, HTTP endpoint and strict context window: https://github.com/strands-labs/strands-decider/blob/main/docs/inference.md
- Deployment options: https://github.com/strands-labs/strands-decider/blob/main/deploy/README.md
- Current upstream package dependencies: https://github.com/strands-labs/strands-decider/blob/main/pyproject.toml
- Amazon Nova on Bedrock, including Converse: https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-nova.html
- Current Bedrock model-access guidance: https://docs.aws.amazon.com/bedrock/latest/userguide/model-access.html
- Nova Lite model card and identifiers: https://docs.aws.amazon.com/bedrock/latest/userguide/model-card-amazon-nova-lite.html
- Session Manager port forwarding: https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-sessions-start.html

The source contract and installation instructions were checked from official documentation. Live AWS access, installation and inference have not been verified in this environment.

Response contract cross-check for the complete source package (21 October 2026):

- Official server: https://github.com/strands-labs/strands-decider/blob/main/src/strands_decider/server.py
- Official response tests: https://github.com/strands-labs/strands-decider/blob/main/tests/test_server.py

Review on 22 October 2026 (IST): the official event page and its embedded Rules text were rechecked. See `HACKATHON_REVIEW.md` for the current status.
