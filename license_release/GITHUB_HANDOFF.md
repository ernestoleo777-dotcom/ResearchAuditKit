# GitHub Publication Handoff

## Step 1: create an empty repository

Create `ResearchAuditKit` on GitHub. Choose visibility yourself. Do not initialize it with a README, LICENSE, `.gitignore`, or template.

## Step 2: inspect locally before adding a remote

```bash
git status
git log --oneline --decorate -n 12
git remote -v
git tag --list
```

Confirm a clean tree, Apache-2.0 consistency, passing tests, passing builds, and zero forbidden assets.

## Step 3: add the remote

```bash
git remote add origin <USER_PROVIDED_GITHUB_REPOSITORY_URL>
```

## Step 4: push the current branch

```bash
git push -u origin <CURRENT_BRANCH>
```

Do not run these commands until the user supplies the URL and has completed the local review.

## Step 5: verify the remote

Review README rendering, GitHub Apache-2.0 recognition, CI, package metadata, the public file list, and privacy/security posture.

## Step 6: tags, releases, and PyPI

The current package version is `0.1.0`, not `0.1.0rc1`; do not create `v0.1.0-rc.1` unless a separately approved version alignment makes it truthful. Do not create a GitHub Release until remote CI and manual review pass. `DO_NOT_PUBLISH_TO_PYPI_YET`.
