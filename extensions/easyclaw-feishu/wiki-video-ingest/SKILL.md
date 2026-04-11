---
name: wiki-video-ingest
description: |
  Download video from Feishu group chat → Extract audio with ffmpeg → Transcribe with EasyClaw API → Save transcript to wiki/raw/video/.
  Trigger keywords: "transcribe this video", "video ingest", "convert video to text".
  This skill only handles the "heavy lifting" (download → extract → transcribe → save). Knowledge extraction is done by the LLM.
---

# Video Transcription Ingest (wiki-video-ingest)

Transcribe Feishu video messages and save to `wiki/raw/video/`. **Saves 70-80% tokens vs feeding raw video.**

## Prerequisites

- **ffmpeg** installed (update path in script if needed)
- **Python 3** + `requests`
- Feishu IM API permissions enabled
- EasyClaw transcription API available

## Usage

### Step 1: Get message_id and file_key

From Feishu message metadata:
- `message_id`: Message ID (format `om_xxxxxx`)
- `file_key`: File key (extract from message content JSON)

### Step 2: Run the script

```bash
python wiki_video_ingest.py <message_id> <file_key> \
  --title "Video Title" \
  --platform "YouTube" \
  --output-dir "/absolute/path/to/wiki/raw/video"
```

**Parameters:**

| Parameter | Required | Description | Example |
|-----------|----------|-------------|---------|
| `message_id` | ✅ | Feishu message ID | `om_abc123` |
| `file_key` | ✅ | Feishu file key | `file_v3_xxx` |
| `--title` | ✅ | Video title | `"Karpathy on LLMs"` |
| `--platform` | ❌ | Source platform (default: "Unknown") | `"YouTube"` / `"Bilibili"` |
| `--output-dir` | ✅ | Output directory (**absolute path**) | `/home/user/wiki/raw/video` |

### Step 3: Handle output

Script outputs JSON to stdout:

**Success:**
```json
{
  "status": "success",
  "transcript_path": "/full/path/to/transcript.md",
  "transcript_text": "Full transcript...",
  "word_count": 1852,
  "audio_tokens": 3753,
  "text_tokens": 3704,
  "duration_seconds": 237.0,
  "cost_estimate_cny": 0.0051
}
```

**Error:**
```json
{
  "status": "error",
  "error": "Error message"
}
```

## Internal Flow (5 steps)

1. **Download video** — Feishu IM API (tenant_access_token) → save to temp dir
2. **Extract audio** — ffmpeg 16kHz mono 64kbps MP3 (16:1 compression)
3. **Transcribe** — EasyClaw API `gpt-4o-mini-transcribe`
4. **Save transcript** — `{output-dir}/YYYY-MM-DD-[platform]title.md` (with YAML frontmatter)
5. **Cleanup** — Auto-delete temp video and audio files

## Cost Reference

| Video Duration | Estimated Cost |
|----------------|----------------|
| 4 min | ~$0.001 |
| 30 min | ~$0.015 |
| 1 hour | ~$0.03 |

## Configuration

Edit constants at the top of `wiki_video_ingest.py`:

```python
FFMPEG_PATH = r"C:\tools\ffmpeg\bin\ffmpeg.exe"  # Your ffmpeg path
TEMP_DIR = r"C:\temp\wiki_video_temp"  # Temp file directory
```

## Script Location

`wiki_video_ingest.py` in this directory.
