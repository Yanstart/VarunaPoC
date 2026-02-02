# Quick- Repository Restructure Archive

**Date**: 2026-02-02
**Reason**: Cleanup and focus on production-ready implementations

## Archived Content

### 1. scripts-legacy/
**Source**: `deployments/scripts/`
**Reason**: Benchmark and validation scripts replaced by newer interactive demo scripts.

Contains:
- `benchmark-*.sh/ps1` - Old benchmark scripts
- `run-*.sh` - Batch validation scripts
- `test-phase1.sh`, `test-protocols.ps1` - Phase 1 test scripts
- `load-test.ps1`, `satellite-test.ps1` - Specialized test scripts
- `build-all.sh`, `start-demo.sh` - Superseded by `quick-demo.ps1`

### 2. quic-go-impl-archive/
**Source**: `Archives/quic-go-implementation/`
**Reason**: Old quic-go implementation archived when project pivoted to native implementations.

Contains:
- Full Go implementation (cmd/, internal/, configs/)
- Docker deployments
- Old Go module files

### 3. specs-archives/
**Source**: `docs/Specifications_Archives/`
**Reason**: Old specification versions (v1, v2) replaced by v2.0.

Contains:
- `CDC.md` - Original Cahier des Charges
- `CDC_v1_ARCHIVE.md` - Version 1 (archived)
- `CDC_v2_ARCHIVE.md` - Version 2 (archived)

## What Was Deleted (Not Archived)

- `docker-build*.log` - Build logs (temporary debugging files)
- `tmpclaude*.cwd` - Claude Code session files
- `nul` - Windows null file artifact
- `node_modules/`, `package.json` - Unused Node.js dependencies
- `Dockerfile.entry`, `Dockerfile.exit`, etc. - Root Dockerfiles superseded by `deployments/docker/`

## Active Repository Structure

After cleanup, Quick-/ contains only essential code:
```
Quick-/
├── native/           # 4 implementations (quiche-cloudflare, quiche-google, msquic)
├── internal/         # quic-go reference implementation
├── deployments/      # Docker, scripts, configs
├── docs/             # quiche-Cloudflare & quiche-Google docs
├── .claude/          # Orchestration brain
├── cmd/              # Go binaries
├── Rapport/          # Thesis deliverables
└── README.md
```

## Recovery

To restore archived files:
```bash
# From git (tracked files only)
git checkout HEAD -- Archives/
git checkout HEAD -- docs/Specifications_Archives/

# From this archive
cp -r /path/to/Archives/Quick-restructure/* /path/to/Quick-/
```
