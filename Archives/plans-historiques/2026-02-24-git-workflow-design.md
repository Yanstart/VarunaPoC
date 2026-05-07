# Git Workflow Design - VarunaPoC

**Date**: 2026-02-24
**Status**: Implemented

## Context

- Private repo, single active developer
- Milestone-based development (M0-M4)
- Self-hosted CI runners (4 replicas)
- GitHub Issues + PRs
- Previously had a dead `develop` branch (deleted)

## Decision: Trunk-Based Development

### Why not GitFlow?
Overkill for single-dev. `develop`/`release` branches add ceremony without value.

### Why not pure GitHub Flow?
Too informal for a medical imaging project requiring traceability.

### Chosen: Trunk-Based with Tags
- `main` = only permanent branch, always deployable
- Short-lived feature/fix branches via PRs
- Semver tags per milestone completion
- Branch protection enforces CI-before-merge

## Implementation

1. **CONTRIBUTING.md** — full workflow documentation
2. **CI updated** — removed dead `develop` trigger
3. **Branch protection** — PRs required, CI required, no force-push
4. **Auto-delete** — branches removed after merge
5. **Tag convention** — `v0.{milestone}.{patch}`
