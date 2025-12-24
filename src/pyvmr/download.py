"""Download manager for VMR files."""

import os
import time
import zipfile
from pathlib import Path
from typing import Callable, List, Optional, Union

import requests
from tqdm import tqdm

from .constants import (
    DEFAULT_CHUNK_SIZE,
    DEFAULT_TIMEOUT,
    MAX_RETRIES,
    RETRY_DELAY,
)


class DownloadError(Exception):
    """Exception raised when a download fails."""
    pass


class DownloadManager:
    """Manages file downloads from the VMR with progress tracking."""

    def __init__(
        self,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        timeout: int = DEFAULT_TIMEOUT,
        max_retries: int = MAX_RETRIES,
        retry_delay: float = RETRY_DELAY,
        show_progress: bool = True,
    ):
        """Initialize the download manager.

        Args:
            chunk_size: Size of download chunks in bytes
            timeout: HTTP request timeout in seconds
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
            show_progress: Whether to show progress bars
        """
        self.chunk_size = chunk_size
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.show_progress = show_progress

    def download(
        self,
        url: str,
        output_path: Union[str, Path],
        expected_size: Optional[int] = None,
        description: Optional[str] = None,
        extract: bool = False,
        on_progress: Optional[Callable[[int, int], None]] = None,
    ) -> Path:
        """Download a file from URL.

        Args:
            url: URL to download from
            output_path: Path to save the file
            expected_size: Expected file size in bytes (for verification)
            description: Description for progress bar
            extract: If True, extract ZIP files after download
            on_progress: Optional callback for progress updates (bytes_downloaded, total_bytes)

        Returns:
            Path to the downloaded file (or extracted directory if extract=True)

        Raises:
            DownloadError: If download fails after all retries
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        last_error = None
        for attempt in range(self.max_retries):
            try:
                return self._download_with_progress(
                    url=url,
                    output_path=output_path,
                    expected_size=expected_size,
                    description=description,
                    extract=extract,
                    on_progress=on_progress,
                )
            except (requests.RequestException, IOError) as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))

        raise DownloadError(
            f"Failed to download {url} after {self.max_retries} attempts: {last_error}"
        )

    def _download_with_progress(
        self,
        url: str,
        output_path: Path,
        expected_size: Optional[int],
        description: Optional[str],
        extract: bool,
        on_progress: Optional[Callable[[int, int], None]],
    ) -> Path:
        """Download with progress tracking."""
        # Check for existing partial download
        temp_path = output_path.with_suffix(output_path.suffix + ".part")
        resume_pos = 0

        headers = {}
        if temp_path.exists():
            resume_pos = temp_path.stat().st_size
            headers["Range"] = f"bytes={resume_pos}-"

        response = requests.get(
            url,
            headers=headers,
            stream=True,
            timeout=self.timeout,
        )

        # Handle resume response
        if response.status_code == 416:
            # Range not satisfiable - file might be complete
            if temp_path.exists():
                temp_path.rename(output_path)
                return self._handle_extraction(output_path, extract)

        response.raise_for_status()

        # Get total size
        total_size = int(response.headers.get("content-length", 0))
        if response.status_code == 206:  # Partial content
            total_size += resume_pos
        elif expected_size:
            total_size = expected_size

        # Set up progress bar
        desc = description or output_path.name
        progress_bar = None
        if self.show_progress and total_size > 0:
            progress_bar = tqdm(
                total=total_size,
                initial=resume_pos,
                unit="B",
                unit_scale=True,
                unit_divisor=1024,
                desc=desc,
            )

        # Download to temp file
        mode = "ab" if resume_pos > 0 else "wb"
        bytes_downloaded = resume_pos

        try:
            with open(temp_path, mode) as f:
                for chunk in response.iter_content(chunk_size=self.chunk_size):
                    if chunk:
                        f.write(chunk)
                        bytes_downloaded += len(chunk)

                        if progress_bar:
                            progress_bar.update(len(chunk))

                        if on_progress:
                            on_progress(bytes_downloaded, total_size)

        finally:
            if progress_bar:
                progress_bar.close()

        # Verify size if expected
        if expected_size and bytes_downloaded != expected_size:
            raise DownloadError(
                f"Size mismatch: expected {expected_size}, got {bytes_downloaded}"
            )

        # Move temp file to final location
        temp_path.rename(output_path)

        return self._handle_extraction(output_path, extract)

    def _handle_extraction(self, file_path: Path, extract: bool) -> Path:
        """Handle ZIP extraction if requested."""
        if not extract or not file_path.suffix.lower() == ".zip":
            return file_path

        extract_dir = file_path.with_suffix("")

        if self.show_progress:
            print(f"Extracting {file_path.name}...")

        with zipfile.ZipFile(file_path, "r") as zf:
            zf.extractall(extract_dir)

        return extract_dir

    def download_batch(
        self,
        downloads: List[dict],
        output_dir: Union[str, Path],
        extract: bool = False,
        delay: float = 0.5,
        on_file_complete: Optional[Callable[[str, Path], None]] = None,
    ) -> List[Path]:
        """Download multiple files.

        Args:
            downloads: List of dicts with 'url', 'filename', and optional 'size' keys
            output_dir: Directory to save files
            extract: If True, extract ZIP files after download
            delay: Delay between downloads in seconds
            on_file_complete: Callback when each file completes (name, path)

        Returns:
            List of paths to downloaded files
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        results = []
        total = len(downloads)

        for i, dl in enumerate(downloads):
            url = dl["url"]
            filename = dl["filename"]
            expected_size = dl.get("size")

            output_path = output_dir / filename

            if self.show_progress:
                print(f"\n[{i + 1}/{total}] Downloading {filename}")

            try:
                result_path = self.download(
                    url=url,
                    output_path=output_path,
                    expected_size=expected_size,
                    extract=extract,
                )
                results.append(result_path)

                if on_file_complete:
                    on_file_complete(filename, result_path)

            except DownloadError as e:
                if self.show_progress:
                    print(f"  Error: {e}")
                results.append(None)

            # Delay between downloads to be respectful to server
            if i < total - 1 and delay > 0:
                time.sleep(delay)

        return results

    def get_file_info(self, url: str) -> dict:
        """Get file information from URL without downloading.

        Args:
            url: URL to check

        Returns:
            Dict with 'size', 'content_type', and 'accepts_ranges' keys
        """
        response = requests.head(url, timeout=self.timeout, allow_redirects=True)
        response.raise_for_status()

        return {
            "size": int(response.headers.get("content-length", 0)),
            "content_type": response.headers.get("content-type", ""),
            "accepts_ranges": response.headers.get("accept-ranges") == "bytes",
        }


def format_size(size_bytes: int) -> str:
    """Format byte size to human-readable string."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} PB"
