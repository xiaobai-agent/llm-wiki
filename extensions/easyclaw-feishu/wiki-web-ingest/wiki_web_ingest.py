#!/usr/bin/env python3
"""
wiki-web-ingest: Fetch web articles → Extract content → Save to wiki raw directory

Part of the EasyClaw + Feishu extension for LLM Wiki.
https://github.com/xiaobai-agent/llm-wiki
"""

import io
import sys

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# ── Auto dependency check ──
import importlib
import subprocess


def ensure_dependency(package_name, pip_name=None):
    try:
        importlib.import_module(package_name)
    except ImportError:
        print(f"[Dependency] Installing {pip_name or package_name}...", file=sys.stderr)
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", pip_name or package_name, "-q"],
            stdout=subprocess.DEVNULL,
        )


ensure_dependency("trafilatura")

# ── Imports ──
import argparse
import hashlib
import json
import os
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.parse import urlparse

import requests
import trafilatura

# ── Constants ──
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/125.0.0.0 Safari/537.36"
)

# Domain → Source name mapping (for frontmatter metadata)
DOMAIN_SOURCE_MAP = {
    "mp.weixin.qq.com": "WeChat",
    "view.inews.qq.com": "Tencent News",
    "new.qq.com": "Tencent News",
    "www.xiaohongshu.com": "Xiaohongshu",
    "www.douyin.com": "Douyin",
    "36kr.com": "36Kr",
    "www.163.com": "NetEase",
    "juejin.cn": "Juejin",
    "zhuanlan.zhihu.com": "Zhihu",
    "www.zhihu.com": "Zhihu",
    "www.toutiao.com": "Toutiao",
    "www.bilibili.com": "Bilibili",
    "medium.com": "Medium",
    "dev.to": "Dev.to",
    "hackernews.com": "Hacker News",
}

# Title suffixes to remove
TITLE_SUFFIXES = [
    " - Tencent News", " - Zhihu", " - Juejin",
    " - 36Kr", " | 36Kr", " - Toutiao",
    " - WeChat", " - bilibili", " | Medium",
    " - 腾讯新闻", "_腾讯新闻", " - 知乎", " - 掘金",
    "_手机新浪网", " - 36氪", " | 36氪", "_网易订阅",
    " - 今日头条", " - 微信公众号",
]


def infer_source(url: str) -> str:
    """Infer source platform from URL domain"""
    hostname = urlparse(url).hostname or ""
    for domain, source in DOMAIN_SOURCE_MAP.items():
        if hostname == domain or hostname.endswith("." + domain):
            return source
    return hostname or "Unknown"


def clean_title(title: str) -> str:
    """Clean title: remove site name suffixes"""
    if not title:
        return "Untitled"
    for suffix in TITLE_SUFFIXES:
        if title.endswith(suffix):
            title = title[: -len(suffix)]
    return title.strip() or "Untitled"


def safe_filename(title: str, max_len: int = 80) -> str:
    """Generate safe filename"""
    safe = re.sub(r'[\\/:*?"<>|\r\n\t]', "_", title)
    safe = re.sub(r"_+", "_", safe).strip("_")
    if len(safe) > max_len:
        safe = safe[:max_len].rstrip("_")
    return safe or "untitled"


def url_hash(url: str) -> str:
    """Generate short hash from URL"""
    return hashlib.md5(url.encode("utf-8")).hexdigest()[:8]


def check_duplicate(output_dir: str, url: str) -> str | None:
    """Check if URL already fetched, return existing file path or None"""
    output_path = Path(output_dir)
    if not output_path.exists():
        return None
    for f in output_path.glob("*.md"):
        try:
            with open(f, "r", encoding="utf-8") as fh:
                for i, line in enumerate(fh):
                    if i > 20:
                        break
                    if line.strip().startswith("url:"):
                        existing_url = line.split("url:", 1)[1].strip().strip('"').strip("'")
                        if existing_url == url:
                            return str(f)
        except Exception:
            continue
    return None


def fetch_webpage(url: str) -> dict:
    """Step 1: Fetch webpage and extract content"""
    headers = {
        "User-Agent": USER_AGENT,
        "Referer": "https://www.google.com/",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
    }

    try:
        resp = requests.get(url, headers=headers, timeout=30, allow_redirects=True)
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Request failed: {e}")

    if resp.encoding and resp.encoding.lower() in ("iso-8859-1",):
        resp.encoding = resp.apparent_encoding

    html = resp.text

    extracted = trafilatura.extract(
        html,
        output_format="markdown",
        include_links=True,
        include_images=True,
        include_formatting=True,
        favor_precision=False,
        favor_recall=True,
    )

    metadata = trafilatura.extract_metadata(html)

    title = ""
    author = ""
    publish_date = ""

    if metadata:
        title = metadata.title or ""
        author = metadata.author or ""
        publish_date = metadata.date or ""

    title = clean_title(title)

    if not extracted or len(extracted.strip()) < 100:
        raise RuntimeError(
            "Content extraction failed or too short (<100 chars). "
            "Page may require JavaScript rendering. Try browser-tool."
        )

    return {
        "title": title,
        "author": author,
        "publish_date": publish_date,
        "content": extracted.strip(),
    }


def save_article(
    content: str,
    output_dir: str,
    title: str,
    author: str,
    source: str,
    url: str,
    publish_date: str,
) -> Path:
    """Step 2: Save to raw directory"""
    os.makedirs(output_dir, exist_ok=True)

    tz = timezone(timedelta(hours=8))
    date_str = datetime.now(tz).strftime("%Y-%m-%d")
    fetched_str = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")

    filename = f"{date_str}-{safe_filename(title)}.md"
    filepath = Path(output_dir) / filename

    word_count = len(content)

    frontmatter = f"""---
title: "{title}"
url: "{url}"
source: "{source}"
author: "{author}"
publish_date: "{publish_date}"
fetched: "{fetched_str}"
word_count: {word_count}
---

"""
    full_content = frontmatter + content

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(full_content)

    print(f"[Step 2] Article saved: {filepath} ({word_count} chars)", file=sys.stderr)
    return filepath


def main():
    parser = argparse.ArgumentParser(description="Web article ingest tool")
    parser.add_argument("url", help="Web page URL")
    parser.add_argument("--source", default=None, help="Source platform (optional, auto-detected)")
    parser.add_argument("--output-dir", required=True, help="Output directory (absolute path)")

    args = parser.parse_args()

    try:
        source = args.source or infer_source(args.url)
        print(f"[Config] URL={args.url}, source={source}", file=sys.stderr)

        existing = check_duplicate(args.output_dir, args.url)
        if existing:
            print(f"[Skip] Already exists: {existing}", file=sys.stderr)
            with open(existing, "r", encoding="utf-8") as f:
                existing_content = f.read()
            parts = existing_content.split("---", 2)
            body = parts[2].strip() if len(parts) >= 3 else existing_content

            result = {
                "status": "skipped",
                "skipped": True,
                "raw_path": existing,
                "url": args.url,
                "source": source,
                "content": body,
                "word_count": len(body),
            }
            print(json.dumps(result, ensure_ascii=False))
            return

        print("[Step 1] Fetching webpage...", file=sys.stderr)
        article = fetch_webpage(args.url)

        filepath = save_article(
            content=article["content"],
            output_dir=args.output_dir,
            title=article["title"],
            author=article["author"],
            source=source,
            url=args.url,
            publish_date=article["publish_date"],
        )

        result = {
            "status": "success",
            "raw_path": str(filepath),
            "title": article["title"],
            "author": article["author"],
            "source": source,
            "url": args.url,
            "word_count": len(article["content"]),
            "content": article["content"],
        }
        print(json.dumps(result, ensure_ascii=False))

    except Exception as e:
        error_result = {
            "status": "error",
            "error": str(e),
            "url": args.url,
        }
        print(json.dumps(error_result, ensure_ascii=False))
        sys.exit(1)


if __name__ == "__main__":
    main()
