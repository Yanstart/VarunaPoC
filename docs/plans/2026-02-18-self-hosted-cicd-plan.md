# Self-Hosted CI/CD Pipeline — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Set up a dockerized GitHub Actions self-hosted runner with local Docker registry and `act` CLI for local workflow testing.

**Architecture:** A Docker Compose stack runs the GitHub Actions runner (myoung34/github-runner) and a local Docker registry (registry:2) on the developer's Linux machine. All 3 existing workflows (ci.yml, cd.yml, security.yml) are modified to use a `runs-on` fallback pattern that switches between self-hosted and ubuntu-latest via a repo variable. `act` is configured for offline local testing.

**Tech Stack:** Docker Compose, GitHub Actions, myoung34/github-runner, registry:2, act CLI, bash

**Design doc:** `docs/plans/2026-02-18-self-hosted-cicd-design.md`

---

## Task 1: Create runner Docker Compose stack

**Files:**
- Create: `.github/runner/docker-compose.yml`
- Create: `.github/runner/.env.example`

**Step 1: Create the Docker Compose file**

Create `.github/runner/docker-compose.yml`:

```yaml
# Self-hosted GitHub Actions runner stack
# Usage:
#   cp .env.example .env  # then fill in ACCESS_TOKEN
#   docker compose up -d
#   docker compose logs -f github-runner

services:
  github-runner:
    image: myoung34/github-runner:latest
    restart: unless-stopped
    environment:
      REPO_URL: ${REPO_URL:-https://github.com/Yanstart/VarunaPoC}
      ACCESS_TOKEN: ${ACCESS_TOKEN:?ACCESS_TOKEN is required - GitHub PAT with repo scope}
      RUNNER_NAME: ${RUNNER_NAME:-varuna-local}
      RUNNER_WORKDIR: /tmp/runner/work
      LABELS: self-hosted,linux,x64,varuna
      DISABLE_AUTO_UPDATE: "true"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - runner-work:/tmp/runner/work
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"

  registry:
    image: registry:2
    restart: unless-stopped
    ports:
      - "5000:5000"
    volumes:
      - registry-data:/var/lib/registry
    environment:
      REGISTRY_STORAGE_DELETE_ENABLED: "true"
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"

volumes:
  runner-work:
  registry-data:
```

**Step 2: Create the .env.example template**

Create `.github/runner/.env.example`:

```bash
# GitHub Actions Self-Hosted Runner Configuration
# Copy this file to .env and fill in your values:
#   cp .env.example .env

# GitHub repository URL
REPO_URL=https://github.com/Yanstart/VarunaPoC

# GitHub Personal Access Token (PAT) with 'repo' scope
# Generate at: https://github.com/settings/tokens
# Required scope: repo (Full control of private repositories)
ACCESS_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Runner display name (shown in GitHub Settings > Actions > Runners)
RUNNER_NAME=varuna-local
```

**Step 3: Validate Docker Compose syntax**

Run: `cd /data/VarunaPoC/.github/runner && docker compose config --quiet`
Expected: No output (valid YAML)

**Step 4: Commit**

```bash
git add .github/runner/docker-compose.yml .github/runner/.env.example
git commit -m "infra: add self-hosted runner Docker Compose stack

Includes GitHub Actions runner (myoung34/github-runner) and
local Docker registry (registry:2) on port 5000."
```

---

## Task 2: Create cleanup script

**Files:**
- Create: `.github/runner/cleanup.sh`

**Step 1: Create the cleanup script**

Create `.github/runner/cleanup.sh`:

```bash
#!/usr/bin/env bash
# Weekly cleanup for self-hosted runner environment
# Recommended: add to crontab
#   crontab -e
#   0 3 * * 0 /data/VarunaPoC/.github/runner/cleanup.sh >> /var/log/runner-cleanup.log 2>&1
set -euo pipefail

echo "=== Runner cleanup: $(date -Iseconds) ==="

echo "Pruning Docker images older than 7 days..."
docker image prune -af --filter "until=168h"

echo "Pruning buildx cache older than 7 days..."
docker buildx prune -af --filter "until=168h" 2>/dev/null || true

echo "Pruning unused volumes..."
docker volume prune -f

echo "Pruning unused networks..."
docker network prune -f

echo "=== Cleanup complete ==="
docker system df
```

**Step 2: Make executable**

Run: `chmod +x /data/VarunaPoC/.github/runner/cleanup.sh`

**Step 3: Commit**

```bash
git add .github/runner/cleanup.sh
git commit -m "infra: add weekly cleanup script for runner environment"
```

---

## Task 3: Update .gitignore

**Files:**
- Modify: `.gitignore:322-327` (append at end)

**Step 1: Add runner secrets entry**

The existing `.env` pattern (line 43, 242) already covers `.github/runner/.env`. Add an explicit comment for clarity, plus ignore act event payloads:

Append to `.gitignore`:

```gitignore

# Self-hosted runner secrets (covered by .env above, explicit for clarity)
.github/runner/.env

# act local testing
.actrc.local
```

**Step 2: Commit**

```bash
git add .gitignore
git commit -m "chore: add runner and act entries to .gitignore"
```

---

## Task 4: Modify ci.yml — runs-on fallback + local cache

**Files:**
- Modify: `.github/workflows/ci.yml`

This is the largest change. 9 jobs need `runs-on` updated, and 2 Docker build jobs need cache strategy changed.

**Step 1: Replace all `runs-on: ubuntu-latest` with fallback pattern**

In `ci.yml`, replace every occurrence of:
```yaml
    runs-on: ubuntu-latest
```
with:
```yaml
    runs-on: ${{ vars.USE_SELF_HOSTED == 'true' && 'self-hosted' || 'ubuntu-latest' }}
```

This affects lines: 28, 63, 106, 146, 171, 203, 244, 294, 408.

**Step 2: Replace GHA Docker cache with local cache (backend-docker job)**

In the `backend-docker` job (around line 115-124), replace:
```yaml
          cache-from: type=gha
          cache-to: type=gha,mode=max
```
with:
```yaml
          cache-from: |
            type=local,src=/tmp/.buildx-cache/backend
            type=registry,ref=localhost:5000/varuna/backend:buildcache
          cache-to: type=local,dest=/tmp/.buildx-cache-new/backend,mode=max
```

**Step 3: Add cache rotation post-step to backend-docker**

After the "Test backend container" step (around line 139), add:
```yaml
      - name: Rotate Docker build cache
        if: always()
        run: |
          rm -rf /tmp/.buildx-cache/backend
          mv /tmp/.buildx-cache-new/backend /tmp/.buildx-cache/backend 2>/dev/null || true
```

**Step 4: Replace GHA Docker cache with local cache (frontend-docker job)**

In the `frontend-docker` job (around line 220-221), replace:
```yaml
          cache-from: type=gha
          cache-to: type=gha,mode=max
```
with:
```yaml
          cache-from: |
            type=local,src=/tmp/.buildx-cache/frontend
            type=registry,ref=localhost:5000/varuna/frontend:buildcache
          cache-to: type=local,dest=/tmp/.buildx-cache-new/frontend,mode=max
```

**Step 5: Add cache rotation post-step to frontend-docker**

After the "Test frontend container" step (around line 236), add:
```yaml
      - name: Rotate Docker build cache
        if: always()
        run: |
          rm -rf /tmp/.buildx-cache/frontend
          mv /tmp/.buildx-cache-new/frontend /tmp/.buildx-cache/frontend 2>/dev/null || true
```

**Step 6: Validate YAML syntax**

Run: `python3 -c "import yaml; yaml.safe_load(open('/data/VarunaPoC/.github/workflows/ci.yml'))"`
Expected: No error

**Step 7: Test with act dry run**

Run: `cd /data/VarunaPoC && act push -n --workflows .github/workflows/ci.yml 2>&1 | head -30`
Expected: Lists jobs without errors

**Step 8: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: add self-hosted runner fallback and local Docker cache

All jobs use vars.USE_SELF_HOSTED toggle for runs-on target.
Docker builds use local cache instead of GHA cache for speed."
```

---

## Task 5: Modify cd.yml — runs-on fallback + dual push + local cache

**Files:**
- Modify: `.github/workflows/cd.yml`

**Step 1: Replace all `runs-on: ubuntu-latest` with fallback pattern**

Replace at lines: 23, 99, 191, 233.

Same pattern as Task 4:
```yaml
    runs-on: ${{ vars.USE_SELF_HOSTED == 'true' && 'self-hosted' || 'ubuntu-latest' }}
```

**Step 2: Replace GHA Docker cache with local cache (build-and-push job)**

In the `build-and-push` job (around line 77-78), replace:
```yaml
          cache-from: type=gha
          cache-to: type=gha,mode=max
```
with:
```yaml
          cache-from: |
            type=local,src=/tmp/.buildx-cache/${{ matrix.component }}
            type=registry,ref=localhost:5000/varuna/${{ matrix.component }}:buildcache
          cache-to: type=local,dest=/tmp/.buildx-cache-new/${{ matrix.component }},mode=max
```

**Step 3: Add local registry push to build-and-push job**

In the `build-and-push` job, after the "Build and push" step (around line 90), add a conditional step:
```yaml
      - name: Push to local registry
        if: vars.USE_SELF_HOSTED == 'true'
        run: |
          TAG=$(echo "${{ steps.meta.outputs.tags }}" | head -1 | sed 's|.*/||')
          docker tag ${{ steps.meta.outputs.tags }} localhost:5000/varuna/${{ matrix.component }}:${TAG} 2>/dev/null || true
          docker push localhost:5000/varuna/${{ matrix.component }}:${TAG} 2>/dev/null || true
```

**Step 4: Add cache rotation post-step**

After the local registry push step, add:
```yaml
      - name: Rotate Docker build cache
        if: always()
        run: |
          rm -rf /tmp/.buildx-cache/${{ matrix.component }}
          mv /tmp/.buildx-cache-new/${{ matrix.component }} /tmp/.buildx-cache/${{ matrix.component }} 2>/dev/null || true
```

**Step 5: Validate YAML syntax**

Run: `python3 -c "import yaml; yaml.safe_load(open('/data/VarunaPoC/.github/workflows/cd.yml'))"`
Expected: No error

**Step 6: Commit**

```bash
git add .github/workflows/cd.yml
git commit -m "cd: add self-hosted runner fallback, local cache, and dual registry push

Builds push to both GHCR and local registry (localhost:5000) when
running on self-hosted. Local Docker cache for faster rebuilds."
```

---

## Task 6: Modify security.yml — runs-on fallback + local cache

**Files:**
- Modify: `.github/workflows/security.yml`

**Step 1: Replace all `runs-on: ubuntu-latest` with fallback pattern**

Replace at lines: 34, 80, 132, 170, 227, 262, 285, 354.

Same pattern:
```yaml
    runs-on: ${{ vars.USE_SELF_HOSTED == 'true' && 'self-hosted' || 'ubuntu-latest' }}
```

**Step 2: Replace GHA Docker cache with local cache (docker-scan job)**

In the `docker-scan` job (around line 195-196), replace:
```yaml
          cache-from: type=gha
          cache-to: type=gha,mode=max
```
with:
```yaml
          cache-from: |
            type=local,src=/tmp/.buildx-cache/${{ matrix.component }}
            type=registry,ref=localhost:5000/varuna/${{ matrix.component }}:buildcache
          cache-to: type=local,dest=/tmp/.buildx-cache-new/${{ matrix.component }},mode=max
```

**Step 3: Add cache rotation post-step to docker-scan**

After the "Generate Docker image vulnerability report" step (around line 220), add:
```yaml
      - name: Rotate Docker build cache
        if: always()
        run: |
          rm -rf /tmp/.buildx-cache/${{ matrix.component }}
          mv /tmp/.buildx-cache-new/${{ matrix.component }} /tmp/.buildx-cache/${{ matrix.component }} 2>/dev/null || true
```

**Step 4: Validate YAML syntax**

Run: `python3 -c "import yaml; yaml.safe_load(open('/data/VarunaPoC/.github/workflows/security.yml'))"`
Expected: No error

**Step 5: Commit**

```bash
git add .github/workflows/security.yml
git commit -m "security: add self-hosted runner fallback and local Docker cache"
```

---

## Task 7: Setup act configuration

**Files:**
- Create: `.actrc`

**Step 1: Create .actrc**

Create `.actrc` at project root:

```
-P ubuntu-latest=catthehacker/ubuntu:act-latest
-P self-hosted=catthehacker/ubuntu:act-latest
--env CI=true
```

**Step 2: Test act installation**

Run: `act --version 2>/dev/null || echo "act not installed — install with: curl -s https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash"`

**Step 3: Test act dry run (if installed)**

Run: `cd /data/VarunaPoC && act push -n --workflows .github/workflows/ci.yml 2>&1 | head -20`
Expected: Lists all CI jobs

**Step 4: Commit**

```bash
git add .actrc
git commit -m "infra: add act configuration for local workflow testing"
```

---

## Task 8: Add email notifications on CI/CD failure

**Files:**
- Create: `.github/workflows/notify-failure.yml`

**Step 1: Create notification workflow**

Create `.github/workflows/notify-failure.yml`:

```yaml
name: CI/CD Failure Notification

on:
  workflow_run:
    workflows:
      - "CI - Continuous Integration"
      - "CD - Continuous Deployment"
      - "Security Scanning"
    types:
      - completed

permissions:
  actions: read

jobs:
  notify-on-failure:
    if: ${{ github.event.workflow_run.conclusion == 'failure' }}
    runs-on: ${{ vars.USE_SELF_HOSTED == 'true' && 'self-hosted' || 'ubuntu-latest' }}

    steps:
      - name: Send failure email notification
        uses: dawidd6/action-send-mail@v3
        with:
          server_address: smtp.gmail.com
          server_port: 587
          username: ${{ secrets.SMTP_USERNAME }}
          password: ${{ secrets.SMTP_PASSWORD }}
          subject: |
            [VarunaPoC] ${{ github.event.workflow_run.name }} FAILED — ${{ github.event.workflow_run.head_branch }}
          to: yandofotsonoeljunior@gmail.com
          from: VarunaPoC CI <${{ secrets.SMTP_USERNAME }}>
          body: |
            Workflow "${{ github.event.workflow_run.name }}" failed.

            Branch: ${{ github.event.workflow_run.head_branch }}
            Commit: ${{ github.event.workflow_run.head_sha }}
            Run: ${{ github.event.workflow_run.html_url }}

            — VarunaPoC CI/CD
```

**Step 2: Validate YAML**

Run: `python3 -c "import yaml; yaml.safe_load(open('/data/VarunaPoC/.github/workflows/notify-failure.yml'))"`
Expected: No error

**Step 3: Commit**

```bash
git add .github/workflows/notify-failure.yml
git commit -m "ci: add email notification on workflow failure

Sends email to yandofotsonoeljunior@gmail.com when CI, CD, or
Security workflows fail."
```

**Manual setup required:**
- Create a Gmail App Password at https://myaccount.google.com/apppasswords
- Add GitHub secrets: `SMTP_USERNAME` (your Gmail) and `SMTP_PASSWORD` (app password)
- Or use any other SMTP provider by changing server_address/server_port

---

## Task 9: Improve act compatibility — secrets and event payloads

**Files:**
- Create: `.github/runner/act-secrets.example`
- Create: `.github/runner/act-events/push.json`
- Create: `.github/runner/act-events/pull_request.json`
- Modify: `.actrc`

**Step 1: Create act secrets template**

Create `.github/runner/act-secrets.example`:

```bash
# act secrets file — copy to .secrets and fill in values
# Usage: act push --secret-file .github/runner/.secrets
# These mock the GitHub Actions secrets for local testing

GITHUB_TOKEN=ghp_fake_for_local_testing
CODECOV_TOKEN=fake-codecov-token
SMTP_USERNAME=fake@gmail.com
SMTP_PASSWORD=fake-password
```

**Step 2: Create push event payload**

Create `.github/runner/act-events/push.json`:

```json
{
  "ref": "refs/heads/main",
  "before": "0000000000000000000000000000000000000000",
  "after": "abc1234567890",
  "repository": {
    "full_name": "Yanstart/VarunaPoC",
    "clone_url": "https://github.com/Yanstart/VarunaPoC.git"
  },
  "head_commit": {
    "id": "abc1234567890",
    "message": "test: local act run",
    "timestamp": "2026-02-18T12:00:00Z"
  }
}
```

**Step 3: Create pull_request event payload**

Create `.github/runner/act-events/pull_request.json`:

```json
{
  "action": "opened",
  "number": 999,
  "pull_request": {
    "number": 999,
    "head": {
      "ref": "feature/test",
      "sha": "abc1234567890"
    },
    "base": {
      "ref": "main"
    }
  }
}
```

**Step 4: Update .actrc with improved defaults**

Replace `.actrc` content with:

```
-P ubuntu-latest=catthehacker/ubuntu:act-latest
-P self-hosted=catthehacker/ubuntu:act-latest
--env CI=true
--env RUNNER_OS=Linux
--env RUNNER_ARCH=X64
--secret-file .github/runner/.secrets
--container-architecture linux/amd64
```

**Step 5: Add .secrets to .gitignore**

Append to `.gitignore`:
```
.github/runner/.secrets
```

**Step 6: Commit**

```bash
git add .github/runner/act-secrets.example .github/runner/act-events/ .actrc .gitignore
git commit -m "infra: add act secrets template and event payloads

Improves act compatibility with mock secrets and pre-built
event payloads for push and pull_request events."
```

---

## Task 10: Final validation and documentation commit

**Step 1: Verify all YAML files parse correctly**

Run:
```bash
cd /data/VarunaPoC
python3 -c "
import yaml, sys
for f in ['.github/workflows/ci.yml', '.github/workflows/cd.yml', '.github/workflows/security.yml', '.github/runner/docker-compose.yml']:
    try:
        yaml.safe_load(open(f))
        print(f'OK: {f}')
    except Exception as e:
        print(f'FAIL: {f}: {e}')
        sys.exit(1)
print('All YAML valid')
"
```
Expected: All OK

**Step 2: Verify the runner stack would start (dry config check)**

Run: `cd /data/VarunaPoC/.github/runner && docker compose config --quiet`
Expected: No error

**Step 3: Verify .gitignore covers .env**

Run: `cd /data/VarunaPoC && git check-ignore .github/runner/.env`
Expected: `.github/runner/.env` (file is ignored)

**Step 4: Set GitHub repo variable**

This must be done manually by the user via GitHub UI or CLI:
```bash
# Via gh CLI (requires auth)
gh variable set USE_SELF_HOSTED --body "false" --repo Yanstart/VarunaPoC
```

Start with `false` (uses ubuntu-latest). Set to `true` after runner is up and verified.

**Step 5: Summary of manual steps after merge**

Print a checklist for the user:
1. Generate a GitHub PAT at https://github.com/settings/tokens (scope: `repo`)
2. `cd .github/runner && cp .env.example .env` and fill in the PAT
3. `docker compose up -d` to start the runner
4. Verify runner appears in GitHub Settings > Actions > Runners
5. Set `USE_SELF_HOSTED=true` in repo settings (Settings > Secrets and variables > Actions > Variables)
6. Install act: `curl -s https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash`
7. Test locally: `act push -j backend-lint --workflows .github/workflows/ci.yml`
8. Add cleanup cron: `crontab -e` → `0 3 * * 0 /data/VarunaPoC/.github/runner/cleanup.sh`
