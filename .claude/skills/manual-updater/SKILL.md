---
name: manual-updater
description: Update user manual in /docs/Manuel/ following the Manual Update Protocol when features are validated and ready for end users. Creates or updates documentation with user-friendly language.
allowed-tools: Read, Write, Edit, Glob
---

# Manual Updater Skill

This skill automates the creation and updating of user-facing documentation in `/docs/Manuel/` following the **Manual Update Protocol** defined in `CLAUDE.md`.

## When to Use This Skill

Invoke this skill ONLY when a feature meets ALL these criteria:

- ✅ Feature is **validated and tested** (not in development)
- ✅ Feature is **accessible to end users** (UI complete)
- ✅ A **complete user workflow** is implemented
- ✅ UI is **finalized** (no placeholders or "Coming soon")

**Do NOT use for:**
- ❌ Features in development (incomplete)
- ❌ Technical implementation details (that's for README.md)
- ❌ Code documentation (use docstrings)

## What This Skill Does

1. **Determines document type** (new feature vs update existing)
2. **Assigns document number** (01-99 based on category)
3. **Creates or updates** manual document with user-friendly content
4. **Updates `/docs/Manuel/README.md`** with new entry
5. **Updates FAQ** if needed (`99-FAQ.md`)
6. **Ensures consistency** across all manual documents

## Document Structure

### Directory Organization

```
docs/Manuel/
├── README.md                      ← Index and overview
├── 01-INTRODUCTION.md             ← Getting started
├── 02-NAVIGATION_DOSSIERS.md      ← File browser
├── 03-ORGANISATION_LAMES.md       ← File organization rules
├── 04-FORMATS_SUPPORTES.md        ← Supported formats
├── 05-VISUALISATION_LAMES.md      ← Slide viewer usage
├── [06-89] Future features
├── [90-98] Administration
└── 99-FAQ.md                      ← Frequently asked questions
```

### Numbering Convention

| Range | Category |
|-------|----------|
| **01-09** | Core features (Introduction, Navigation, etc.) |
| **10-89** | Advanced features (Annotations, Measurements, Export) |
| **90-98** | Administration and configuration |
| **99** | FAQ (always last) |

**Examples:**
- `01-INTRODUCTION.md` - Getting started
- `02-NAVIGATION_DOSSIERS.md` - File browser
- `15-ANNOTATIONS.md` - Annotation tools (future)
- `20-MESURES_DISTANCES.md` - Distance measurements (future)
- `99-FAQ.md` - FAQ

## Document Template

Every manual document follows this structure:

```markdown
# [Feature Title]

**Statut:** ✅ Validé et prêt à l'emploi
**Dernière mise à jour:** YYYY-MM-DD
**Fonctionnalité:** [Brief description]

---

## Vue d'Ensemble
[Introduction: What is this feature and why does it exist?]

## [Section 1: Main Concept]
[Explanation of the core concept]

## [Section 2: How to Use]
[Step-by-step user guide]

### Étape 1: [Action]
[Detailed explanation with screenshots (future)]

### Étape 2: [Action]
[...]

## [Section 3: Use Cases]
[2-3 practical examples with real scenarios]

### Example 1: [Scenario]
[Step-by-step walkthrough]

### Example 2: [Scenario]
[...]

## Dépannage
[Common problems and solutions]

### Problème: [Description]
**Solution:** [Step-by-step fix]

### Problème: [Description]
**Solution:** [...]

## Conseils et Astuces
💡 [Helpful tips for power users]

## Prochaines Étapes
[Links to related manual documents]

- Voir aussi: [Related Document](./XX-RELATED.md)

---

**Version:** X.Y
**Dernière révision:** YYYY-MM-DD
**Auteur:** Équipe VarunaPoC
```

## Content Guidelines

### User-Friendly Language

❌ **Technical language (AVOID):**
```markdown
The `/api/slides/browse` endpoint uses `format_detector.py` to scan
the filesystem recursively and identify slides via OpenSlide detection.
```

✅ **User-friendly language (GOOD):**
```markdown
Lorsque vous ouvrez un dossier, VarunaPoC détecte automatiquement toutes
les lames histologiques présentes et affiche leurs aperçus.
```

### Required Elements

Every document MUST include:

- ✅ Clear, concise introduction (Vue d'Ensemble)
- ✅ Step-by-step usage instructions
- ✅ At least 2-3 practical use cases
- ✅ Troubleshooting section (common problems)
- ✅ Tips and tricks (💡)
- ✅ Links to related documents
- ✅ Version number and date

### Elements to AVOID

- ❌ Code snippets (unless absolutely necessary for users)
- ❌ Technical implementation details
- ❌ Unexplained jargon
- ❌ Too much text without structure
- ❌ Outdated information (always update dates)

## Status Indicators

Use these status indicators at the top of each document:

- ✅ **Validé et prêt à l'emploi** - Complete and tested feature
- ⚠️ **Fonctionnalité partielle** - Known limitations
- 🔄 **En développement** - Pre-documentation (rare, special cases only)

## Workflow

### Step 1: Determine Document Type

**New feature:**
```
If feature doesn't have a manual document yet:
  → Create new file with next available number
  → Use full document template
```

**Existing feature update:**
```
If feature already has a manual document:
  → Update relevant sections
  → Increment version number (e.g., 1.2 → 1.3)
  → Add to version history
```

### Step 2: Assign Number

Based on feature category:
- Core feature (navigation, viewing) → 01-09
- Advanced feature (annotations, export) → 10-89
- Administration (config, setup) → 90-98

### Step 3: Write Content

Follow the document template with:
- Clear section headings
- User-friendly language
- Practical examples
- Screenshots (future Phase 2+)
- Troubleshooting
- Tips and tricks

### Step 4: Update README.md

Add entry to `/docs/Manuel/README.md`:

```markdown
### 📚 Documents Disponibles

1. **[01-INTRODUCTION.md](./01-INTRODUCTION.md)**
   Présentation générale, prérequis système, premiers pas

2. **[NEW_DOCUMENT.md](./NEW_DOCUMENT.md)**  ← ADD HERE
   [Brief description of the new feature]

...
```

### Step 5: Update FAQ (if needed)

If the feature introduces common questions, add them to `99-FAQ.md`:

```markdown
## [Category]

### Q: [User question about new feature]
**R:** [Clear, concise answer with link to relevant manual doc]

Voir aussi: [XX-FEATURE_NAME.md](./XX-FEATURE_NAME.md)
```

## Example Usage

**Scenario:** Navigation feature is complete and tested. You need to document it for users.

**Skill invocation:**
```
The file browser feature is complete:
- Users can navigate folders hierarchically
- Slides are displayed as thumbnail cards
- Search functionality works
- Tested with all supported formats

Need to create user manual documentation.
```

**Skill output:**
1. Creates `/docs/Manuel/02-NAVIGATION_DOSSIERS.md`
2. Sections include:
   - Vue d'Ensemble (concept of hierarchical navigation)
   - Naviguer dans les Dossiers (click, breadcrumb, back)
   - Affichage du Contenu (cards, info, status)
   - Recherche de Lames (search bar usage)
   - Ouvrir une Lame (complete workflow)
   - Organisation Recommandée (best practices)
   - Dépannage (common issues)
3. Updates `/docs/Manuel/README.md` with entry
4. Updates `99-FAQ.md` with navigation questions

## Versioning

**Document versions:**

```markdown
**Version:** 1.2
**Dernière révision:** 2025-10-21

**Historique:**
- v1.2 (2025-10-21): Ajout section "Recherche avancée"
- v1.1 (2025-10-15): Correction erreur dans exemple
- v1.0 (2025-10-10): Version initiale
```

**When to increment:**
- **Major (1.0 → 2.0):** Complete rewrite or major feature change
- **Minor (1.0 → 1.1):** New section added
- **Patch (1.0.0 → 1.0.1):** Typo fixes, small clarifications

## Quality Checklist

Before considering a manual document complete:

- [ ] Language is user-friendly (no technical jargon)
- [ ] At least 3 practical use cases included
- [ ] Troubleshooting section has at least 2 common problems
- [ ] Links to related documents are correct
- [ ] Numbering and naming follow conventions
- [ ] README.md is updated with entry
- [ ] Version and date are current
- [ ] Status indicator is appropriate (✅/⚠️/🔄)

## Integration with Other Skills

This skill works well with:
- **api-documenter** - Technical API docs for developers (separate from user manual)
- **slide-tester** - Validate features work before documenting for users

## References

- **Manual Update Protocol:** See `CLAUDE.md` section "Manual Update Protocol"
- **Manual Index:** `/docs/Manuel/README.md`
- **Document Template:** See above "Document Template" section
- **Existing Manuals:** `/docs/Manuel/*.md`

---

**Remember:** User manual is for end users (pathologists, technicians), not developers. Use clear, jargon-free language and focus on "how to" rather than "how it works technically."
