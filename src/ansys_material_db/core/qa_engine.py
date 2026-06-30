"""Retrieval-Augmented Generation Q&A engine."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from ansys_material_db.data.llm_client import LLMClient
from ansys_material_db.data.embeddings import EmbeddingService
from ansys_material_db.data.database import SQLiteManager
from ansys_material_db.models.document import TextChunk
from ansys_material_db.models.chat import ChatMessage

logger = logging.getLogger(__name__)

_PROMPT_TEMPLATE_PATH = (
    Path(__file__).resolve().parents[1]
    / "resources"
    / "prompts"
    / "qa_context.txt"
)

_EMPTY_KB_MESSAGE = (
    "The knowledge base is currently empty. "
    "Please import material documents first before asking questions."
)


class QAEngine:
    """RAG-based Q&A engine for material science questions."""

    def __init__(
        self,
        llm_client: LLMClient,
        embedding_service: EmbeddingService,
        database: SQLiteManager,
    ) -> None:
        self._llm = llm_client
        self._embeddings = embedding_service
        self._db = database
        self._prompt_template = self._load_prompt_template()

    async def ask(
        self,
        question: str,
        top_k: int = 5,
        conversation_history: Optional[list[ChatMessage]] = None,
    ) -> tuple[str, list[TextChunk]]:
        """Answer a question using RAG.

        Parameters
        ----------
        question:
            The user's question.
        top_k:
            Number of relevant chunks to retrieve.
        conversation_history:
            Optional prior messages for multi-turn context.

        Returns
        -------
        tuple[str, list[TextChunk]]
            The answer string and the source chunks used.
        """
        if not question or not question.strip():
            return "", []

        # 1. Retrieve relevant chunks via embedding similarity
        chunks = await self._retrieve_chunks(question, top_k)

        if not chunks:
            return _EMPTY_KB_MESSAGE, []

        # 2. Build context and prompt
        context = self._build_context(question, chunks)
        messages = self._build_qa_prompt(question, context, conversation_history)

        # 3. Generate answer
        answer = await self._llm.chat(messages)

        # 4. Append source citation block
        answer = self._append_source_citations(answer, chunks)

        return answer, chunks

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------

    async def _retrieve_chunks(self, query: str, top_k: int) -> list[TextChunk]:
        """Embed the query and retrieve the top-k most similar chunks."""
        try:
            query_embedding = self._embeddings.embed_text(query)
        except Exception:
            logger.exception("Failed to embed query")
            return []

        try:
            results = self._db.search_chunks(query_embedding, top_k=top_k)
        except Exception:
            logger.exception("Failed to search chunks in database")
            return []

        return results

    # ------------------------------------------------------------------
    # Context & prompt construction
    # ------------------------------------------------------------------

    def _build_context(self, question: str, chunks: list[TextChunk]) -> str:
        """Assemble retrieved chunks into a context string."""
        parts: list[str] = []
        for i, chunk in enumerate(chunks, 1):
            source = chunk.source_file or "unknown"
            page = chunk.page_number or "?"
            header = f"[Chunk {i} -- {source}, Page {page}]"
            parts.append(f"{header}\n{chunk.text}")
        return "\n\n".join(parts)

    def _build_qa_prompt(
        self,
        question: str,
        context: str,
        conversation_history: Optional[list[ChatMessage]] = None,
    ) -> list[dict[str, str]]:
        """Build the chat messages list for the LLM call."""
        system_message = self._prompt_template.replace("{context}", context).replace(
            "{question}", question
        )

        messages: list[dict[str, str]] = [
            {"role": "system", "content": system_message},
        ]

        # Append conversation history for multi-turn support
        if conversation_history:
            for msg in conversation_history[-10:]:  # Keep last 10 messages
                role = msg.role if hasattr(msg, "role") else "user"
                content = msg.content if hasattr(msg, "content") else str(msg)
                messages.append({"role": role, "content": content})

        # The actual user question
        messages.append({"role": "user", "content": question})

        return messages

    # ------------------------------------------------------------------
    # Source citations
    # ------------------------------------------------------------------

    @staticmethod
    def _append_source_citations(answer: str, chunks: list[TextChunk]) -> str:
        """Append a formatted source list to the answer."""
        if not chunks:
            return answer

        seen: set[str] = set()
        source_lines: list[str] = []

        for chunk in chunks:
            source = chunk.source_file or "unknown"
            page = chunk.page_number or "?"
            key = f"{source}|{page}"
            if key not in seen:
                seen.add(key)
                source_lines.append(f"- {source}, Page {page}")

        if source_lines:
            citation_block = "\n\n**Sources:**\n" + "\n".join(source_lines)
            return answer + citation_block

        return answer

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _load_prompt_template() -> str:
        try:
            return _PROMPT_TEMPLATE_PATH.read_text(encoding="utf-8")
        except FileNotFoundError:
            logger.warning(
                "QA prompt template not found at %s, using fallback",
                _PROMPT_TEMPLATE_PATH,
            )
            return (
                "Answer the following question using the provided context.\n"
                "Cite your sources.\n\n"
                "Context:\n{context}\n\n"
                "Question:\n{question}"
            )