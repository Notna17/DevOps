# Branch Protection Rules for `main`

Configure these rules in GitHub → Settings → Branches → Add rule for `main`:

## Required status checks before merging:
- [ ] lint-python
- [ ] lint-docker
- [ ] lint-shell
- [ ] lint-yaml
- [ ] test

## Other settings:
- [x] Require status checks to pass before merging
- [x] Require branches to be up to date before merging
- [x] Do not allow bypassing the above settings
