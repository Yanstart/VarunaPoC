# Self-Hosted CI/CD Pipeline — Design Document

**Date**: 2026-02-18
**Status**: Approved
**Scope**: GitHub self-hosted runners + act local testing for VarunaPoC

## Context

VarunaPoC uses GitHub Actions (3 workflows: CI, CD, Security) running on `ubuntu-latest`.
Goals: reduce costs, improve speed, keep medical data local, learn infra, prepare for future Gitea/Forgejo migration.

## Decision

**Approach 3: Dockerized self-hosted runner + act CLI**

- Keep GitHub as the git forge
- Run a containerized GitHub Actions runner on a local Linux machine (16+ GB RAM)
- Add a local Docker registry for image caching
- Install `act` for local workflow testing

## Architecture

```
Local Linux Machine (16+ GB RAM)
├── Docker Compose (runner stack)
│   ├── github-runner (myoung34/github-runner)
│   │   └── /var/run/docker.sock mounted
│   └── registry (registry:2, port 5000)
├── act CLI (installed on host)
└── HTTPS polling → github.com/Yanstart/VarunaPoC
```

## File Structure

```
.github/
├── workflows/
│   ├── ci.yml              # Modified: runs-on self-hosted, local cache
│   ├── cd.yml              # Modified: dual push GHCR + local registry
│   └── security.yml        # Modified: runs-on self-hosted
└── runner/
    ├── docker-compose.yml  # Runner + registry stack
    ├── .env.example        # Template (REPO_URL, ACCESS_TOKEN, RUNNER_NAME)
    ├── .env                # (gitignored) actual secrets
    └── cleanup.sh          # Weekly cron: prune images/cache/volumes
.actrc                      # act default config
```

## Workflow Modifications

### runs-on with fallback

All jobs use a repository variable for toggling:

```yaml
runs-on: ${{ vars.USE_SELF_HOSTED == 'true' && 'self-hosted' || 'ubuntu-latest' }}
```

When `USE_SELF_HOSTED=true` in repo settings → self-hosted runner.
When `false` or machine offline → falls back to GitHub-hosted.

### Docker cache strategy

```yaml
# Replace GHA cache with local cache (10-100x faster on self-hosted)
cache-from: type=local,src=/tmp/.buildx-cache
cache-to: type=local,dest=/tmp/.buildx-cache-new,mode=max
```

Post-step to rotate cache and prevent unbounded growth.

### CD dual push

```yaml
tags: |
  ghcr.io/yanstart/varunapoc/${{ matrix.component }}:$TAG
  localhost:5000/varuna/${{ matrix.component }}:$TAG
```

## act Configuration

`.actrc`:
```
-P ubuntu-latest=catthehacker/ubuntu:act-latest
-P self-hosted=catthehacker/ubuntu:act-latest
--env CI=true
```

Usage:
```bash
act push -j backend-lint                          # Single job
act push --workflows .github/workflows/ci.yml     # Full CI
act -l                                            # List jobs
act push -n                                       # Dry run
```

Limitations: `actions/cache` partial, no Codecov/CodeQL/Gitleaks upload, no `GITHUB_TOKEN` auto.

## Security

- Docker socket mounted: runner processes only this repo's jobs (repo-level, not org-level)
- PAT stored in `.env` (gitignored), scope `repo` only, rotate every 90 days
- No inbound ports needed (HTTPS polling only)
- Job isolation via Docker containers

## Maintenance

- **Cleanup cron** (weekly): prune images >7 days, buildx cache, orphan volumes
- **Updates**: `docker compose pull && docker compose up -d`
- **Auto-restart**: `restart: unless-stopped` on all containers
- **Log rotation**: Docker daemon log driver with max-size

## Future

This setup prepares for eventual migration to Gitea/Forgejo + Woodpecker CI on a dedicated server.
Docker Compose orchestration skills are directly transferable.
