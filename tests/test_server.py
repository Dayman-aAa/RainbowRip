import os
import json
import time
import pytest
from unittest.mock import patch, MagicMock
from app.server import app, DOWNLOAD_DIR


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_index_route(client):
    rv = client.get('/')
    assert rv.status_code == 200
    assert b"MediaFetcher" in rv.data


def test_get_info_missing_url(client):
    rv = client.post('/api/info', json={})
    assert rv.status_code == 400
    data = json.loads(rv.data)
    assert "error" in data


@patch("yt_dlp.YoutubeDL")
def test_get_info_success(mock_ydl, client):
    mock_instance = MagicMock()
    mock_ydl.return_value.__enter__.return_value = mock_instance
    mock_instance.extract_info.return_value = {
        "title": "Test YouTube Video",
        "duration": 180,
        "uploader": "Test Channel",
        "thumbnail": "https://example.com/thumb.jpg",
        "description": "Test description for YouTube video",
        "formats": [
            {"height": 1080, "vcodec": "avc1"},
            {"height": 720, "vcodec": "avc1"},
            {"height": 360, "vcodec": "avc1"},
        ]
    }

    rv = client.post('/api/info', json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"})
    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert data["title"] == "Test YouTube Video"
    assert data["uploader"] == "Test Channel"
    assert data["duration"] == "03:00"
    assert "1080p" in data["video_qualities"]


@patch("yt_dlp.YoutubeDL")
def test_download_flow(mock_ydl, client):
    mock_instance = MagicMock()
    mock_ydl.return_value.__enter__.return_value = mock_instance
    mock_instance.extract_info.return_value = {
        "title": "Sample Song",
        "ext": "mp3"
    }
    mock_instance.prepare_filename.return_value = os.path.join(DOWNLOAD_DIR, "test_download_id_Sample Song.mp3")

    # Create dummy file to simulate downloaded file
    test_file_path = os.path.join(DOWNLOAD_DIR, "dummy_test_file.mp3")
    with open(test_file_path, "w") as f:
        f.write("dummy audio content")

    # Initiate download
    rv = client.post('/api/download', json={
        "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "type": "audio",
        "quality": "mp3"
    })
    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert "download_id" in data
    download_id = data["download_id"]

    # Check progress (may be starting or downloading/completed)
    time.sleep(0.3)
    rv_prog = client.get(f'/api/progress/{download_id}')
    assert rv_prog.status_code == 200

    # Test file serving endpoint
    rv_file = client.get(f'/api/files/dummy_test_file.mp3')
    assert rv_file.status_code == 200
    assert rv_file.data == b"dummy audio content"

    # Cleanup
    if os.path.exists(test_file_path):
        os.remove(test_file_path)


def test_progress_not_found(client):
    rv = client.get('/api/progress/nonexistent_id')
    assert rv.status_code == 404
