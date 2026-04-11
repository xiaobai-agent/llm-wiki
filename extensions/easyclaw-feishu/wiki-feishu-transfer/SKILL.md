---
name: wiki-feishu-transfer
description: |
  Transfer files from Feishu group chat to Feishu Drive for archival.
  Trigger keywords: "transfer to drive", "archive video", "save source file".
  Typical use case: After wiki-video-ingest transcribes a video, call this skill to archive the original video to Drive.
---

# Feishu File Transfer to Drive (wiki-feishu-transfer)

Transfer Feishu message files to Feishu Drive for archival. **User can retrieve instantly via Drive link.**

## Prerequisites

- **Python 3** + `requests`
- Feishu IM API permissions (download message files)
- Feishu Drive API permissions (upload to drive)

## Configuration

### Drive Folder Token

You need to create a folder in Feishu Drive and get its token from the URL:

```
https://feishu.cn/drive/folder/XXXXX
                                ^^^^^
                           This is your folder_token
```

Edit `wiki_feishu_transfer.py`:

```python
DEFAULT_DRIVE_FOLDER = "your_folder_token_here"
```

Or pass via command line with `--drive-folder`.

## Usage

### Step 1: Get message_id and file_key

From Feishu message metadata (same as wiki-video-ingest).

### Step 2: Run the script

```bash
python wiki_feishu_transfer.py <message_id> <file_key> \
  --filename "meeting_recording.mp4" \
  --drive-folder "optional_custom_folder_token"
```

**Parameters:**

| Parameter | Required | Description | Example |
|-----------|----------|-------------|---------|
| `message_id` | ✅ | Feishu message ID | `om_abc123` |
| `file_key` | ✅ | Feishu file key | `file_v3_xxx` |
| `--filename` | ✅ | File name | `"meeting.mp4"` |
| `--drive-folder` | ❌ | Drive folder token (uses default if not set) | `"FolderToken"` |

### Step 3: Handle output

Script outputs JSON to stdout:

**Success (small file, upload_all):**
```json
{
  "status": "success",
  "file_token": "AbcDefGhIjK",
  "file_name": "meeting.mp4",
  "file_size": 15728640,
  "drive_folder": "FolderToken",
  "message_id": "om_abc123",
  "upload_method": "upload_all"
}
```

**Success (large file, chunked upload):**
```json
{
  "status": "success",
  "file_token": "AbcDefGhIjK",
  "file_name": "large_video.mp4",
  "file_size": 157286400,
  "drive_folder": "FolderToken",
  "message_id": "om_abc123",
  "upload_method": "chunked"
}
```

**Error:**
```json
{
  "status": "error",
  "error": "Error message",
  "message_id": "om_abc123"
}
```

## Internal Flow

1. **Download** — Feishu IM API → temp file
2. **Upload** — ≤20MB uses `upload_all`, >20MB uses chunked upload (4MB per chunk)
3. **Cleanup** — Auto-delete temp file

## Notes

1. **Domain fallback** — Auto-switches between `open.larksuite.com` ↔ `open.feishu.cn` on 502/503/404
2. **20MB limit** — `upload_all` only supports ≤20MB, larger files use 3-step chunked upload
3. **Chunked upload** — prepare → part (multiple, seq starts from 0) → finish
4. **parent_type** — Always `"explorer"` for Drive uploads
5. **Temp cleanup** — `finally` block ensures cleanup

## Script Location

`wiki_feishu_transfer.py` in this directory.
