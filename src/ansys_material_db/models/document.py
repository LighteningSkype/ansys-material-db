"""Document and TextChunk data models for knowledge base."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class TextChunk:
    """A chunk of text extracted from a document, used for embedding/search."""

    id: Optional[int] = None
    document_id: Optional[int] = None
    chunk_index: int = 0
    page_number: int = 0
    text: str = ""
    embedding: Optional[list[float]] = None
    source_file: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "document_id": self.document_id,
            "chunk_index": self.chunk_index,
            "page_number": self.page_number,
            "text": self.text,
            "embedding": self.embedding,
            "source_file": self.source_file,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TextChunk:
        return cls(
            id=data.get("id"),
            document_id=data.get("document_id"),
            chunk_index=data.get("chunk_index", 0),
            page_number=data.get("page_number", 0),
            text=data.get("text", ""),
            embedding=data.get("embedding"),
            source_file=data.get("source_file", ""),
        )


@dataclass
class Document:
    """A source document (PDF/image) imported into the knowledge base."""

    id: Optional[int] = None
    filename: str = ""
    file_path: str = ""
    file_type: str = ""  # "pdf", "image", etc.
    page_count: int = 0
    status: str = "pending"  # "pending", "processing", "completed", "extraction_failed"
    text_content: str = ""
    chunks: list[TextChunk] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "filename": self.filename,
            "file_path": self.file_path,
            "file_type": self.file_type,
            "page_count": self.page_count,
            "status": self.status,
            "text_content": self.text_content,
            "chunks": [c.to_dict() for c in self.chunks],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Document:
        return cls(
            id=data.get("id"),
            filename=data.get("filename", ""),
            file_path=data.get("file_path", ""),
            file_type=data.get("file_type", ""),
            page_count=data.get("page_count", 0),
            status=data.get("status", "pending"),
            text_content=data.get("text_content", ""),
            chunks=[TextChunk.from_dict(c) for c in data.get("chunks", [])],
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
        )