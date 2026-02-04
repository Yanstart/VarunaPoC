---
name: error-documenter
description: Automatically document non-trivial errors following the Error Documentation Protocol from CLAUDE.md. Use when encountering errors that require research, workarounds, or could recur.
allowed-tools: Read, Write, Edit, Glob, WebFetch
---

# Error Documenter Skill

This skill automates the creation of comprehensive error documentation following the **Error Documentation Protocol** defined in `CLAUDE.md`.

## When to Use This Skill

Invoke this skill when you encounter an error that meets ANY of these criteria:

- ✅ Error persists after initial debugging attempts
- ✅ Requires research (GitHub issues, forums, documentation deep-dive)
- ✅ Related to external library limitation or bug
- ✅ Solution requires a workaround rather than straightforward fix
- ✅ Could recur with other files/scenarios

## What This Skill Does

1. **Creates error documentation file** in `/docs/ERROR_[NAME].md`
2. **Fills all mandatory sections** from `ERROR_TEMPLATE.md`
3. **Adds entry to `/docs/README.md`** for error tracking
4. **Generates code comment** linking to the error doc
5. **Suggests implementation** of workaround with documentation

## Workflow

### Step 1: Read ERROR_TEMPLATE.md

```bash
# The skill will read this file to get the structure
/docs/ERROR_TEMPLATE.md
```

### Step 2: Gather Information

The skill will ask you (or gather from context):

- **Error name** (descriptive, e.g., `BIF_DIRECTION_LEFT`)
- **Component affected** (e.g., OpenSlide, FastAPI, frontend)
- **Error message** (full traceback or browser error)
- **Files involved** (which code files triggered the error)
- **What you tried** (debugging steps, research links)
- **Root cause** (technical analysis)
- **Solution implemented** (or proposed)

### Step 3: Create Documentation

Creates `/docs/ERROR_[COMPONENT]_[SHORT_DESCRIPTION].md` with:

**Mandatory sections:**
1. **Métadonnées** (Date, composant, sévérité, statut)
2. **Description du Problème** (Quoi, où, quand)
3. **Analyse Technique** (Pourquoi, comment - root cause)
4. **Recherches Effectuées** (Tests, searches, attempts)
5. **Solutions Envisagées** (All options, even rejected)
6. **Solution Implémentée** (What was actually done)
7. **Tests de Reproduction** (Script to reproduce)
8. **Références Externes** (GitHub issues, docs, forums)
9. **Prévention Future** (How to avoid this)
10. **Historique** (Updates and resolution timeline)

### Step 4: Update Error Index

Adds entry to `/docs/README.md`:

```markdown
### [ERROR_COMPONENT_DESCRIPTION](./ERROR_COMPONENT_DESCRIPTION.md)
**Status:** 🔴 Open / 🟡 Workaround / 🟢 Resolved
**Date:** YYYY-MM-DD
**Component:** [Backend/Frontend/OpenSlide/etc.]
Brief one-line description of the error.
```

### Step 5: Generate Code Comment

Provides you with a code comment template to add where the workaround is implemented:

```python
# Workaround for docs/ERROR_[NAME].md
# [Brief explanation of why workaround is needed]
# See full analysis in documentation
```

## Example Usage

**Scenario:** You encounter an OpenSlide error when opening a Ventana BIF file with `direction="LEFT"` attribute.

**Skill invocation:**
```
I'm getting an OpenSlide error when opening BIF files:
"OpenSlideError: Bad direction attribute: LEFT"

The file works with Ventana's viewer but not OpenSlide.
I've found a GitHub issue suggesting it's unsupported.
```

**Skill output:**
1. Creates `/docs/ERROR_BIF_DIRECTION_LEFT.md` with full analysis
2. Updates `/docs/README.md` with entry
3. Provides code comment:
   ```python
   # Workaround for docs/ERROR_BIF_DIRECTION_LEFT.md
   # OpenSlide does not support direction="LEFT" in Ventana BIF files
   # This is a known limitation (GitHub openslide/openslide#123)
   try:
       slide = openslide.OpenSlide(path)
   except openslide.OpenSlideError as e:
       if "Bad direction attribute" in str(e):
           return {"is_supported": False, "notes": "BIF LEFT direction unsupported"}
       raise
   ```

## Critical Rules

### NO EMOJIS IN PYTHON LOGS

**NEVER** use emojis in Python code (causes UnicodeEncodeError on Windows):

❌ **BAD:**
```python
print("✅ SUCCESS: File opened")
print(f"❌ FAILED: {error}")
```

✅ **GOOD:**
```python
print("SUCCESS: File opened")
print(f"FAILED: {error}")
# Or use ASCII: [OK], [FAIL], [WARN]
```

### Documentation Quality Standards

Every error doc must include:
- [ ] Clear, concise problem description
- [ ] Full technical analysis (root cause)
- [ ] All research links (GitHub issues, docs, forums)
- [ ] Reproduction steps (script or command)
- [ ] Solution with code examples
- [ ] Prevention recommendations

### Naming Convention

```
ERROR_[COMPONENT]_[SHORT_DESCRIPTION].md
```

**Examples:**
- `ERROR_BIF_DIRECTION_LEFT.md`
- `ERROR_OPENSLIDE_JPEG_CORRUPTION.md`
- `ERROR_CORS_LOCALHOST_BLOCKED.md`
- `ERROR_FASTAPI_TILE_TIMEOUT.md`

## Template Sections (From ERROR_TEMPLATE.md)

When creating a new error document, use this structure:

```markdown
# ERROR: [Descriptive Title]

## Métadonnées
**Date de Découverte:** YYYY-MM-DD
**Composant Affecté:** [Backend/Frontend/OpenSlide/etc.]
**Sévérité:** [Critique/Haute/Moyenne/Basse]
**Statut:** [🔴 Open / 🟡 Workaround / 🟢 Resolved]
**Version:** [OpenSlide/FastAPI/etc. version]

---

## Description du Problème

### Quoi
[Clear description of the error]

### Où
[Which files/components/endpoints]

### Quand
[Under what conditions does it occur]

---

## Analyse Technique

### Pourquoi (Root Cause)
[Deep technical analysis]

### Comment (Mechanism)
[How the error manifests]

---

## Recherches Effectuées

### Tests Réalisés
1. [Test 1]
2. [Test 2]
...

### Recherches Externes
- GitHub Issues: [links]
- Documentation: [links]
- Forums/StackOverflow: [links]

---

## Solutions Envisagées

### Option 1: [Description]
**Pros:** ...
**Cons:** ...
**Decision:** ✅ Chosen / ❌ Rejected

### Option 2: [Description]
...

---

## Solution Implémentée

### Code
```python
# Implementation with comments
```

### Fichiers Modifiés
- `backend/services/file.py:123`
- `backend/routes/slides.py:45`

---

## Tests de Reproduction

### Script
```bash
# Script to reproduce the error
```

### Résultats Attendus
[What should happen]

### Résultats Réels
[What actually happens]

---

## Prévention Future

### Détection Précoce
[How to catch this earlier]

### Recommandations
1. [Recommendation 1]
2. [Recommendation 2]

---

## Références Externes

1. [GitHub Issue #123](https://github.com/...)
2. [OpenSlide Docs](https://openslide.org/...)
3. [Forum Thread](https://forum.example.com/...)

---

## Historique

- **YYYY-MM-DD:** Erreur découverte
- **YYYY-MM-DD:** Workaround implémenté
- **YYYY-MM-DD:** [Future updates]
```

## Integration with Other Skills

This skill works well with:
- **api-documenter** - Document API changes made as workarounds
- **slide-tester** - Test workarounds with all slide formats

## References

- **Error Documentation Protocol:** See `CLAUDE.md` section "Error Documentation Protocol"
- **ERROR_TEMPLATE.md:** `/docs/ERROR_TEMPLATE.md`
- **Error Index:** `/docs/README.md`
- **Existing Error Docs:** `/docs/ERROR_*.md`

---

**Remember:** Every non-trivial error is a learning opportunity. Comprehensive documentation prevents repeating the same debugging work and helps future maintainers.
