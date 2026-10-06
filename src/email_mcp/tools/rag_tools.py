"""RAG tools for Email MCP: semantic neural search and mailbox vector synchronization."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import structlog
from fastmcp import FastMCP

from email_mcp.rag import EmailIngestor, EmailVectorStore, embed_use_gpu

if TYPE_CHECKING:
    from email_mcp.server import EmailMCP

logger = structlog.get_logger(__name__)

_store: EmailVectorStore | None = None
_ingestor: EmailIngestor | None = None


def get_rag_store() -> EmailVectorStore:
    global _store
    if _store is None:
        _store = EmailVectorStore()
    return _store


def get_rag_ingestor() -> EmailIngestor:
    global _ingestor
    if _ingestor is None:
        _ingestor = EmailIngestor()
    return _ingestor


def register_rag_tools(mcp: FastMCP, server: EmailMCP) -> None:
    """Register RAG semantic search and synchronization tools."""

    # Real MCP hints (the old {"readonly": True} is not an MCP annotation and advertises nothing).
    _READ_ONLY = {"readOnlyHint": True, "openWorldHint": False}
    # sync writes only the local derived vector index (never the mailbox), but it reads from it.
    _SYNC = {"readOnlyHint": False, "destructiveHint": False, "openWorldHint": True}

    @mcp.tool(annotations=_READ_ONLY)
    async def email_rag(
        query: str,
        limit: int = 5,
        service: str | None = None,
        folder: str | None = None,
        min_score: float = 0.35,
    ) -> dict[str, Any]:
        """Perform natural-language semantic neural search across indexed emails.

        Unlike literal keyword searches, this tool matches conceptual meaning,
        questions, topics, and paraphrased details across email bodies and threads.

        ## Parameters
        - query: Natural-language question or topic (e.g. "invoice from cloud provider in March", "deadline discussed with Alex")
        - limit: Maximum number of matched passages to return (default: 5)
        - service: Filter to a specific email service account (optional)
        - folder: Filter to a specific mailbox folder like INBOX or Sent (optional)
        - min_score: Minimum relevance similarity score 0.0-1.0 (default: 0.35)

        ## Returns
        {success, query, count, results: [{email_id, subject, from, to, date, snippet, score, content}], message}
        """
        try:
            store = get_rag_store()
            results = store.search(
                query=query,
                limit=limit,
                service=service,
                folder=folder,
                min_score=min_score,
            )
            return {
                "success": True,
                "operation": "email_rag",
                "query": query,
                "count": len(results),
                "results": results,
                "message": (
                    f"Found {len(results)} relevant email passages for '{query}'."
                    if results
                    else f"No email passages met the similarity threshold ({min_score}) for '{query}'. Run sync_email_rag to update index."
                ),
            }
        except Exception as exc:
            logger.error("email_rag search failed", query=query, error=str(exc))
            return {
                "success": False,
                "operation": "email_rag",
                "error": str(exc),
                "message": f"Semantic search failed: {exc}",
            }

    @mcp.tool(annotations=_SYNC)
    async def sync_email_rag(
        service: str = "default",
        folder: str = "INBOX",
        limit: int = 100,
        full_reindex: bool = False,
    ) -> dict[str, Any]:
        """Synchronize an email folder into the local neural vector index.

        Indexes email message bodies and metadata into LanceDB.
        By default, runs incrementally: only newly arrived emails are vectorized.
        Set full_reindex=True to wipe and re-embed all messages from scratch.

        ## Parameters
        - service: Email service to index (default: "default")
        - folder: Mailbox folder to index (default: "INBOX")
        - limit: Maximum recent emails to check (default: 100)
        - full_reindex: If True, rebuilds the vector index for this folder (default: False)
        """
        if service not in server.services:
            return {
                "success": False,
                "operation": "sync_email_rag",
                "error": f"Service '{service}' not available",
            }

        svc = server.services[service]
        try:
            store = get_rag_store()
            ingestor = get_rag_ingestor()
            result = await ingestor.sweep_service_folder(
                service_obj=svc,
                service_name=service,
                folder=folder,
                vector_store=store,
                limit=limit,
                full_reindex=full_reindex,
            )
            return {
                "operation": "sync_email_rag",
                **result,
            }
        except Exception as exc:
            logger.error("sync_email_rag failed", service=service, folder=folder, error=str(exc))
            return {
                "success": False,
                "operation": "sync_email_rag",
                "error": str(exc),
                "message": f"Sync failed: {exc}",
            }

    @mcp.tool(annotations=_READ_ONLY)
    async def email_rag_stats() -> dict[str, Any]:
        """Retrieve statistics and health of the Email RAG vector store."""
        try:
            store = get_rag_store()
            return {
                "success": True,
                "operation": "email_rag_stats",
                "total_chunks": store.count_documents(),
                "storage_mb": store.get_storage_size_mb(),
                "indexed_services": store.list_indexed_services(),
                "embedding_model": store.model_name,
                "gpu_accelerated": embed_use_gpu(),
                "status": "healthy",
            }
        except Exception as exc:
            return {
                "success": False,
                "operation": "email_rag_stats",
                "error": str(exc),
            }
