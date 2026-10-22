import os
import pytest
from unittest.mock import patch, MagicMock
from cli import download_media, main


@patch("yt_dlp.YoutubeDL")
def test_cli_download_video(mock_ydl, tmp_path):
    mock_instance = MagicMock()
    mock_ydl.return_value.__enter__.return_value = mock_instance
    mock_instance.extract_info.return_value = {
        "title": "CLI Test Video"
    }
    mock_instance.prepare_filename.return_value = str(tmp_path / "CLI Test Video.mp4")

    download_media(
        url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        download_type="video",
        quality="720p",
        output_dir=str(tmp_path)
    )

    mock_instance.extract_info.assert_called_once_with(
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        download=True
    )


@patch("yt_dlp.YoutubeDL")
def test_cli_download_audio(mock_ydl, tmp_path):
    mock_instance = MagicMock()
    mock_ydl.return_value.__enter__.return_value = mock_instance
    mock_instance.extract_info.return_value = {
        "title": "CLI Test Song"
    }
    mock_instance.prepare_filename.return_value = str(tmp_path / "CLI Test Song.mp3")

    download_media(
        url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        download_type="audio",
        quality="mp3",
        output_dir=str(tmp_path)
    )

    mock_instance.extract_info.assert_called_once_with(
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        download=True
    )


def test_cli_main_argparse():
    with patch("sys.argv", ["cli.py", "--url", "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "--type", "audio"]), \
         patch("cli.download_media") as mock_download:
        main()
        mock_download.assert_called_once_with(
            url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            download_type="audio",
            quality="best",
            output_dir="."
        )
