### Pipeline overview

```
PR / push to main
	|
	|---> lint.yml ------------------+
	|     (flake8, mypy,             |
	|      hadolint, shellcheck,     |  All must pass for PR merge
	|      yamllint)                 |
	|                                |
	+---> test.yml ------------------+
		 (pytest, coverage >=40%)
			 |
			 | push to main -> build.yml
			 | (tags: latest, sha-<hash>)
			 |
		 annotated tag (v*.*.*)
			 |
			 v
		 build.yml
		 (tags: stable, v*.*.*)
			 |
			 v
		 deploy.yml [self-hosted runner]
		 (SSH -> target VM -> docker compose pull + up)
			 |
			 v
		 verify.yml [self-hosted runner]
		 (pytest testinfra: endpoints, nginx rules)
```

### Required GitHub Secrets

| Secret | Description |
|---|---|
| DEPLOY_SSH_KEY_PATH | Path to SSH private key on runner (e.g., `/home/runner/.ssh/deploy_key`) |
| TARGET_NODE_IP | IP address of the target VM |
| DEPLOY_USER | SSH username on target VM (e.g., `student`) |
| GHCR_TOKEN | GitHub PAT with `read:packages` for pulling from GHCR |

### How to run tests locally

```bash
cd app
pip install -r requirements.txt
pytest
pytest --cov-report=html && open htmlcov/index.html
```

### How to trigger a deployment

```bash
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0
```

### Self-hosted runner setup

- Use [deploy/setup-runner.sh](deploy/setup-runner.sh) on a clean Ubuntu 24.04 VM.
- Runner registration is a manual step (token is not stored in repo).
- Stop the runner VM after demo for safety.

### Demonstration artifacts

- Successful PR with green checks
- Failing PR blocked by checks
- Successful deploy workflow run log
- Failed verify workflow run log
- Coverage report artifact from test workflow

### Branch protection rules

- See [.github/BRANCH_PROTECTION.md](.github/BRANCH_PROTECTION.md)