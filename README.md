# YouTube Video and Music Downloader

A modern web application and CLI tool to fetch video details and download/save YouTube videos and music directly to your computer.

## Features
- **URL Analysis**: Fetch title, thumbnail, duration, channel, and available formats/qualities.
- **Video Downloads**: Download MP4 videos in various qualities (e.g. 1080p, 720p, 480p, 360p, or best available).
- **Audio Extractions**: Extract and download audio files (MP3, M4A, WAV) from YouTube videos/music clips.
- **Real-Time Progress**: Track live download progress in the Web UI.
- **CLI Support**: Simple command line tool (`cli.py`) for downloading directly from terminal.
- **Clean Responsive UI**: Modern dark-themed user interface for smooth desktop and mobile experience.

## Installation

1. Ensure Python 3.10+ and `ffmpeg` are installed on your system.
   - On Linux (Ubuntu/Debian): `sudo apt-get install -y ffmpeg`
   - On macOS: `brew install ffmpeg`
   - On Windows: Install ffmpeg via winget or download from official site and add to PATH.

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Web Application

Start the Flask server:
```bash
python -m app.server
```
or
```bash
python app/server.py
```

Then open your browser and go to `http://localhost:5000`.

## Using the CLI Tool

Download video:
```bash
python cli.py --url "https://www.youtube.com/watch?v=dQw4w9WgXcQ" --type video --quality 720p
```

Download music / audio (MP3 format):
```bash
python cli.py --url "https://www.youtube.com/watch?v=dQw4w9WgXcQ" --type audio --quality mp3
```

Specify output directory:
```bash
python cli.py --url "https://www.youtube.com/watch?v=dQw4w9WgXcQ" --type audio --output-dir ~/Downloads
```

## Running Tests

Run the unit test suite:
```bash
pytest
```
