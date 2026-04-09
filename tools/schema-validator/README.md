# 📋 Wiki Schema Validator

Validate your LLM Wiki knowledge base against the WIKI-SCHEMA.md specification. Catches structural issues, broken links, missing frontmatter, and orphan pages.

## Quick Start

```bash
# No dependencies needed — pure Node.js!
node validate.js ./wiki
```

## Usage

```
node validate.js <wiki_directory> [options]
```

### Options

| Flag | Description |
|------|-------------|
| `--json` | Output results as JSON (for CI/automation) |
| `--fix` | Auto-fix simple issues (create missing directories and files) |
| `--strict` | Treat warnings as errors (exit code 1 on any warning) |

### Exit Codes

| Code | Meaning |
|------|---------|
| `0` | All checks passed |
| `1` | Errors found (or warnings in strict mode) |
| `2` | Invalid arguments |

## What It Checks

### ✅ Structure Validation
- Required directories exist (`raw/`, `pages/`, `meta/`)
- Required subdirectories present (`raw/articles/`, `pages/concepts/`, etc.)
- `index.md` exists
- Recommended meta files present (`ingest-strategies.md`, etc.)

### ✅ Frontmatter Validation
- Every wiki page has YAML frontmatter
- Required fields present: `title`, `type`, `created`
- Recommended fields flagged if missing: `tags`, `sources`, `related`, `updated`, `confidence`
- Valid `type` values: `concept`, `entity`, `source`, `comparison`, `insight`
- Valid `confidence` values: `high`, `medium`, `low`
- Date format check (YYYY-MM-DD)

### ✅ Cross-Reference Checks
- Links in `sources` and `related` fields point to existing files
- Broken links reported with source → target

### ✅ Health Metrics
- **Orphan pages** — pages not linked from any other page
- **Duplicate titles** — multiple pages with the same title
- **Raw file naming** — checks YYYY-MM-DD-title.md convention
- **Index coverage** — pages not listed in index.md

### ✅ Statistics
- Total pages and raw sources
- Breakdown by page type and confidence level

## Example Output

```
╔══════════════════════════════════════════╗
║     📋 LLM Wiki Validation Report       ║
╚══════════════════════════════════════════╝

  Wiki directory: /path/to/wiki

  📊 Statistics
     Pages: 12
     Raw sources: 8
     By type:
       concept: 5
       entity: 3
       source: 4
     By confidence:
       high: 7
       medium: 4
       low: 1

  ⚠️  Warnings (2)
     • Missing recommended frontmatter field: tags [pages/concepts/ai-safety.md]
     • 1 orphan page(s) found (not linked from any other page)

  🔗 Orphan pages (not linked from any other page)
     • pages/entities/old-company.md

  ✅ All checks passed!
```

## JSON Output

```bash
node validate.js ./wiki --json
```

```json
{
  "passed": true,
  "wikiDir": "/path/to/wiki",
  "errors": [],
  "warnings": [...],
  "stats": {
    "totalPages": 12,
    "totalRawFiles": 8,
    "pagesByType": { "concept": 5, "entity": 3, "source": 4 },
    "orphanPages": ["pages/entities/old-company.md"]
  }
}
```

## Auto-Fix Mode

```bash
node validate.js ./wiki --fix
```

Creates missing directories and files automatically:
- Missing `raw/`, `pages/`, `meta/` subdirectories
- Missing `index.md` (with template content)

## CI Integration

```yaml
# GitHub Actions example
- name: Validate Wiki
  run: node tools/schema-validator/validate.js ./wiki --strict --json
```

## Dependencies

None — pure Node.js (≥ 12). No npm install needed.

## License

MIT
