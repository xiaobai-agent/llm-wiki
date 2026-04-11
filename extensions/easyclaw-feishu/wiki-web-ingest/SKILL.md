---
name: wiki-web-ingest
description: |
  Fetch web articles → Extract content as Markdown → Save to wiki/raw/ directory.
  Trigger keywords: "fetch this article", "web ingest", "save this link to wiki".
  This skill only handles the "heavy lifting" (fetch → extract → save). Knowledge extraction is done by the LLM.
---

# Web Article Ingest (wiki-web-ingest)

Fetch web articles as Markdown and save to `wiki/raw/`. **Zero cost, 3-5 seconds.**

## Prerequisites

- **Python 3** + `requests`
- `trafilatura` (auto-installed on first run)

## Usage

### Step 1: Determine output directory by URL domain

Map URL domain to raw subdirectory:

| URL Domain | Source | raw Subdirectory |
|------------|--------|------------------|
| `mp.weixin.qq.com` | WeChat | `wiki/raw/wechat/` |
| `view.inews.qq.com` / `new.qq.com` | Tencent News | `wiki/raw/news/` |
| `www.xiaohongshu.com` | Xiaohongshu | `wiki/raw/xiaohongshu/` |
| `36kr.com` / `juejin.cn` / `zhuanlan.zhihu.com` | Tech/News | `wiki/raw/news/` |
| Others | Other | `wiki/raw/other/` |

### Step 2: Run the script

```bash
python wiki_web_ingest.py "https://example.com/article" \
  --output-dir "/absolute/path/to/wiki/raw/news"
```

**Parameters:**

| Parameter | Required | Description | Example |
|-----------|----------|-------------|---------|
| `url` | ✅ | Web page URL | `"https://mp.weixin.qq.com/s/xxx"` |
| `--output-dir` | ✅ | Output directory (absolute path) | `"/home/user/wiki/raw/wechat"` |
| `--source` | ❌ | Source platform (auto-detected if not provided) | `"WeChat"` |

### Step 3: Handle output

Script outputs JSON to stdout:

**Success:**
```json
{
  "status": "success",
  "raw_path": "/full/path/to/article.md",
  "title": "Article Title",
  "author": "Author Name",
  "source": "WeChat",
  "url": "https://...",
  "word_count": 3500,
  "content": "Full Markdown content..."
}
```

**Already exists (skipped):**
```json
{
  "status": "skipped",
  "skipped": true,
  "raw_path": "/path/to/existing.md",
  "url": "https://...",
  "content": "Existing content..."
}
```

**Error:**
```json
{
  "status": "error",
  "error": "Content extraction failed. Page may require JavaScript rendering. Try browser-tool.",
  "url": "https://..."
}
```

## Notes

1. **Anti-scraping**: Script includes User-Agent/Referer headers. If it fails, use browser-tool instead.
2. **JS-rendered pages**: Content <100 chars triggers error with browser-tool suggestion.
3. **Duplicate detection**: Same URL already saved → returns `skipped: true`.
4. **Auto-install**: `trafilatura` installs automatically on first run.

## Script Location

`wiki_web_ingest.py` in this directory.
