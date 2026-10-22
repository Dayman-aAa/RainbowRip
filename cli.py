#!/usr/bin/env python3
"""
CLI tool for downloading YouTube videos and music directly to your computer.
"""

import argparse
import os
import sys
import yt_dlp


def progress_hook(d):
    if d['status'] == 'downloading':
        total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
        downloaded = d.get('downloaded_bytes', 0)
        speed = d.get('speed', 0)
        eta = d.get('eta', 0)

        speed_str = f"{speed / 1024 / 1024:.2f} MB/s" if speed else "N/A"
        pct_str = f"{(downloaded / total) * 100:.1f}%" if total > 0 else "N/A"

        sys.stdout.write(f"\rDownloading: {pct_str} | Speed: {speed_str} | ETA: {eta}s")
        sys.stdout.flush()
    elif d['status'] == 'finished':
        sys.stdout.write("\nDownload complete. Processing file...\n")
        sys.stdout.flush()


def download_media(url: str, download_type: str = "video", quality: str = "best", output_dir: str = "."):
    os.makedirs(output_dir, exist_ok=True)

    out_tmpl = os.path.join(output_dir, "%(title)s.%(ext)s")
    ydl_opts = {
        'outtmpl': out_tmpl,
        'progress_hooks': [progress_hook],
        'quiet': True,
        'no_warnings': True,
    }

    if download_type.lower() == "audio":
        audio_fmt = quality.lower() if quality else "mp3"
        if audio_fmt not in ['mp3', 'm4a', 'wav', 'flac']:
            audio_fmt = "mp3"
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': audio_fmt,
                'preferredquality': '192',
            }],
        })
    else:
        # Video download
        if quality and quality.endswith('p') and quality[:-1].isdigit():
            height = quality[:-1]
            ydl_opts['format'] = f"bestvideo[height<={height}]+bestaudio/best[height<={height}]/best"
        else:
            ydl_opts['format'] = "bestvideo+bestaudio/best"
        ydl_opts['merge_output_format'] = 'mp4'

    print(f"Starting {download_type} download for: {url}")
    print(f"Quality/Format target: {quality}")
    print(f"Output directory: {os.path.abspath(output_dir)}")

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        if "entries" in info:
            info = info["entries"][0]
        filename = ydl.prepare_filename(info)
        print(f"\nSuccessfully saved: {filename}")


def main():
    parser = argparse.ArgumentParser(description="YouTube Video & Music Downloader CLI")
    parser.add_argument("--url", "-u", required=True, help="YouTube video/music URL")
    parser.add_argument("--type", "-t", choices=["video", "audio"], default="video", help="Download type: 'video' (MP4) or 'audio' (Music)")
    parser.add_argument("--quality", "-q", default="best", help="Quality (e.g. '1080p', '720p', '360p' for video; 'mp3', 'm4a', 'wav' for audio)")
    parser.add_argument("--output-dir", "-o", default=".", help="Directory to save downloaded file")

    args = parser.parse_args()

    try:
        download_media(
            url=args.url,
            download_type=args.type,
            quality=args.quality,
            output_dir=args.output_dir
        )
    except Exception as e:
        print(f"\nError downloading media: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
