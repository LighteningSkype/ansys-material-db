"""ChatMessage data model for the Q&A interface."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class ChatMessage:
    """A single message in the Q&A chat panel."""

    id: Optional[int] = None
    role: str = "user"  # "user" or "assistant"
    content: str = ""
    sources: list[str] = field(default_factory=list)  # source document references
    created_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "role": self.role,
            "content": self.content,
            "sources": self.sources,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ChatMessage:
        return cls(
            id=data.get("id"),
            role=data.get("role", "user"),
            content=data.get("content", ""),
            sources=data.get("sources", []),
            created_at=data.get("created_at", ""),
        )