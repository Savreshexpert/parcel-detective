#!/usr/bin/env bash
# Run on the Amazon Linux 2023 EC2 instance as ec2-user; use the attached role.
set -euo pipefail
cd /opt/parcel-detective
python3.12 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements-aws.txt
.venv/bin/python -m pip install torch==2.7.1 --index-url https://download.pytorch.org/whl/cpu
.venv/bin/python -m pip install transformers==5.17.0 peft==0.21.0
# Current upstream code is needed for the October reference model. Record the
# exact installed Git commit via pip freeze; live install has not been verified.
.venv/bin/python -m pip install 'strands-decider @ git+https://github.com/strands-labs/strands-decider@main'
mkdir -p runtime
.venv/bin/python -m pip freeze > runtime/installed-requirements.txt
sudo cp infra/parcel-decider.service /etc/systemd/system/parcel-decider.service
sudo cp infra/parcel-detective.service /etc/systemd/system/parcel-detective.service
sudo systemctl daemon-reload
sudo systemctl enable --now parcel-decider parcel-detective
echo 'Services started. Model download can take several minutes. Check journalctl, then run scripts/preflight.py.'
