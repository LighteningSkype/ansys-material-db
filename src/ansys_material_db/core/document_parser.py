"""PDF and image text extraction with chunking."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Optional

import fitz  # PyMuPDF
import pytesseract
from PIL import Image

from ansys_material_db.models.document import TextChunk

logger = logging.getLogger(__name__)

_OVERLAP_RATIO = 0.15


class DocumentParser:
    """Extract text from PDF and image documents, then chunk for downstream use."""

    # ------------------------------------------------------------------
    # PDF parsing
    # ------------------------------------------------------------------

    def parse_pdf(
        self,
        file_path: str | Path,
        page_range: Optional[tuple[int, int]] = None,
    ) -> list[TextChunk]:
        """Extract text from a PDF file.

        Parameters
        ----------
        file_path:
            Path to the PDF file.
        page_range:
            Optional ``(start, end)`` 1-based inclusive page range.
            ``None`` means all pages.

        Returns
        -------
        list[TextChunk]
            Extracted and chunked text segments.
        """
        file_path = Path(file_path)
        if not file_path.exists():
            logger.warning("PDF file not found: %s", file_path)
            return []

        try:
            doc = fitz.open(str(file_path))
        except Exception:
            logger.exception("Failed to open PDF: %s", file_path)
            return []

        if doc.page_count == 0:
            logger.info("PDF has no pages: %s", file_path)
            doc.close()
            return []

        start, end = self._resolve_page_range(page_range, doc.page_count)
        all_chunks: list[TextChunk] = []

        for page_idx in range(start - 1, end):
            page = doc[page_idx]
            raw_text = page.get_text("text") or ""
            page_number = page_idx + 1  # 1-based
            cleaned = self._clean_text(raw_text)
            if cleaned:
                chunks = self.chunk_text(cleaned, page_number, file_path=str(file_path))
                all_chunks.extend(chunks)

        doc.close()
        return all_chunks

    # ------------------------------------------------------------------
    # Image / OCR parsing
    # ------------------------------------------------------------------

    def parse_image(self, file_path: str | Path) -> list[TextChunk]:
        """OCR an image file and return chunked text.

        Parameters
        ----------
        file_path:
            Path to an image file (PNG, JPEG, TIFF, ...).

        Returns
        -------
        list[TextChunk]
            Extracted and chunked text segments.
        """
        file_path = Path(file_path)
        if not file_path.exists():
            logger.warning("Image file not found: %s", file_path)
            return []

        try:
            img = Image.open(str(file_path))
        except Exception:
            logger.exception("Failed to open image: %s", file_path)
            return []

        try:
            raw_text = pytesseract.image_to_string(img)
        except Exception:
            logger.exception("OCR failed for image: %s", file_path)
            return []
        finally:
            img.close()

        cleaned = self._clean_text(raw_text)
        if not cleaned:
            return []

        return self.chunk_text(cleaned, page_number=1, file_path=str(file_path))

    # ------------------------------------------------------------------
    # Text chunking
    # ------------------------------------------------------------------

    def chunk_text(
        self,
        text: str,
        page_number: int,
        chunk_size: int = 500,
        file_path: str = "",
    ) -> list[TextChunk]:
        """Split text into overlapping chunks.

        Parameters
        ----------
        text:
            Cleaned body text.
        page_number:
            Source page number (1-based).
        chunk_size:
            Target character count per chunk.
        file_path:
            Original file path for provenance.

        Returns
        -------
        list[TextChunk]
        """
        text = text.strip()
        if not text:
            return []

        if len(text) <= chunk_size:
            return [
                TextChunk(
                    text=text,
                    page_number=page_number,
                    source_file=file_path,
                    chunk_index=0,
                )
            ]

        overlap = max(1, int(chunk_size * _OVERLAP_RATIO))
        step = chunk_size - overlap
        chunks: list[TextChunk] = []
        idx = 0
        start = 0

        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunk = TextChunk(
                text=text[start:end],
                page_number=page_number,
                source_file=file_path,
                chunk_index=idx,
            )
            chunks.append(chunk)
            idx += 1
            start += step
            if start >= len(text):
                break

        return chunks

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _clean_text(text: str) -> str:
        """Normalize whitespace and strip common header/footer artefacts."""
        # Collapse runs of whitespace (but preserve single newlines for structure)
        text = re.sub(r"[^\S\n]+", " ", text)
        # Collapse 3+ consecutive newlines into 2
        text = re.sub(r"\n{3,}", "\n\n", text)
        # Strip lines that are mostly digits (page numbers)
        text = re.sub(r"^\s*\d{1,5}\s*$", "", text, flags=re.MULTILINE)
        # Strip common header/footer patterns
        text = re.sub(
            r"^(?:confidential|proprietary|copyright|\s*©).*$",
            "",
            text,
            flags=re.IGNORECASE | re.MULTILINE,
        )
        return text.strip()

    @staticmethod
    def _resolve_page_range(
        page_range: Optional[tuple[int, int]],
        total_pages: int,
    ) -> tuple[int, int]:
        if page_range is None:
            return (1, total_pages)
        start = max(1, page_range[0])
        end = min(total_pages, page_range[1])
        if start > end:
            return (1, total_pages)
        return (start, end)