# YouTube Downloader

![YouTube](assets/youtube.jpg)

Downloads YouTube videos from a URL list as `.mp4` files. Tries web → android → ios extractor clients to get the best available quality (4K VP9/AV1 where available).

## Requirements

- Python 3.10+
- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- [ffmpeg](https://ffmpeg.org/) — required for video+audio merging

## Setup

```bash
# 1. Clone
git clone <repo-url>
cd YoutubeSpoofer

# 2. Install dependencies
pip install yt-dlp

# macOS (recommended ffmpeg install)
brew install ffmpeg

# 3. Create your URL list
cp urls.txt.example urls.txt

# 4. Export YouTube cookies (required for best quality)
yt-dlp --cookies-from-browser chrome --cookies cookies.txt "https://www.youtube.com"
```

> **Why cookies?** YouTube blocks anonymous requests from the web client (which serves 4K). Exporting your cookies authenticates those requests. You only need to do this once — re-run if downloads start failing weeks later.
>
> Replace `chrome` with `firefox` or `safari` if needed.

## Usage

Add YouTube URLs to `urls.txt` (one per line) then run:

```bash
python3 main.py
```

Downloaded files are saved to `media/output/`.

```bash
# Optional: pass a custom URL file
python3 main.py /path/to/my-urls.txt
```

**How it works:**
- Reads URLs from `urls.txt`
- Downloads up to 10 videos per run
- Successfully downloaded URLs are removed from `urls.txt` automatically
- Failed URLs stay in `urls.txt` so the next run retries them

## Configuration

Edit the constants at the top of `main.py`:

| Variable | Default | Description |
|---|---|---|
| `MAX_DOWNLOADS` | `10` | Max videos per run |
| `COOKIES_FILE` | `cookies.txt` | Path to exported cookies file (preferred) |
| `COOKIES_BROWSER` | `"chrome"` | Browser to extract cookies from if `cookies.txt` not found |
| `DOWNLOAD_DIR` | `media/downloads` | Staging directory |
| `OUTPUT_DIR` | `media/output` | Final output directory |
| `URL_FILE` | `urls.txt` | Default URL list |

## Refreshing Cookies

If downloads start failing with auth errors, your cookies have expired. Re-export:

```bash
yt-dlp --cookies-from-browser chrome --cookies cookies.txt "https://www.youtube.com"
```
