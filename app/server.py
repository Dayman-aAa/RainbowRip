import os
import uuid
import threading
import time
from typing import Dict, Any
from flask import Flask, request, jsonify, send_from_directory, render_template
from flask_cors import CORS
import yt_dlp

app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)

DOWNLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# In-memory store for active/completed downloads
# format: download_id -> {"status": "starting"|"downloading"|"completed"|"error", "progress": float, "filename": str, "error": str}
downloads_status: Dict[str, Dict[str, Any]] = {}


def format_duration(seconds: float) -> str:
    if not seconds:
        return "00:00"
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/info", methods=["POST"])
def get_info():
    data = request.get_json() or {}
    url = data.get("url", "").strip()

    if not url:
        return jsonify({"error": "URL parameter is required"}), 400

    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            # If playlist/multi-entry, take first entry for simplicity or return info
            if "entries" in info:
                info = info["entries"][0]

            title = info.get("title", "Unknown Title")
            duration_sec = info.get("duration", 0)
            duration_str = format_duration(duration_sec)
            uploader = info.get("uploader") or info.get("channel") or "Unknown"
            thumbnail = info.get("thumbnail") or ""
            description = info.get("description", "")
            if description and len(description) > 200:
                description = description[:200] + "..."

            # Available video resolutions
            formats = info.get("formats", [])
            available_heights = set()
            for f in formats:
                h = f.get("height")
                if h and f.get("vcodec") != "none":
                    available_heights.add(h)

            height_list = sorted(list(available_heights), reverse=True)
            video_qualities = [f"{h}p" for h in height_list if h >= 144]
            if not video_qualities:
                video_qualities = ["best", "720p", "480p", "360p"]

            audio_formats = ["mp3", "m4a", "wav", "flac"]

            return jsonify({
                "url": url,
                "title": title,
                "uploader": uploader,
                "duration": duration_str,
                "duration_sec": duration_sec,
                "thumbnail": thumbnail,
                "description": description,
                "video_qualities": video_qualities,
                "audio_formats": audio_formats,
            })

    except Exception as e:
        return jsonify({"error": f"Failed to fetch video details: {str(e)}"}), 400


def progress_hook(d, download_id):
    if d['status'] == 'downloading':
        total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
        downloaded = d.get('downloaded_bytes', 0)
        if total > 0:
            pct = round((downloaded / total) * 100, 1)
        else:
            pct = 0.0
        downloads_status[download_id]["progress"] = pct
        downloads_status[download_id]["status"] = "downloading"
    elif d['status'] == 'finished':
        downloads_status[download_id]["progress"] = 100.0
        downloads_status[download_id]["status"] = "processing"


def run_download_thread(download_id: str, url: str, download_type: str, quality: str):
    try:
        downloads_status[download_id] = {
            "status": "starting",
            "progress": 0.0,
            "filename": None,
            "error": None
        }

        output_template = os.path.join(DOWNLOAD_DIR, f"{download_id}_%(title)s.%(ext)s")

        ydl_opts = {
            'outtmpl': output_template,
            'progress_hooks': [lambda d: progress_hook(d, download_id)],
            'quiet': True,
            'no_warnings': True,
        }

        if download_type == "audio":
            audio_format = quality.lower() if quality else "mp3"
            ydl_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': audio_format if audio_format in ['mp3', 'm4a', 'wav', 'flac'] else 'mp3',
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

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if "entries" in info:
                info = info["entries"][0]

            filename = ydl.prepare_filename(info)
            if download_type == "audio":
                # Ext changed post conversion
                base, _ = os.path.splitext(filename)
                fmt = quality.lower() if quality in ['mp3', 'm4a', 'wav', 'flac'] else 'mp3'
                filename = f"{base}.{fmt}"
            elif not filename.endswith('.mp4') and os.path.exists(os.path.splitext(filename)[0] + '.mp4'):
                filename = os.path.splitext(filename)[0] + '.mp4'

            basename = os.path.basename(filename)
            downloads_status[download_id]["filename"] = basename
            downloads_status[download_id]["status"] = "completed"
            downloads_status[download_id]["progress"] = 100.0

    except Exception as e:
        downloads_status[download_id]["status"] = "error"
        downloads_status[download_id]["error"] = str(e)


@app.route("/api/download", methods=["POST"])
def start_download():
    data = request.get_json() or {}
    url = data.get("url", "").strip()
    download_type = data.get("type", "video").lower()  # "video" or "audio"
    quality = data.get("quality", "best")

    if not url:
        return jsonify({"error": "URL parameter is required"}), 400

    download_id = str(uuid.uuid4())
    thread = threading.Thread(
        target=run_download_thread,
        args=(download_id, url, download_type, quality),
        daemon=True
    )
    thread.start()

    return jsonify({
        "download_id": download_id,
        "message": "Download started"
    })


@app.route("/api/progress/<download_id>", methods=["GET"])
def get_progress(download_id):
    status_info = downloads_status.get(download_id)
    if not status_info:
        return jsonify({"error": "Download ID not found"}), 404
    return jsonify(status_info)


@app.route("/api/files/<filename>", methods=["GET"])
def download_file(filename):
    # Ensure secure filename preventing path traversal
    safe_filename = os.path.basename(filename)
    return send_from_directory(
        DOWNLOAD_DIR,
        safe_filename,
        as_attachment=True
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
