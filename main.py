import subprocess
import os
import sys
import shutil
from typing import Optional

# --- Configuration ---
_BASE = os.path.dirname(os.path.abspath(__file__))

DOWNLOAD_DIR   = os.path.join(_BASE, 'media', 'downloads')  # staging (yt-dlp writes here)
OUTPUT_DIR     = os.path.join(_BASE, 'media', 'output')     # final destination
URL_FILE       = os.path.join(_BASE, 'urls.txt')
MAX_DOWNLOADS   = 10
COOKIES_FILE    = os.path.join(_BASE, 'cookies.txt')  # export once: see README
COOKIES_BROWSER = "chrome"                            # fallback if cookies.txt not found

os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


def _cookie_args() -> list:
    """Use cookies.txt if it exists, otherwise fall back to live browser extraction."""
    if os.path.isfile(COOKIES_FILE):
        return ['--cookies', COOKIES_FILE]
    if COOKIES_BROWSER:
        return ['--cookies-from-browser', COOKIES_BROWSER]
    return []


def run_yt_dlp(url: str, output_path: str) -> int:
    """
    Try web → android → ios extractor clients to get the best available quality.
    Web client is tried first because it supports 4K VP9/AV1; android/ios are capped at 1080p.
    """
    output_tmpl = os.path.join(output_path, '%(title).150s [%(id)s].%(ext)s')
    ytdlp = [sys.executable, '-m', 'yt_dlp']
    base_cmd = [
        *ytdlp,
        '-f', 'bestvideo+bestaudio/best',
        '--merge-output-format', 'mp4',
        '-o', output_tmpl,
        '--no-simulate',
        '--no-playlist',
        '--retry-sleep', '2',
        '--concurrent-fragments', '4',
    ]
    base_cmd.extend(_cookie_args())
    base_cmd.append(url)

    for extra in [
        [],                                                      # web (default) — 4K/VP9/AV1 capable
        ['--extractor-args', 'youtube:player_client=android'],  # fallback — capped at 1080p
        ['--extractor-args', 'youtube:player_client=ios'],      # fallback — capped at 1080p
    ]:
        label = ' '.join(extra) if extra else 'web'
        print(f"  [{label}] {url}")
        if subprocess.run(base_cmd[:1] + extra + base_cmd[1:]).returncode == 0:
            return 0
        print("  variant failed, trying next...")

    # Last resort: web_creator client with best quality (avoids throttling on some videos)
    print("  final fallback: web_creator client...")
    fallback = [
        *ytdlp,
        '--extractor-args', 'youtube:player_client=web_creator',
        '-f', 'bestvideo+bestaudio/best',
        '--merge-output-format', 'mp4',
        '-o', output_tmpl,
        '--no-simulate',
        '--no-playlist',
    ]
    fallback.extend(_cookie_args())
    fallback.append(url)
    return subprocess.run(fallback).returncode


def get_latest_file(directory: str) -> Optional[str]:
    files = [os.path.join(directory, f) for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
    return max(files, key=os.path.getctime) if files else None


def download(url: str) -> Optional[str]:
    try:
        if run_yt_dlp(url, DOWNLOAD_DIR) != 0:
            print("  yt-dlp failed.")
            return None
        latest = get_latest_file(DOWNLOAD_DIR)
        if latest and os.path.getsize(latest) > 0:
            dest = os.path.join(OUTPUT_DIR, os.path.basename(latest))
            if os.path.exists(dest):
                os.remove(dest)
            shutil.move(latest, dest)
            print(f"  saved -> {dest}\n")
            return dest
        print("  no output file found.")
        return None
    except FileNotFoundError:
        print("  yt-dlp not found — run: pip install yt-dlp")
        print(f"  (using Python: {sys.executable})")
        return None
    except Exception as e:
        print(f"  error: {e}")
        return None


def file_summary(path: str) -> str:
    size = os.path.getsize(path)
    if size >= 1_073_741_824:
        size_str = f"{size / 1_073_741_824:.1f} GB"
    elif size >= 1_048_576:
        size_str = f"{size / 1_048_576:.1f} MB"
    else:
        size_str = f"{size / 1024:.1f} KB"
    return f"{os.path.basename(path)}  ({size_str})"


def run(url_file: str = URL_FILE):
    if not os.path.isfile(url_file):
        print(f"URL file not found: {url_file}")
        print("Create urls.txt and add one YouTube URL per line.")
        return

    with open(url_file) as f:
        urls = [l.strip() for l in f if l.strip() and not l.startswith('#')]

    if not urls:
        print("urls.txt is empty — add some URLs and run again.")
        return

    print(f"Found {len(urls)} URL(s). Processing up to {MAX_DOWNLOADS}.\n")

    remaining = list(urls)
    succeeded, failed = [], []

    for url in urls[:MAX_DOWNLOADS]:
        print(f"Downloading: {url}")
        result = download(url)
        if result:
            remaining.remove(url)
            succeeded.append(result)
        else:
            failed.append(url)
            print(f"  skipped (failed): {url}\n")

    with open(url_file, 'w') as f:
        f.writelines(u + '\n' for u in remaining)

    # --- Summary ---
    width = 72
    print("\n" + "─" * width)
    print(f"  Downloaded {len(succeeded)}/{len(succeeded) + len(failed)}  •  {len(remaining)} URL(s) remaining in queue")
    print("─" * width)
    for path in succeeded:
        print(f"  ✓  {file_summary(path)}")
    for url in failed:
        print(f"  ✗  {url}")
    print("─" * width)


if __name__ == '__main__':
    run(sys.argv[1] if len(sys.argv) > 1 else URL_FILE)
