from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class RetrievedChunk:
    source_id: str
    title: str
    text: str
    score: float


class Retriever(Protocol):
    def search(self, query: str, *, limit: int = 5) -> list[RetrievedChunk]: ...


class NullRetriever:
    def search(self, query: str, *, limit: int = 5) -> list[RetrievedChunk]:
        del query, limit
        return []


class ChromaRetriever:
    """Lazy Chroma adapter so unit tests do not require the optional dependency."""

    def __init__(self, *, host: str, port: int, collection_name: str) -> None:
        try:
            import chromadb
        except ImportError as exc:  # pragma: no cover - optional production dependency
            raise RuntimeError("Install chromadb to enable RAG") from exc
        self._client = chromadb.HttpClient(host=host, port=port)
        self._collection = self._client.get_or_create_collection(collection_name)

    def search(self, query: str, *, limit: int = 5) -> list[RetrievedChunk]:
        result = self._collection.query(query_texts=[query], n_results=limit)
        documents = (result.get("documents") or [[]])[0]
        ids = (result.get("ids") or [[]])[0]
        distances = (result.get("distances") or [[]])[0]
        metadatas = (result.get("metadatas") or [[]])[0]
        chunks: list[RetrievedChunk] = []
        for index, text in enumerate(documents):
            metadata = metadatas[index] if index < len(metadatas) else {}
            distance = distances[index] if index < len(distances) else 1.0
            chunks.append(
                RetrievedChunk(
                    source_id=ids[index],
                    title=str(metadata.get("title", "Documento técnico")),
                    text=text,
                    score=max(0.0, 1.0 - float(distance)),
                )
            )
        return chunks
