"""Email MCP Neural RAG Module."""

from .fastembed_gpu import create_text_embedding, embed_use_gpu
from .ingestor import EmailIngestor
from .vector_store import EmailVectorStore

__all__ = [
    "EmailIngestor",
    "EmailVectorStore",
    "create_text_embedding",
    "embed_use_gpu",
]
