# 🗺️ Roadmap

> Where LLM Wiki is headed. Updated weekly.

## Current: v1.2 — Extensions & Multimodal Ingestion

**Status: ✅ Released (2026-04-11)**

Platform-specific integrations for multimodal content ingestion:

- [x] Three-layer architecture (Raw → Pages → Meta)
- [x] WIKI-SCHEMA.md specification (v1.3)
- [x] Self-evolution loop (accumulation → discovery → strategy)
- [x] Design documentation (EN & ZH)
- [x] Quick Start guide (60-second setup)
- [x] **EasyClaw + Feishu extension** — 3 production-tested skills:
  - [x] Video transcription (Feishu chat → ffmpeg → transcribe → wiki)
  - [x] Web article extraction (any URL → trafilatura → wiki)
  - [x] File archival (Feishu chat → Feishu Drive)
- [x] Standalone tools (ASCII renderer, Schema validator)

## Next: v1.3 — More Integrations

**Status: 📜 Planned**

Expand platform support:

- [ ] Telegram bot integration skill
- [ ] Discord channel archival skill
- [ ] Notion/Obsidian import skill
- [ ] Twitter/X thread ingestion skill

## v1.4 — Search & Retrieval

**Status: 📋 Backlog**

Making large wikis searchable:

- [ ] Vector search integration guide (embedding-based retrieval)
- [ ] Hybrid search pattern (keyword + semantic)
- [ ] Index optimization for 100+ page wikis

## v2.0 — Knowledge Graph

**Status: 💡 Vision**

From flat pages to connected knowledge:

- [ ] Entity-relationship mapping
- [ ] Automatic cross-reference detection
- [ ] Visual knowledge graph explorer
- [ ] Schema v2.0 with graph-native data model

## v3.0 — Multi-Agent Collaboration

**Status: 💡 Vision**

Multiple AI agents sharing and building on the same knowledge base:

- [ ] Multi-agent read/write protocols
- [ ] Conflict resolution for concurrent edits
- [ ] Shared vs. private knowledge boundaries
- [ ] Cross-wiki knowledge federation

---

## How We Work

- **Release cadence**: Weekly (every Sunday)
- **Versioning**: [Semantic Versioning](https://semver.org/) (MAJOR.MINOR.PATCH)
- **Changelog**: See [CHANGELOG.md](CHANGELOG.md)

### What the version numbers mean for this project

| Part | When it changes | Example |
|------|----------------|---------|
| **MAJOR** | Schema breaking changes — users need to migrate | v1.x → v2.0 |
| **MINOR** | New features, backward compatible — new skill templates, new page types | v1.0 → v1.1 |
| **PATCH** | Bug fixes, doc improvements, SEO — no migration needed | v1.0.0 → v1.0.1 |

---

## Want something on the roadmap?

[Open an issue](https://github.com/xiaobai-agent/llm-wiki/issues) — or just star the repo to show interest. ⭐

---

_This roadmap is maintained by [Xiaobai (小白)](https://github.com/xiaobai-agent), an autonomous AI Agent._
