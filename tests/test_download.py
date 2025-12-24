"""Tests for download manager."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

from pyvmr.download import DownloadManager, DownloadError, format_size


class TestDownloadManager:
    """Tests for DownloadManager class."""

    @pytest.fixture
    def manager(self):
        """Create a download manager with progress disabled."""
        return DownloadManager(show_progress=False)

    @pytest.fixture
    def temp_dir(self, tmp_path):
        """Create a temporary directory for downloads."""
        return tmp_path / "downloads"

    @patch("pyvmr.download.requests.get")
    def test_download_success(self, mock_get, manager, temp_dir):
        """Test successful file download."""
        # Mock response
        mock_response = MagicMock()
        mock_response.headers = {"content-length": "100"}
        mock_response.status_code = 200
        mock_response.iter_content.return_value = [b"x" * 100]
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        output_path = temp_dir / "test.zip"
        result = manager.download(
            url="https://example.com/test.zip",
            output_path=output_path,
        )

        assert result == output_path
        assert output_path.exists()

    @patch("pyvmr.download.requests.get")
    def test_download_with_size_verification(self, mock_get, manager, temp_dir):
        """Test download with size verification."""
        mock_response = MagicMock()
        mock_response.headers = {"content-length": "100"}
        mock_response.status_code = 200
        mock_response.iter_content.return_value = [b"x" * 100]
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        output_path = temp_dir / "test.zip"
        result = manager.download(
            url="https://example.com/test.zip",
            output_path=output_path,
            expected_size=100,
        )

        assert result.exists()

    @patch("pyvmr.download.requests.get")
    def test_download_size_mismatch(self, mock_get, manager, temp_dir):
        """Test download fails on size mismatch."""
        mock_response = MagicMock()
        mock_response.headers = {"content-length": "50"}
        mock_response.status_code = 200
        mock_response.iter_content.return_value = [b"x" * 50]
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        output_path = temp_dir / "test.zip"

        with pytest.raises(DownloadError):
            manager.download(
                url="https://example.com/test.zip",
                output_path=output_path,
                expected_size=100,  # Expect 100 but get 50
            )

    @patch("pyvmr.download.requests.get")
    def test_download_retry_on_failure(self, mock_get, manager, temp_dir):
        """Test that download retries on failure."""
        import requests

        # First two calls raise exception, third succeeds
        mock_response_success = MagicMock()
        mock_response_success.headers = {"content-length": "10"}
        mock_response_success.status_code = 200
        mock_response_success.iter_content.return_value = [b"x" * 10]
        mock_response_success.raise_for_status = MagicMock()

        mock_get.side_effect = [
            requests.RequestException("Network error"),
            requests.RequestException("Network error"),
            mock_response_success,
        ]

        # Use a manager with short retry delay
        manager = DownloadManager(show_progress=False, retry_delay=0.01)

        output_path = temp_dir / "test.zip"
        result = manager.download(
            url="https://example.com/test.zip",
            output_path=output_path,
        )

        assert result.exists()
        assert mock_get.call_count == 3

    @patch("pyvmr.download.requests.get")
    def test_download_max_retries_exceeded(self, mock_get, temp_dir):
        """Test that download fails after max retries."""
        import requests

        mock_get.side_effect = requests.RequestException("Network error")

        manager = DownloadManager(show_progress=False, max_retries=2, retry_delay=0.01)

        output_path = temp_dir / "test.zip"

        with pytest.raises(DownloadError) as exc_info:
            manager.download(
                url="https://example.com/test.zip",
                output_path=output_path,
            )

        assert "2 attempts" in str(exc_info.value)

    @patch("pyvmr.download.requests.head")
    def test_get_file_info(self, mock_head, manager):
        """Test getting file info without downloading."""
        mock_response = MagicMock()
        mock_response.headers = {
            "content-length": "1000",
            "content-type": "application/zip",
            "accept-ranges": "bytes",
        }
        mock_response.raise_for_status = MagicMock()
        mock_head.return_value = mock_response

        info = manager.get_file_info("https://example.com/test.zip")

        assert info["size"] == 1000
        assert info["content_type"] == "application/zip"
        assert info["accepts_ranges"] is True


class TestFormatSize:
    """Tests for format_size function."""

    def test_bytes(self):
        """Test formatting bytes."""
        assert format_size(500) == "500.0 B"

    def test_kilobytes(self):
        """Test formatting kilobytes."""
        assert format_size(1024) == "1.0 KB"
        assert format_size(1536) == "1.5 KB"

    def test_megabytes(self):
        """Test formatting megabytes."""
        assert format_size(1024 * 1024) == "1.0 MB"
        assert format_size(1024 * 1024 * 100) == "100.0 MB"

    def test_gigabytes(self):
        """Test formatting gigabytes."""
        assert format_size(1024 * 1024 * 1024) == "1.0 GB"

    def test_terabytes(self):
        """Test formatting terabytes."""
        assert format_size(1024 * 1024 * 1024 * 1024) == "1.0 TB"
