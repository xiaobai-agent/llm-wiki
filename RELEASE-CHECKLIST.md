# 📋 Release Checklist

> Run through this checklist **every time** before pushing a release.
> Copy the checklist into your commit message or PR description to track completion.

---

## Pre-Release Checklist

### 1. Content Sync (Bilingual)

- [ ] **README.md** (EN) — updated with new features/data/sections
- [ ] **README_CN.md** (CN) — **fully synced** with English version
  - [ ] Same sections, same order
  - [ ] Same data/numbers (page counts, source counts, etc.)
  - [ ] Same badges and links
  - [ ] New sections translated
- [ ] **docs/design-document.md** (EN) — updated if architecture changed
- [ ] **docs/design-document-zh.md** (CN) — **fully synced** with English version

### 2. Version Tracking

- [ ] **CHANGELOG.md** — new entry added with:
  - [ ] Version number (semver: MAJOR.MINOR.PATCH)
  - [ ] Date
  - [ ] Added / Changed / Fixed / Removed sections
- [ ] **ROADMAP.md** — completed items checked off, new items added
- [ ] **docs/devlog.md** — weekly entry appended

### 3. Schema & Data

- [ ] **WIKI-SCHEMA.md** — version bumped if schema rules changed
- [ ] **wiki/** seed content — updated if schema structure changed
- [ ] **examples/** — updated if usage patterns changed

### 4. Tools

- [ ] **tools/ascii-renderer/** — README updated if features added
- [ ] **tools/schema-validator/** — README updated if checks added
- [ ] Tool READMEs consistent with root README descriptions

### 5. Git & GitHub Release

- [ ] Git tag created: `git tag -a vX.Y.Z -m "description"`
- [ ] Git tag pushed: `git push origin vX.Y.Z`
- [ ] **GitHub Release created** from the tag:
  - [ ] Go to: https://github.com/xiaobai-agent/llm-wiki/releases/new
  - [ ] Choose tag: vX.Y.Z
  - [ ] Title: `vX.Y.Z — <short description>`
  - [ ] Description: Copy from CHANGELOG.md (the new version's section)
  - [ ] Click "Publish release"

### 6. Meta

- [ ] **Profile README** (xiaobai-agent/xiaobai-agent) — synced if project description changed

---

## Version Numbering Guide

| Change Type | Bump | Example |
|-------------|------|---------|
| New tools, major features | MINOR | v1.0 → v1.1 |
| Doc updates, bug fixes, tweaks | PATCH | v1.1.0 → v1.1.1 |
| Breaking schema changes | MAJOR | v1.x → v2.0 |

---

## Quick Sync Commands

```bash
# Check what files changed since last tag
git diff --name-only $(git describe --tags --abbrev=0) HEAD

# List all files that need bilingual sync
echo "Check these pairs:"
echo "  README.md ↔ README_CN.md"
echo "  docs/design-document.md ↔ docs/design-document-zh.md"
```

---

## Post-Release

- [ ] Verify on GitHub: README renders correctly
- [ ] Verify: Chinese README matches English
- [ ] Verify: GitHub Release page shows correct version and notes
- [ ] Update Profile README if needed
- [ ] Record release in devlog.md

---

## Why This Exists

On 2026-04-09, we discovered that README_CN.md was missing 10+ sections that existed in the English version. Nobody noticed until a human eyeballed it. This checklist ensures bilingual parity is never silently broken again.

**Rule: If you change one language, you change both. No exceptions.**
