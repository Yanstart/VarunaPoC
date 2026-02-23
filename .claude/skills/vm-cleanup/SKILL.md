---
name: vm-cleanup
description: This skill should be used when the user asks to "clean up", "free disk space", "clean the VM", "liberer de la memoire", "nettoyer", or when disk usage exceeds 80%. Also trigger proactively after heavy build/test sessions that generate large artifacts.
allowed-tools: Bash, Read, Glob
---

# VM Cleanup Skill

Clean up disk space on the development VM by removing build artifacts, caches, stale containers, and temporary files related to the VarunaPoC project. Designed for the self-hosted runner environment.

## When to Trigger

- User explicitly asks for cleanup
- Disk usage on `/` exceeds 80% (check with `df -h /`)
- After heavy Docker build sessions
- After running E2E test suites (Playwright generates large artifacts)
- After multiple `cargo build` cycles (target dirs grow fast)

## Cleanup Procedure

### Phase 1: Assess

Run the diagnostic script to see current disk state before taking action:

```bash
bash .claude/skills/vm-cleanup/scripts/disk-report.sh
```

Present the report to the user. Only proceed with cleanup if disk usage warrants it or if the user explicitly requested it.

### Phase 2: Safe Cleanup (always safe to run)

These operations never break anything:

1. **Python caches**: `find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null`
2. **Pytest/Ruff caches**: `rm -rf .pytest_cache .ruff_cache`
3. **Temp files**: `rm -f /tmp/security-scan-log.txt /tmp/pr*-logs.txt`
4. **Old logs**: `find /var/log -name "*.gz" -o -name "*.old" -o -name "*.[0-9]" | xargs rm -f 2>/dev/null`
5. **Pip cache**: `rm -rf /root/.cache/pip`
6. **npm cache**: `npm cache clean --force 2>/dev/null`
7. **Playwright artifacts**: `rm -rf frontend/test-results frontend/e2e/test-results frontend/e2e/playwright-report`
8. **Build outputs**: `rm -rf frontend/dist`

### Phase 3: Medium Impact (ask user first)

These free significant space but may require rebuild time:

1. **Docker prune**: `docker system prune -f` (removes stopped containers, dangling images)
2. **Cargo target clean**: `cd native/quiche-cloudflare && cargo clean` (can be several GB)
3. **Node modules**: `rm -rf frontend/node_modules` (requires `npm ci` to restore)

### Phase 4: High Impact (always ask user first)

These free the most space but have significant rebuild cost:

1. **Docker full prune**: `docker system prune -a -f --volumes` (removes ALL unused images/volumes)
2. **Python venvs**: `rm -rf backend/venv backend/.venv` (requires `pip install -r requirements.txt`)
3. **Rust toolchain cache**: `rm -rf /root/.cargo/registry/cache` (re-downloads on next build)

## Post-Cleanup

After cleanup, run the diagnostic script again to confirm space was freed:

```bash
bash .claude/skills/vm-cleanup/scripts/disk-report.sh
```

Report the before/after comparison to the user.

## Important Notes

- Never delete `Slides/` directory (60+ GB of medical imaging data)
- Never delete `.claude/` tracked files (project memory/config)
- Never delete `backend/data/` (SQLite databases, uploaded files)
- The `backend/venv` and `backend/.venv` are gitignored and can always be recreated
- Docker images can always be rebuilt from Dockerfiles
