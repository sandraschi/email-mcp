"""LanceDB Vector Store for Email MCP RAG."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import lancedb

from .fastembed_gpu import DEFAULT_EMBED_MODEL, create_text_embedding, repo_root_from_here

logger = logging.getLogger(__name__)


def _sql_literal(value: str) -> str:
    """Single-quoted SQL string literal with embedded quotes doubled."""
    return "'" + str(value).replace("'", "''") + "'"


class EmailVectorStore:
    """Manages email embeddings and retrieval using LanceDB."""

    def __init__(
        self,
        db_path: Path | str | None = None,
        embedding_model_name: str = DEFAULT_EMBED_MODEL,
        table_name: str = "emails",
    ):
        root = repo_root_from_here()
        self.db_path = Path(db_path) if db_path else root / "data" / "email_lancedb"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.db = lancedb.connect(str(self.db_path))

        cache_dir = str(root / "data" / "cache" / "fastembed")
        self.embedding_model, self.embed_device, self.embed_batch_size = create_text_embedding(
            embedding_model_name, cache_dir, repo_root=root
        )
        self.table_name = table_name
        self.model_name = embedding_model_name

    def _table_exists(self) -> bool:
        try:
            res = self.db.list_tables()
            table_list = res.tables if hasattr(res, "tables") else list(res)
            return self.table_name in table_list
        except Exception:
            return False

    def _open_table(self):
        if self._table_exists():
            return self.db.open_table(self.table_name)
        return None

    def count_documents(self) -> int:
        """Return total number of indexed chunk vectors."""
        tbl = self._open_table()
        if tbl is None:
            return 0
        try:
            return tbl.count_rows()
        except Exception:
            return 0

    def list_indexed_services(self) -> list[str]:
        """Return distinct service names in the index."""
        tbl = self._open_table()
        if tbl is None:
            return []
        try:
            pylist = tbl.to_arrow().to_pylist()
            return sorted(list({r.get("service", "") for r in pylist if r.get("service")}))
        except Exception:
            return []

    def list_indexed_email_ids(self, service: str, folder: str) -> set[str]:
        """Return set of email IDs already indexed for a service and folder."""
        tbl = self._open_table()
        if tbl is None:
            return set()
        try:
            pylist = tbl.to_arrow().to_pylist()
            return {
                r.get("email_id", "")
                for r in pylist
                if r.get("service") == service and r.get("folder") == folder and r.get("email_id")
            }
        except Exception:
            return set()

    def get_storage_size_mb(self) -> float:
        """Return size of LanceDB storage on disk in megabytes."""
        if not self.db_path.exists():
            return 0.0
        total_bytes = sum(f.stat().st_size for f in self.db_path.rglob("*") if f.is_file())
        return round(total_bytes / (1024 * 1024), 2)

    def add_chunks(
        self,
        chunks: list[dict[str, Any]],
        *,
        overwrite: bool = False,
        progress_callback=None,
    ) -> int:
        """Embed and store email chunks into LanceDB."""
        if not chunks:
            return 0

        contents = [c.get("content", "") for c in chunks]
        total = len(contents)
        all_embeddings: list[Any] = []
        batch = self.embed_batch_size

        for start in range(0, total, batch):
            batch_texts = contents[start : start + batch]
            all_embeddings.extend(list(self.embedding_model.embed(batch_texts)))
            if progress_callback:
                progress_callback(min(start + len(batch_texts), total), total, "embedding")

        records: list[dict[str, Any]] = []
        for chunk, emb in zip(chunks, all_embeddings, strict=False):
            records.append(
                {
                    "id": chunk.get("id", ""),
                    "vector": emb.tolist(),
                    "content": chunk.get("content", ""),
                    "service": chunk.get("service", "default"),
                    "folder": chunk.get("folder", "INBOX"),
                    "email_id": chunk.get("email_id", ""),
                    "subject": chunk.get("subject", ""),
                    "from_addr": chunk.get("from_addr", ""),
                    "to_addr": chunk.get("to_addr", ""),
                    "date": chunk.get("date", ""),
                    "snippet": chunk.get("snippet", ""),
                    "chunk_index": int(chunk.get("chunk_index", 0)),
                    "total_chunks": int(chunk.get("total_chunks", 1)),
                }
            )

        if overwrite or not self._table_exists():
            self.db.create_table(self.table_name, data=records, mode="overwrite")
        else:
            tbl = self.db.open_table(self.table_name)
            tbl.add(records)

        logger.info(f"Indexed {len(records)} email chunks into LanceDB table '{self.table_name}'.")
        return len(records)

    def search(
        self,
        query: str,
        limit: int = 5,
        service: str | None = None,
        folder: str | None = None,
        min_score: float = 0.35,
    ) -> list[dict[str, Any]]:
        """Semantic neural search over indexed emails."""
        tbl = self._open_table()
        if tbl is None:
            return []

        query_emb = next(iter(self.embedding_model.embed([query])))
        search_req = tbl.search(query_emb).limit(limit * 2)

        # service/folder come from the calling agent: quote them as SQL string literals so a
        # stray ' cannot break out of the filter or widen it.
        where_parts = []
        if service:
            where_parts.append(f"service = {_sql_literal(service)}")
        if folder:
            where_parts.append(f"folder = {_sql_literal(folder)}")
        if where_parts:
            search_req = search_req.where(" AND ".join(where_parts))

        results = search_req.to_arrow().to_pylist()
        output = []
        seen_ids = set()

        for r in results:
            distance = r.get("_distance", 0.0)
            score = round(max(0.0, 1.0 - distance), 4)
            if score < min_score:
                continue

            unique_key = f"{r.get('service')}_{r.get('folder')}_{r.get('email_id')}_{r.get('chunk_index')}"
            if unique_key in seen_ids:
                continue
            seen_ids.add(unique_key)

            output.append(
                {
                    "id": r.get("id"),
                    "email_id": r.get("email_id"),
                    "service": r.get("service"),
                    "folder": r.get("folder"),
                    "subject": r.get("subject"),
                    "from": r.get("from_addr"),
                    "to": r.get("to_addr"),
                    "date": r.get("date"),
                    "snippet": r.get("snippet"),
                    "content": r.get("content"),
                    "score": score,
                    "chunk_index": r.get("chunk_index"),
                    "total_chunks": r.get("total_chunks"),
                }
            )
            if len(output) >= limit:
                break

        return output

    def clear_index(self, service: str | None = None, folder: str | None = None) -> bool:
        """Clear all or scoped rows from the vector table."""
        tbl = self._open_table()
        if tbl is None:
            return True
        try:
            if not service and not folder:
                self.db.drop_table(self.table_name)
                return True
            # Partial deletion: retain records that don't match
            pylist = tbl.to_arrow().to_pylist()
            kept = [
                r
                for r in pylist
                if not (
                    (service is None or r.get("service") == service) and (folder is None or r.get("folder") == folder)
                )
            ]
            self.db.create_table(self.table_name, data=kept, mode="overwrite")
            return True
        except Exception as e:
            logger.error(f"Error clearing vector store: {e}")
            return False
