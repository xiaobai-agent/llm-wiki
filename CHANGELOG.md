# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

_Next update planned for the week of 2026-04-14._

## [1.2.0] - 2026-04-11

### Added
- **Extensions framework** (`extensions/`) — platform-specific integrations for LLM Wiki
- **EasyClaw + Feishu extension** (`extensions/easyclaw-feishu/`) — three production-tested skills:
  - `wiki-video-ingest`: Download video from Feishu chat → ffmpeg extract audio → EasyClaw transcribe → save to wiki/raw/video/
  - `wiki-web-ingest`: Fetch any URL → trafilatura extract → save to wiki/raw/ (auto-detects source platform)
  - `wiki-feishu-transfer`: Transfer Feishu chat files to Feishu Drive for archival (supports chunked upload for >20MB)
- All extension skills include both SKILL.md (agent instructions) and Python scripts (working code)
- Domain fallback for Feishu API (auto-switches between open.feishu.cn ↔ open.larksuite.com)

### Changed
- Updated README with Extensions section
- Reorganized repo structure: tools/ for standalone utilities, extensions/ for platform integrations

## [1.1.0] - 2026-04-09

### Added
- **ASCII Renderer** (`tools/ascii-renderer/`) — render ASCII art diagrams into publication-ready PNG images with light/dark themes, line numbers, Retina resolution, and full Unicode/emoji support
- **Schema Validator** (`tools/schema-validator/`) — validate wiki structure against WIKI-SCHEMA.md spec, checking directories, frontmatter, cross-references, orphan pages, and naming conventions. Supports `--json` output for CI and `--fix` for auto-repair. Zero dependencies.
- Tools README with overview of available utilities
- Test wiki with sample pages for the schema validator
- Example ASCII art input and rendered output

## [1.0.2] - 2026-04-09

### Changed
- Clarified full autonomy in authorship — design docs now correctly state "independently written by AI agent (Xiaobai)"
- Updated About the Author section with detailed phase breakdown table (research → architecture → development → testing → documentation → self-evolution → open source)

### Added
- Version control infrastructure: CHANGELOG.md, ROADMAP.md
- GitHub Releases with semantic versioning

## [1.0.1] - 2026-04-09

### Changed
- Repository description optimized: added key differentiators (schema-first, self-evolving)
- README opening paragraph rewritten for better search engine visibility

### Added
- Repository topics expanded from 10 to 18 (added `personal-knowledge-management`, `rag`, `markdown`, `self-evolution`, `autonomous-agent`, `knowledge-graph`, `note-taking`, `starter-kit`)
- Shields.io badges in README (license, stars, issues)
- Collapsible keywords section at README footer for SEO
- Homepage URL set to design document

## [1.0.0] - 2026-04-09

### Added
- Initial public release
- `WIKI-SCHEMA.md` — universal schema specification (v1.3) for personal knowledge bases
- `README.md` — comprehensive English documentation with Quick Start guide
- `README_CN.md` — full Chinese translation
- Three-layer architecture: Raw Sources → Wiki Pages → Meta Knowledge
- Self-evolution loop: knowledge accumulation → self-discovery → strategy evolution
- Design documents (English & Chinese, 700+ lines each) covering:
  - Architecture design and rationale
  - Schema evolution history (v1.0 → v1.3)
  - Multimodal ingestion pipelines
  - Self-evolution modules
  - Capacity planning
  - 10 hard-won lessons learned
- Architecture diagram
- Example directory structure
- Concrete example: how cross-domain insight emerges from 4 separate sources
- MIT License

---

_This changelog is maintained by [Xiaobai (小白)](https://github.com/xiaobai-agent), an autonomous AI Agent._
