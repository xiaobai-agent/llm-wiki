#!/usr/bin/env python3
"""
wiki-video-ingest: Download video from Feishu → ffmpeg extract audio → EasyClaw transcribe → Save transcript

Part of the EasyClaw + Feishu extension for LLM Wiki.
https://github.com/xiaobai-agent/llm-wiki
"""

import io
import sys

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import argparse
import json
import os
import subprocess
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

import requests

# ── Configuration (edit these for your setup) ────────────────────
FFMPEG_PATH = r"C:\tools\ffmpeg\bin\ffmpeg.exe"  # Change to your ffmpeg path
TEMP_DIR = r"C:\temp\wiki_video_temp"  # Temp directory for downloads

# EasyClaw paths (standard locations, usually don't need to change)
EASYCLAW_USERINFO = os.path.expanduser(r"~\.easyclaw\identity\easyclaw-userinfo.json")
EASYCLAW_CONFIG = os.path.expanduser(r"~\.easyclaw\easyclaw.json")
TRANSCRIPTION_URL = "https://aibot-srv.easyclaw.com/audio/transcriptions"
TRANSCRIPTION_MODEL = "gpt-4o-mini-transcribe"

# Feishu endpoints (auto-detected from config)
FEISHU_HOSTS = {
    "lark": "https://open.larksuite.com",   # International
    "feishu": "https://open.feishu.cn",     # China
}
TOKEN_PATH = "/open-apis/auth/v3/tenant_access_token/internal"
RESOURCE_PATH = "/open-apis/im/v1/messages/{message_id}/resources/{file_key}?type=file"


def get_feishu_credentials():
    """Read Feishu appId, appSecret and domain from easyclaw.json"""
    with open(EASYCLAW_CONFIG, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    feishu = cfg.get("channels", {}).get("feishu", {})
    app_id = feishu.get("appId")
    app_secret = feishu.get("appSecret")
    domain = feishu.get("domain", "feishu")
    if not app_id or not app_secret:
        raise RuntimeError("Feishu appId/appSecret not found in easyclaw.json")
    return app_id, app_secret, domain


def get_feishu_base_url(domain: str) -> str:
    """Get Feishu API base URL by domain"""
    return FEISHU_HOSTS.get(domain, FEISHU_HOSTS["feishu"])


def get_tenant_access_token(app_id: str, app_secret: str, base_url: str) -> str:
    """Get Feishu tenant_access_token"""
    resp = requests.post(
        base_url + TOKEN_PATH,
        json={"app_id": app_id, "app_secret": app_secret},
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") != 0:
        raise RuntimeError(f"Failed to get tenant_access_token: {data}")
    return data["tenant_access_token"]


def _do_download(message_id: str, file_key: str, token: str, base_url: str) -> Path:
    """Actually download the file"""
    os.makedirs(TEMP_DIR, exist_ok=True)
    url = (base_url + RESOURCE_PATH).format(message_id=message_id, file_key=file_key)
    resp = requests.get(
        url,
        headers={"Authorization": f"Bearer {token}"},
        stream=True,
        timeout=300,
    )
    resp.raise_for_status()

    content_disp = resp.headers.get("Content-Disposition", "")
    if "filename=" in content_disp:
        fname = content_disp.split("filename=")[-1].strip('" ')
    else:
        fname = f"{file_key}.mp4"

    video_path = Path(TEMP_DIR) / fname
    with open(video_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)

    size_mb = video_path.stat().st_size / (1024 * 1024)
    print(f"[Step 1] Video downloaded: {video_path} ({size_mb:.2f} MB)", file=sys.stderr)
    return video_path


# Domain fallback mapping
FALLBACK_URLS = {
    "https://open.larksuite.com": "https://open.feishu.cn",
    "https://open.feishu.cn": "https://open.larksuite.com",
}


def download_video(message_id: str, file_key: str, token: str, base_url: str) -> Path:
    """Step 1: Download video from Feishu (with domain fallback)"""
    try:
        return _do_download(message_id, file_key, token, base_url)
    except requests.exceptions.HTTPError as e:
        if e.response is not None and e.response.status_code in (502, 503, 404):
            alt = FALLBACK_URLS.get(base_url)
            if alt:
                print(
                    f"[Step 1] {base_url} returned {e.response.status_code}, trying fallback: {alt}",
                    file=sys.stderr,
                )
                return _do_download(message_id, file_key, token, alt)
        raise


def extract_audio(video_path: Path) -> Path:
    """Step 2: Extract audio with ffmpeg (16kHz mono 64kbps MP3)"""
    audio_path = video_path.with_suffix(".mp3")
    cmd = [
        FFMPEG_PATH,
        "-i", str(video_path),
        "-vn",
        "-acodec", "libmp3lame",
        "-ar", "16000",
        "-ac", "1",
        "-b:a", "64k",
        "-y",
        str(audio_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {result.stderr}")

    size_mb = audio_path.stat().st_size / (1024 * 1024)
    print(f"[Step 2] Audio extracted: {audio_path} ({size_mb:.2f} MB)", file=sys.stderr)
    return audio_path


def get_audio_duration(audio_path: Path) -> float:
    """Get audio duration in seconds using ffmpeg"""
    cmd = [
        FFMPEG_PATH,
        "-i", str(audio_path),
        "-f", "null", "-"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    for line in result.stderr.splitlines():
        if "Duration:" in line:
            time_str = line.split("Duration:")[1].split(",")[0].strip()
            parts = time_str.split(":")
            return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
    return 0.0


def transcribe_audio(audio_path: Path) -> dict:
    """Step 3: Call EasyClaw transcription API"""
    with open(EASYCLAW_USERINFO, "r", encoding="utf-8") as f:
        userinfo = json.load(f)
    uid = userinfo["uid"]
    token = userinfo["token"]

    headers = {
        "X-Auth-Uid": uid,
        "X-Auth-Token": token,
        "Authorization": "Bearer easyclaw-placeholder",
    }

    with open(audio_path, "rb") as audio_file:
        files = {"file": (audio_path.name, audio_file, "audio/mpeg")}
        data = {"model": TRANSCRIPTION_MODEL}
        resp = requests.post(
            TRANSCRIPTION_URL,
            headers=headers,
            files=files,
            data=data,
            timeout=600,
        )

    resp.raise_for_status()
    result = resp.json()
    transcript_text = result.get("text", "")

    text_tokens = len(transcript_text) * 2  # Rough estimate
    audio_tokens = result.get("usage", {}).get("total_tokens", 0)

    print(f"[Step 3] Transcription complete: {len(transcript_text)} chars", file=sys.stderr)
    return {
        "text": transcript_text,
        "audio_tokens": audio_tokens,
        "text_tokens": text_tokens,
    }


def save_transcript(
    transcript_text: str,
    output_dir: str,
    title: str,
    platform: str,
    duration_seconds: float,
    audio_tokens: int,
    text_tokens: int,
) -> Path:
    """Step 4: Save transcript with YAML frontmatter"""
    os.makedirs(output_dir, exist_ok=True)

    tz = timezone(timedelta(hours=8))
    date_str = datetime.now(tz).strftime("%Y-%m-%d")
    safe_title = title.replace("/", "_").replace("\\", "_").replace(":", "_").replace("?", "_").replace('"', "_")
    filename = f"{date_str}-[{platform}]{safe_title}.md"
    filepath = Path(output_dir) / filename

    frontmatter = f"""---
title: "{title}"
type: video_transcript
source_platform: "{platform}"
date: "{date_str}"
duration_seconds: {duration_seconds:.1f}
word_count: {len(transcript_text)}
audio_tokens: {audio_tokens}
text_tokens: {text_tokens}
---

"""
    content = frontmatter + transcript_text

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"[Step 4] Transcript saved: {filepath}", file=sys.stderr)
    return filepath


def cleanup(*paths):
    """Step 5: Clean up temp files"""
    for p in paths:
        try:
            if p and Path(p).exists():
                Path(p).unlink()
                print(f"[Step 5] Deleted: {p}", file=sys.stderr)
        except Exception as e:
            print(f"[Step 5] Failed to delete {p}: {e}", file=sys.stderr)

    try:
        temp = Path(TEMP_DIR)
        if temp.exists() and not any(temp.iterdir()):
            temp.rmdir()
    except Exception:
        pass


def main():
    parser = argparse.ArgumentParser(description="Video transcription ingest tool")
    parser.add_argument("message_id", help="Feishu message ID")
    parser.add_argument("file_key", help="Feishu file key")
    parser.add_argument("--title", required=True, help="Video title")
    parser.add_argument("--platform", default="Unknown", help="Source platform (YouTube/Bilibili/etc)")
    parser.add_argument("--output-dir", required=True, help="Output directory (absolute path)")

    args = parser.parse_args()

    video_path = None
    audio_path = None

    try:
        # Step 1: Download
        app_id, app_secret, domain = get_feishu_credentials()
        base_url = get_feishu_base_url(domain)
        print(f"[Config] Feishu domain={domain}, base_url={base_url}", file=sys.stderr)
        tenant_token = get_tenant_access_token(app_id, app_secret, base_url)
        video_path = download_video(args.message_id, args.file_key, tenant_token, base_url)

        # Step 2: Extract audio
        audio_path = extract_audio(video_path)
        duration = get_audio_duration(audio_path)

        # Step 3: Transcribe
        transcription = transcribe_audio(audio_path)

        # Step 4: Save
        transcript_path = save_transcript(
            transcript_text=transcription["text"],
            output_dir=args.output_dir,
            title=args.title,
            platform=args.platform,
            duration_seconds=duration,
            audio_tokens=transcription["audio_tokens"],
            text_tokens=transcription["text_tokens"],
        )

        cost_usd = (duration / 60) * 0.003
        cost_cny = cost_usd * 7.2

        result = {
            "status": "success",
            "transcript_path": str(transcript_path),
            "transcript_text": transcription["text"],
            "word_count": len(transcription["text"]),
            "audio_tokens": transcription["audio_tokens"],
            "text_tokens": transcription["text_tokens"],
            "duration_seconds": round(duration, 1),
            "cost_estimate_cny": round(cost_cny, 4),
        }
        print(json.dumps(result, ensure_ascii=False))

    except Exception as e:
        error_result = {
            "status": "error",
            "error": str(e),
        }
        print(json.dumps(error_result, ensure_ascii=False))
        sys.exit(1)

    finally:
        cleanup(video_path, audio_path)


if __name__ == "__main__":
    main()
