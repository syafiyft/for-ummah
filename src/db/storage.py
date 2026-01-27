"""
Storage service for PDF files using Supabase Storage.
Handles upload, download, and signed URL generation.
"""

import logging
from pathlib import Path
from functools import lru_cache

from src.core import settings
from src.db.client import get_supabase_client, is_supabase_configured

logger = logging.getLogger(__name__)

# Local cache directory for downloaded PDFs
CACHE_DIR = Path("data/.cache")


class StorageService:
    """
    Service for managing PDF files in Supabase Storage.

    Storage structure:
        {bucket}/{source}/{filename}.pdf
        - shariah-documents/bnm/document1.pdf
        - shariah-documents/sc_malaysia/resolution.pdf
        - shariah-documents/manual/uploaded.pdf
    """

    def __init__(self):
        self.bucket = settings.pdf_storage_bucket
        self._client = None

    @property
    def client(self):
        """Lazy-load Supabase client."""
        if self._client is None:
            self._client = get_supabase_client()
        return self._client

    @property
    def storage(self):
        """Get storage interface."""
        return self.client.storage.from_(self.bucket)

    def _get_storage_path(self, source: str, filename: str) -> str:
        """
        Generate storage path for a file.

        Args:
            source: Source category (e.g., 'bnm', 'manual')
            filename: PDF filename

        Returns:
            Storage path (e.g., 'bnm/document.pdf')
        """
        # Ensure .pdf extension
        if not filename.lower().endswith('.pdf'):
            filename = f"{filename}.pdf"
        return f"{source.lower()}/{filename}"

    def upload_pdf(
        self,
        file_content: bytes,
        source: str,
        filename: str,
        upsert: bool = True
    ) -> str:
        """
        Upload a PDF file to Supabase Storage.

        Args:
            file_content: PDF file bytes
            source: Source category (e.g., 'bnm', 'manual')
            filename: PDF filename
            upsert: If True, overwrite existing file

        Returns:
            Storage path of uploaded file

        Raises:
            Exception: If upload fails
        """
        storage_path = self._get_storage_path(source, filename)

        logger.info(f"Uploading to storage: {storage_path}")

        # Upload with upsert option
        options = {"upsert": "true"} if upsert else {}
        result = self.storage.upload(
            path=storage_path,
            file=file_content,
            file_options={"content-type": "application/pdf", **options}
        )

        logger.info(f"Upload complete: {storage_path}")
        return storage_path

    def upload_pdf_from_path(
        self,
        file_path: Path,
        source: str,
        filename: str | None = None,
        upsert: bool = True
    ) -> str:
        """
        Upload a PDF file from local path to Supabase Storage.

        Args:
            file_path: Path to local PDF file
            source: Source category
            filename: Optional custom filename (defaults to file_path.name)
            upsert: If True, overwrite existing file

        Returns:
            Storage path of uploaded file
        """
        if filename is None:
            filename = file_path.name

        content = file_path.read_bytes()
        return self.upload_pdf(content, source, filename, upsert)

    def download_pdf(self, storage_path: str, use_cache: bool = True) -> bytes:
        """
        Download a PDF file from Supabase Storage.

        Args:
            storage_path: Path in storage (e.g., 'bnm/document.pdf')
            use_cache: If True, use local cache

        Returns:
            PDF file bytes
        """
        # Check cache first
        if use_cache:
            cache_path = CACHE_DIR / storage_path
            if cache_path.exists():
                logger.debug(f"Cache hit: {storage_path}")
                return cache_path.read_bytes()

        logger.info(f"Downloading from storage: {storage_path}")
        result = self.storage.download(storage_path)

        # Cache the file locally
        if use_cache:
            cache_path = CACHE_DIR / storage_path
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_bytes(result)
            logger.debug(f"Cached: {storage_path}")

        return result

    def download_pdf_to_path(
        self,
        storage_path: str,
        local_path: Path,
        use_cache: bool = True
    ) -> Path:
        """
        Download a PDF file to a local path.

        Args:
            storage_path: Path in storage
            local_path: Local destination path
            use_cache: If True, use local cache

        Returns:
            Path to downloaded file
        """
        content = self.download_pdf(storage_path, use_cache)
        local_path.parent.mkdir(parents=True, exist_ok=True)
        local_path.write_bytes(content)
        return local_path

    def get_signed_url(self, storage_path: str, expires_in: int = 3600) -> str:
        """
        Generate a signed URL for direct PDF access.

        Args:
            storage_path: Path in storage
            expires_in: URL expiration time in seconds (default: 1 hour)

        Returns:
            Signed URL for the PDF
        """
        result = self.storage.create_signed_url(storage_path, expires_in)
        return result.get("signedURL") or result.get("signedUrl")

    def get_public_url(self, storage_path: str) -> str:
        """
        Get the public URL for a file (if bucket is public).

        Args:
            storage_path: Path in storage

        Returns:
            Public URL for the PDF
        """
        result = self.storage.get_public_url(storage_path)
        return result

    def delete_pdf(self, storage_path: str) -> bool:
        """
        Delete a PDF from storage.

        Args:
            storage_path: Path in storage

        Returns:
            True if deletion was successful
        """
        logger.info(f"Deleting from storage: {storage_path}")
        result = self.storage.remove([storage_path])

        # Clear cache
        cache_path = CACHE_DIR / storage_path
        if cache_path.exists():
            cache_path.unlink()

        return True

    def list_pdfs(self, source: str | None = None) -> list[dict]:
        """
        List all PDFs in storage.

        Args:
            source: Optional source to filter by

        Returns:
            List of file metadata dicts
        """
        path = source.lower() if source else ""
        result = self.storage.list(path)
        return result

    def file_exists(self, storage_path: str) -> bool:
        """
        Check if a file exists in storage.

        Args:
            storage_path: Path in storage

        Returns:
            True if file exists
        """
        try:
            # List the parent directory and check for the file
            parts = storage_path.rsplit('/', 1)
            if len(parts) == 2:
                folder, filename = parts
            else:
                folder, filename = "", parts[0]

            files = self.storage.list(folder)
            return any(f.get('name') == filename for f in files)
        except Exception:
            return False

    def clear_cache(self, storage_path: str | None = None):
        """
        Clear local cache.

        Args:
            storage_path: Specific file to clear, or None to clear all
        """
        if storage_path:
            cache_path = CACHE_DIR / storage_path
            if cache_path.exists():
                cache_path.unlink()
        else:
            import shutil
            if CACHE_DIR.exists():
                shutil.rmtree(CACHE_DIR)
                CACHE_DIR.mkdir(parents=True, exist_ok=True)


# Convenience function
def get_storage_service() -> StorageService:
    """Get a StorageService instance."""
    return StorageService()
