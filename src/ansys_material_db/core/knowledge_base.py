"""Knowledge base orchestration: document import, chunking, embedding, and semantic search."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Callable, Optional

from ansys_material_db.core.document_parser import DocumentParser
from ansys_material_db.data.database import SQLiteManager
from ansys_material_db.data.embeddings import EmbeddingService
from ansys_material_db.models.document import Document, TextChunk

logger = logging.getLogger(__name__)

# Supported file extensions
_IMAGE_EXTENSIONS = frozenset({".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp", ".gif"})
_PDF_EXTENSIONS = frozenset({".pdf"})

# Type alias for progress callbacks: (current_step: str, progress: float, total: float) -> None
ProgressCallback = Callable[[str, float, float], None]


class KnowledgeBaseManager:
    """Orchestrates document import, chunking, embedding, and semantic search.

    Coordinates :class:DocumentParser, :class:EmbeddingService, and
    :class:SQLiteManager to provide a single entry point for managing
    the knowledge base lifecycle.

    Parameters
    ----------
    database:
        SQLite manager for persistent storage.
    document_parser:
        PDF/image text extractor and chunker.
    embedding_service:
        Text embedding generator (local or API).
    """

    def __init__(
        self,
        database: SQLiteManager,
        document_parser: DocumentParser,
        embedding_service: EmbeddingService,
    ) -> None:
        self.database = database
        self.document_parser = document_parser
        self.embedding_service = embedding_service

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def import_document(
        self,
        file_path: str,
        supplier: str = "",
        page_range: Optional[tuple[int, int]] = None,
        progress_callback: Optional[ProgressCallback] = None,
        deferred: bool = False,
    ) -> dict[str, Any]:
        """Import a document into the knowledge base.

        When *deferred* is `False` (default), runs the full pipeline:
        parse -> chunk -> embed -> store.  When `True`, only parses the
        text and stores the document with status `"pending"` — no chunking
        or embedding is performed.

        Parameters
        ----------
        file_path:
            Path to the PDF or image file.
        supplier:
            Material supplier / manufacturer name.
        page_range:
            Optional `(start, end)` 1-based inclusive page range for PDFs.
        progress_callback:
            Optional callback `(step, current, total)` for progress updates.
        deferred:
            If `True`, store parsed text only (no vectorization).

        Returns
        -------
        dict
            Summary with keys `document_id`, `chunk_count`, `status`.
            On duplicate detection `status` is `"skipped"`.
        """
        path = Path(file_path)
        result: dict[str, Any] = {
            "document_id": None,
            "chunk_count": 0,
            "status": "pending",
        }

        # --- Validate file exists ---
        if not path.exists():
            logger.error("File not found: %s", file_path)
            result["status"] = "error"
            result["error"] = f"File not found: {file_path}"
            return result

        # --- Duplicate detection ---
        if self._is_duplicate(str(path.resolve())):
            logger.info("Duplicate document skipped: %s", file_path)
            result["status"] = "skipped"
            result["error"] = "Document already imported"
            return result

        # --- Determine file type ---
        suffix = path.suffix.lower()
        if suffix in _PDF_EXTENSIONS:
            file_type = "pdf"
        elif suffix in _IMAGE_EXTENSIONS:
            file_type = "image"
        else:
            logger.error("Unsupported file type: %s", suffix)
            result["status"] = "error"
            result["error"] = f"Unsupported file type: {suffix}"
            return result

        # --- Step 1: Parse document ---
        if progress_callback:
            progress_callback("parsing", 0.0, 3.0)

        doc = Document(
            filename=path.name,
            file_path=str(path.resolve()),
            file_type=file_type,
            status="processing",
        )

        try:
            if file_type == "pdf":
                chunks = self.document_parser.parse_pdf(
                    str(path), page_range=page_range
                )
                doc.page_count = self._count_pdf_pages(str(path), page_range)
            else:
                chunks = self.document_parser.parse_image(str(path))
                doc.page_count = 1
        except Exception as exc:
            logger.exception("Failed to parse document: %s", file_path)
            doc.status = "extraction_failed"
            document_id = self._store_document(doc)
            result["document_id"] = document_id
            result["status"] = "extraction_failed"
            result["error"] = str(exc)
            if progress_callback:
                progress_callback("failed", 3.0, 3.0)
            return result

        if progress_callback:
            progress_callback("parsing", 1.0, 3.0)

        # --- Deferred mode: store text only, skip vectorization ---
        if deferred:
            doc.text_content = "\n".join(c.text for c in chunks) if chunks else ""
            doc.chunks = []
            doc.status = "pending"
            document_id = self._store_document(doc)
            result["document_id"] = document_id
            result["chunk_count"] = 0
            result["status"] = "pending"
            if progress_callback:
                progress_callback("done", 3.0, 3.0)
            return result

        if not chunks:
            logger.warning("No text extracted from document: %s", file_path)
            doc.status = "completed"
            document_id = self._store_document(doc)
            result["document_id"] = document_id
            result["chunk_count"] = 0
            result["status"] = "completed"
            if progress_callback:
                progress_callback("done", 3.0, 3.0)
            return result

        doc.chunks = chunks
        doc.text_content = "\n".join(c.text for c in chunks)

        # --- Step 2: Embed chunks ---
        if progress_callback:
            progress_callback("embedding", 1.0, 3.0)

        try:
            texts = [c.text for c in chunks]
            embeddings = self.embedding_service.embed_batch(texts)
            for chunk, emb in zip(chunks, embeddings):
                chunk.embedding = emb
        except Exception as exc:
            logger.exception("Embedding failed for document: %s", file_path)
            doc.status = "extraction_failed"
            document_id = self._store_document(doc)
            result["document_id"] = document_id
            result["status"] = "extraction_failed"
            result["error"] = str(exc)
            if progress_callback:
                progress_callback("failed", 3.0, 3.0)
            return result

        if progress_callback:
            progress_callback("embedding", 2.0, 3.0)

        # --- Step 3: Store in database ---
        doc.status = "completed"
        document_id = self._store_document(doc)

        if progress_callback:
            progress_callback("storing", 3.0, 3.0)

        result["document_id"] = document_id
        result["chunk_count"] = len(chunks)
        result["status"] = "completed"
        return result

    async def vectorize_document(
        self,
        document_id: int,
        progress_callback: Optional[ProgressCallback] = None,
    ) -> dict[str, Any]:
        """Chunk and embed a previously imported document.

        If already vectorized (has chunks), replaces existing chunks.

        Parameters
        ----------
        document_id:
            Database id of the document to vectorize.
        progress_callback:
            Optional callback `(step, current, total)` for progress updates.

        Returns
        -------
        dict
            Summary with keys `chunk_count`, `status`.
        """
        result: dict[str, Any] = {"chunk_count": 0, "status": "error"}

        doc = self.database.get_document(document_id)
        if doc is None:
            result["error"] = f"Document {document_id} not found"
            return result

        # --- Step 1: Parse text from file if text_content is empty ---
        if progress_callback:
            progress_callback("parsing", 0.0, 3.0)

        text_content = doc.text_content or ""
        if not text_content:
            # Re-parse from file
            file_path = Path(doc.file_path)
            if not file_path.exists():
                result["error"] = f"Source file not found: {doc.file_path}"
                return result

            try:
                if doc.file_type == "pdf":
                    chunks = self.document_parser.parse_pdf(doc.file_path)
                else:
                    chunks = self.document_parser.parse_image(doc.file_path)
                text_content = "\n".join(c.text for c in chunks)
            except Exception as exc:
                logger.exception("Failed to parse document %d", document_id)
                doc.status = "extraction_failed"
                self.database.update_document(doc)
                result["error"] = str(exc)
                return result
        else:
            # We have text_content but need to re-chunk from it
            chunks = self.document_parser.chunk_text(
                text_content, page_number=1, file_path=doc.file_path
            )

        if not chunks:
            logger.warning("No text to vectorize for document %d", document_id)
            doc.status = "vectorized"
            self.database.update_document(doc)
            result["chunk_count"] = 0
            result["status"] = "vectorized"
            return result

        if progress_callback:
            progress_callback("parsing", 1.0, 3.0)

        # --- Step 2: Embed chunks ---
        if progress_callback:
            progress_callback("embedding", 1.0, 3.0)

        try:
            texts = [c.text for c in chunks]
            embeddings = self.embedding_service.embed_batch(texts)
            for chunk, emb in zip(chunks, embeddings):
                chunk.embedding = emb
        except Exception as exc:
            logger.exception("Embedding failed for document %d", document_id)
            doc.status = "extraction_failed"
            self.database.update_document(doc)
            result["error"] = str(exc)
            return result

        if progress_callback:
            progress_callback("embedding", 2.0, 3.0)

        # --- Step 3: Replace existing chunks and store ---
        self.database.delete_document_chunks(document_id)
        doc.chunks = chunks
        doc.text_content = text_content
        doc.status = "vectorized"
        self.database.add_chunks(document_id, chunks)
        self.database.update_document(doc)

        if progress_callback:
            progress_callback("storing", 3.0, 3.0)

        result["chunk_count"] = len(chunks)
        result["status"] = "vectorized"
        return result

    async def extract_properties_from_document(
        self,
        document_id: int,
        llm_client: Any,
        progress_callback: Optional[ProgressCallback] = None,
    ) -> dict[str, Any]:
        """Extract material properties from a document using LLM.

        Requires the document to have `text_content` populated.

        Parameters
        ----------
        document_id:
            Database id of the document.
        llm_client:
            LLM client instance for extraction.
        progress_callback:
            Optional callback `(step, current, total)` for progress updates.

        Returns
        -------
        dict
            Summary with keys `materials_found`, `material_ids`, `status`.
        """
        result: dict[str, Any] = {
            "materials_found": 0,
            "material_ids": [],
            "status": "error",
        }

        doc = self.database.get_document(document_id)
        if doc is None:
            result["error"] = f"Document {document_id} not found"
            return result

        text_content = doc.text_content or ""

        if progress_callback:
            progress_callback("extracting", 0.0, 2.0)

        try:
            from ansys_material_db.core.property_extractor import PropertyExtractor

            extractor = PropertyExtractor(llm_client)

            # For image files, use multimodal (send image directly to LLM)
            if doc.file_type == "image" and Path(doc.file_path).exists():
                logger.info("Using multimodal extraction for image: %s", doc.file_path)
                materials = await extractor.extract_from_image([doc.file_path])
            elif text_content.strip():
                materials = await extractor.extract_from_text(text_content)
            else:
                # Try to get text from document first
                text_content = self.get_document_text(document_id)
                if text_content.strip():
                    materials = await extractor.extract_from_text(text_content)
                else:
                    result["error"] = "No text or recognizable content to extract from"
                    return result
        except Exception as exc:
            logger.exception("Property extraction failed for document %d", document_id)
            doc.status = "extraction_failed"
            self.database.update_document(doc)
            result["error"] = str(exc)
            return result

        if progress_callback:
            progress_callback("storing", 1.0, 2.0)

        # Save extracted materials to database
        material_ids: list[int] = []
        for mat in materials:
            mat.source_document_id = document_id
            mat_id = self.database.add_material(mat)
            material_ids.append(mat_id)

        doc.status = "completed"
        self.database.update_document(doc)

        if progress_callback:
            progress_callback("done", 2.0, 2.0)

        result["materials_found"] = len(materials)
        result["material_ids"] = material_ids
        result["status"] = "completed"
        return result

    def get_document_text(self, document_id: int) -> str:
        """Get the text content of a document.

        Returns stored `text_content` if available, otherwise re-parses
        from `file_path` and stores the result.
        """
        doc = self.database.get_document(document_id)
        if doc is None:
            return ""

        if doc.text_content:
            return doc.text_content

        # Re-parse from file
        file_path = Path(doc.file_path)
        if not file_path.exists():
            logger.warning(
                "get_document_text: text_content empty and source file not found: %s",
                doc.file_path,
            )
            return ""

        try:
            if doc.file_type == "pdf":
                chunks = self.document_parser.parse_pdf(doc.file_path)
            else:
                chunks = self.document_parser.parse_image(doc.file_path)
            text_content = "\n".join(c.text for c in chunks)
        except Exception:
            logger.exception("Failed to re-parse document %d", document_id)
            return ""

        # Store for future use
        doc.text_content = text_content
        self.database.update_document(doc)
        return text_content

    def search(
        self, query: str, top_k: int = 5
    ) -> list[tuple[TextChunk, float]]:
        """Semantic search across the knowledge base.

        Parameters
        ----------
        query:
            Natural-language search query.
        top_k:
            Maximum number of results to return.

        Returns
        -------
        list[tuple[TextChunk, float]]
            Pairs of (chunk, similarity_score) ordered by relevance.
        """
        if not query or not query.strip():
            return []

        query_embedding = self.embedding_service.embed_text(query)
        chunks = self.database.search_chunks(query_embedding, top_k=top_k)

        results: list[tuple[TextChunk, float]] = []
        for chunk in chunks:
            score = getattr(chunk, "similarity_score", 0.0)
            results.append((chunk, score))
        return results

    def delete_document(self, document_id: int) -> None:
        """Remove a document and all its associated chunks.

        Parameters
        ----------
        document_id:
            Database id of the document to remove.
        """
        # Foreign key ON DELETE CASCADE handles chunk removal
        conn = self.database.conn
        conn.execute("DELETE FROM text_chunks WHERE document_id = ?", (document_id,))
        conn.execute("DELETE FROM documents WHERE id = ?", (document_id,))
        conn.commit()

    def get_document_info(self, document_id: int) -> dict[str, Any]:
        """Get document metadata and associated chunk count.

        Parameters
        ----------
        document_id:
            Database id of the document.

        Returns
        -------
        dict
            Document metadata including `chunk_count`.
            Returns empty dict if document not found.
        """
        doc = self.database.get_document(document_id)
        if doc is None:
            return {}

        chunk_count = self.database.conn.execute(
            "SELECT COUNT(*) as cnt FROM text_chunks WHERE document_id = ?",
            (document_id,),
        ).fetchone()["cnt"]

        return {
            "id": doc.id,
            "filename": doc.filename,
            "file_path": doc.file_path,
            "file_type": doc.file_type,
            "page_count": doc.page_count,
            "status": doc.status,
            "chunk_count": chunk_count,
            "imported_at": doc.created_at,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _is_duplicate(self, resolved_path: str) -> bool:
        """Check if a document with the same resolved file path already exists."""
        existing = self.database.list_documents()
        for doc in existing:
            if doc.file_path and os.path.normpath(doc.file_path) == os.path.normpath(resolved_path):
                return True
        return False

    def _store_document(self, doc: Document) -> int:
        """Persist a document and its chunks, returning the document id.

        The document is inserted/updated via the database manager, and
        chunks are bulk-inserted via :py:meth:SQLiteManager.add_chunks.
        """
        document_id = self.database.add_document(doc)
        if doc.chunks:
            self.database.add_chunks(document_id, doc.chunks)
        return document_id

    @staticmethod
    def _count_pdf_pages(
        file_path: str,
        page_range: Optional[tuple[int, int]] = None,
    ) -> int:
        """Count pages in a PDF, optionally restricted to a page range."""
        try:
            import fitz  # PyMuPDF

            doc = fitz.open(file_path)
            total = doc.page_count
            doc.close()
            if page_range is None:
                return total
            start = max(1, page_range[0])
            end = min(total, page_range[1])
            return max(0, end - start + 1)
        except Exception:
            logger.warning("Could not count PDF pages: %s", file_path)
            return 0