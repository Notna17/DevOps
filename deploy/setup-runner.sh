#!/usr/bin/env bash
# Sets up a fresh Ubuntu 24.04 VM as a GitHub Actions self-hosted runner.
# Run as root or with sudo.
# After running this script, manually register the runner:
#   cd /home/runner/actions-runner
#   ./config.sh --url https://github.com/YOUR/REPO --token YOUR_TOKEN
#   sudo ./svc.sh install && sudo ./svc.sh start

set -euo pipefail

RUNNER_VERSION="2.317.0"
RUNNER_USER="runner"
RUNNER_HOME="/home/runner"

echo "=== Installing prerequisites ==="
apt-get update -qq
apt-get install -y curl git docker.io python3 python3-pip openssh-client jq

echo "=== Creating runner user ==="
id "${RUNNER_USER}" &>/dev/null || useradd -m -s /bin/bash "${RUNNER_USER}"
usermod -aG docker "${RUNNER_USER}"

echo "=== Downloading GitHub Actions runner ==="
mkdir -p "${RUNNER_HOME}/actions-runner"
cd "${RUNNER_HOME}/actions-runner"
curl -sL \
  "https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz" \
  -o runner.tar.gz
tar xzf runner.tar.gz
rm runner.tar.gz
chown -R "${RUNNER_USER}:${RUNNER_USER}" "${RUNNER_HOME}/actions-runner"

echo "=== Generating SSH key for deployment ==="
sudo -u "${RUNNER_USER}" ssh-keygen -t ed25519 \
  -f "${RUNNER_HOME}/.ssh/deploy_key" \
  -C "github-actions-deploy" -N "" 2>/dev/null || true

echo ""
echo "=== NEXT STEPS (manual) ==="
echo "1. Copy the deploy public key to the target VM:"
echo "   cat ${RUNNER_HOME}/.ssh/deploy_key.pub"
echo "   # Add this to target VM's /home/student/.ssh/authorized_keys"
echo ""
echo "2. Register the runner (get token from GitHub repo → Settings → Actions → Runners → New):"
echo "   sudo -u ${RUNNER_USER} bash -c 'cd ${RUNNER_HOME}/actions-runner && \
     ./config.sh --url https://github.com/YOUR_USER/YOUR_REPO --token YOUR_TOKEN'"
echo ""
echo "3. Install and start as a service:"
echo "   cd ${RUNNER_HOME}/actions-runner && sudo ./svc.sh install ${RUNNER_USER}"
echo "   sudo ./svc.sh start"
echo ""
echo "4. Add these GitHub Secrets to your repository:"
echo "   DEPLOY_SSH_KEY_PATH = ${RUNNER_HOME}/.ssh/deploy_key"
echo "   TARGET_NODE_IP      = <IP of your target VM>"
echo "   DEPLOY_USER         = student"
echo "   GHCR_TOKEN          = <GitHub PAT with read:packages>"
