#!/usr/bin/env python3
"""
wiki-feishu-transfer: Transfer Feishu message files to Feishu Drive

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
from pathlib import Path

import requests

# ── Configuration (edit these for your setup) ────────────────────
TEMP_DIR = r"C:\temp\wiki_transfer_temp"  # Temp directory for downloads

# Your Feishu Drive folder token (get from Drive URL: /drive/folder/XXXXX)
DEFAULT_DRIVE_FOLDER = "YOUR_FOLDER_TOKEN_HERE"  # CHANGE THIS!

# EasyClaw config path (standard location)
EASYCLAW_CONFIG = os.path.expanduser(r"~\.easyclaw\easyclaw.json")

# ── Feishu endpoints ─────────────────────────────────────────────
FEISHU_HOSTS = {
    "lark": "https://open.larksuite.com",
    "feishu": "https://open.feishu.cn",
}
FALLBACK_URLS = {
    "https://open.larksuite.com": "https://open.feishu.cn",
    "https://open.feishu.cn": "https://open.larksuite.com",
}

TOKEN_PATH = "/open-apis/auth/v3/tenant_access_token/internal"
RESOURCE_PATH = "/open-apis/im/v1/messages/{message_id}/resources/{file_key}?type=file"
UPLOAD_ALL_PATH = "/open-apis/drive/v1/files/upload_all"
UPLOAD_PREPARE_PATH = "/open-apis/drive/v1/files/upload_prepare"
UPLOAD_PART_PATH = "/open-apis/drive/v1/files/upload_part"
UPLOAD_FINISH_PATH = "/open-apis/drive/v1/files/upload_finish"

# Chunk threshold (use chunked upload for files > 20MB)
CHUNK_THRESHOLD = 20 * 1024 * 1024


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


def get_base_url(domain: str) -> str:
    return FEISHU_HOSTS.get(domain, FEISHU_HOSTS["feishu"])


def _do_get_token(app_id: str, app_secret: str, base_url: str) -> str:
    """Actually get tenant_access_token"""
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


def get_tenant_access_token(app_id: str, app_secret: str, base_url: str) -> str:
    """Get tenant_access_token with domain fallback"""
    try:
        return _do_get_token(app_id, app_secret, base_url)
    except (requests.exceptions.HTTPError, requests.exceptions.ConnectionError) as e:
        alt = FALLBACK_URLS.get(base_url)
        if alt:
            print(f"[Auth] {base_url} failed, trying fallback: {alt}", file=sys.stderr)
            return _do_get_token(app_id, app_secret, alt)
        raise


# ── Step 1: Download file (with domain fallback) ─────────────────

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
        fname = f"{file_key}.dat"

    file_path = Path(TEMP_DIR) / fname
    with open(file_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)

    size_mb = file_path.stat().st_size / (1024 * 1024)
    print(f"[Step 1] File downloaded: {file_path} ({size_mb:.2f} MB)", file=sys.stderr)
    return file_path


def download_file(message_id: str, file_key: str, token: str, base_url: str) -> Path:
    """Download with domain fallback"""
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


# ── Step 2: Upload to Feishu Drive ───────────────────────────────

def _do_upload_small(file_path: Path, filename: str, folder_token: str, token: str, base_url: str) -> str:
    """Upload small file (≤20MB)"""
    file_size = file_path.stat().st_size
    url = base_url + UPLOAD_ALL_PATH

    with open(file_path, "rb") as f:
        resp = requests.post(
            url,
            headers={"Authorization": f"Bearer {token}"},
            data={
                "file_name": filename,
                "parent_type": "explorer",
                "parent_node": folder_token,
                "size": str(file_size),
            },
            files={"file": (filename, f)},
            timeout=300,
        )

    resp.raise_for_status()
    data = resp.json()
    if data.get("code") != 0:
        raise RuntimeError(f"upload_all failed: {data}")

    file_token = data.get("data", {}).get("file_token", "")
    print(f"[Step 2] Small file upload complete: file_token={file_token}", file=sys.stderr)
    return file_token


def upload_small(file_path: Path, filename: str, folder_token: str, token: str, base_url: str) -> str:
    """Small file upload with domain fallback"""
    try:
        return _do_upload_small(file_path, filename, folder_token, token, base_url)
    except requests.exceptions.HTTPError as e:
        if e.response is not None and e.response.status_code in (502, 503, 404):
            alt = FALLBACK_URLS.get(base_url)
            if alt:
                print(f"[Step 2] upload_all {base_url} returned {e.response.status_code}, trying fallback: {alt}", file=sys.stderr)
                return _do_upload_small(file_path, filename, folder_token, token, alt)
        raise


def _do_upload_chunked(file_path: Path, filename: str, folder_token: str, token: str, base_url: str) -> str:
    """Upload large file (>20MB) with chunked upload"""
    file_size = file_path.stat().st_size
    headers = {"Authorization": f"Bearer {token}"}

    # Step 2a: upload_prepare
    print(f"[Step 2] Preparing chunked upload... (file size: {file_size / (1024*1024):.2f} MB)", file=sys.stderr)
    resp = requests.post(
        base_url + UPLOAD_PREPARE_PATH,
        headers={**headers, "Content-Type": "application/json"},
        json={
            "file_name": filename,
            "parent_type": "explorer",
            "parent_node": folder_token,
            "size": file_size,
        },
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") != 0:
        raise RuntimeError(f"upload_prepare failed: {data}")

    upload_id = data["data"]["upload_id"]
    block_size = data["data"]["block_size"]
    block_num = data["data"]["block_num"]
    print(f"[Step 2] upload_id={upload_id}, block_size={block_size}, block_num={block_num}", file=sys.stderr)

    # Step 2b: upload_part for each chunk
    with open(file_path, "rb") as f:
        for seq in range(block_num):
            chunk = f.read(block_size)
            if not chunk:
                break

            resp = requests.post(
                base_url + UPLOAD_PART_PATH,
                headers=headers,
                data={
                    "upload_id": upload_id,
                    "seq": str(seq),
                    "size": str(len(chunk)),
                },
                files={"file": (f"part_{seq}", chunk)},
                timeout=300,
            )
            resp.raise_for_status()
            part_data = resp.json()
            if part_data.get("code") != 0:
                raise RuntimeError(f"upload_part seq={seq} failed: {part_data}")

            print(f"[Step 2] Chunk {seq + 1}/{block_num} uploaded", file=sys.stderr)

    # Step 2c: upload_finish
    resp = requests.post(
        base_url + UPLOAD_FINISH_PATH,
        headers={**headers, "Content-Type": "application/json"},
        json={
            "upload_id": upload_id,
            "block_num": block_num,
        },
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") != 0:
        raise RuntimeError(f"upload_finish failed: {data}")

    file_token = data.get("data", {}).get("file_token", "")
    print(f"[Step 2] Chunked upload complete: file_token={file_token}", file=sys.stderr)
    return file_token


def upload_chunked(file_path: Path, filename: str, folder_token: str, token: str, base_url: str) -> str:
    """Chunked upload with domain fallback"""
    try:
        return _do_upload_chunked(file_path, filename, folder_token, token, base_url)
    except requests.exceptions.HTTPError as e:
        if e.response is not None and e.response.status_code in (502, 503, 404):
            alt = FALLBACK_URLS.get(base_url)
            if alt:
                print(f"[Step 2] Chunked upload {base_url} returned {e.response.status_code}, trying fallback: {alt}", file=sys.stderr)
                return _do_upload_chunked(file_path, filename, folder_token, token, alt)
        raise


def upload_to_drive(file_path: Path, filename: str, folder_token: str, token: str, base_url: str) -> tuple:
    """Choose upload method based on file size"""
    file_size = file_path.stat().st_size

    if file_size <= CHUNK_THRESHOLD:
        method = "upload_all"
        file_token = upload_small(file_path, filename, folder_token, token, base_url)
    else:
        method = "chunked"
        file_token = upload_chunked(file_path, filename, folder_token, token, base_url)

    return file_token, method, file_size


# ── Step 3: Cleanup ──────────────────────────────────────────────

def cleanup(*paths):
    """Clean up temp files"""
    for p in paths:
        try:
            if p and Path(p).exists():
                Path(p).unlink()
                print(f"[Step 3] Deleted: {p}", file=sys.stderr)
        except Exception as e:
            print(f"[Step 3] Failed to delete {p}: {e}", file=sys.stderr)

    try:
        temp = Path(TEMP_DIR)
        if temp.exists() and not any(temp.iterdir()):
            temp.rmdir()
    except Exception:
        pass


# ── Main ─────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Transfer Feishu message files to Drive")
    parser.add_argument("message_id", help="Feishu message ID")
    parser.add_argument("file_key", help="Feishu file key")
    parser.add_argument("--filename", required=True, help="File name to save in Drive")
    parser.add_argument(
        "--drive-folder",
        default=DEFAULT_DRIVE_FOLDER,
        help=f"Feishu Drive folder token (default: {DEFAULT_DRIVE_FOLDER})",
    )

    args = parser.parse_args()

    if args.drive_folder == "YOUR_FOLDER_TOKEN_HERE":
        print("ERROR: Please configure DEFAULT_DRIVE_FOLDER in the script or use --drive-folder", file=sys.stderr)
        sys.exit(1)

    local_file = None

    try:
        app_id, app_secret, domain = get_feishu_credentials()
        base_url = get_base_url(domain)
        print(f"[Config] domain={domain}, base_url={base_url}", file=sys.stderr)
        tenant_token = get_tenant_access_token(app_id, app_secret, base_url)

        # Step 1: Download
        local_file = download_file(args.message_id, args.file_key, tenant_token, base_url)

        # Step 2: Upload to Drive
        file_token, method, file_size = upload_to_drive(
            local_file, args.filename, args.drive_folder, tenant_token, base_url
        )

        result = {
            "status": "success",
            "file_token": file_token,
            "file_name": args.filename,
            "file_size": file_size,
            "drive_folder": args.drive_folder,
            "message_id": args.message_id,
            "upload_method": method,
        }
        print(json.dumps(result, ensure_ascii=False))

    except Exception as e:
        error_result = {
            "status": "error",
            "error": str(e),
            "message_id": args.message_id,
        }
        print(json.dumps(error_result, ensure_ascii=False))
        sys.exit(1)

    finally:
        cleanup(local_file)


if __name__ == "__main__":
    main()
