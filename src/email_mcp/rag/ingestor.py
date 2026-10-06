"""Email Content Ingestor and Chunker for RAG."""

from __future__ import annotations

import hashlib
import logging
import re
from typing import Any

from bs4 import BeautifulSoup

from .vector_store import EmailVectorStore

logger = logging.getLogger(__name__)


def clean_html(html_text: str) -> str:
    """Strip HTML markup and convert common tags to clean text."""
    if not html_text:
        return ""
    try:
        soup = BeautifulSoup(html_text, "html.parser")
        for tag in soup(["script", "style", "head", "title", "meta", "[document]"]):
            tag.decompose()
        text = soup.get_text(separator=" ")
        # Collapse multiple whitespace
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n\s*\n+", "\n\n", text)
        return text.strip()
    except Exception:
        # Fallback regex
        clean = re.sub(r"<[^>]+>", " ", html_text)
        return re.sub(r"\s+", " ", clean).strip()


class EmailIngestor:
    """Processes raw email messages into semantically enriched chunks for embedding."""

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 150):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_text(self, text: str) -> list[str]:
        """Markdown and paragraph-aware recursive text chunker."""
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]

        paragraphs = text.split("\n\n")
        chunks: list[str] = []
        current_chunk: list[str] = []
        current_len = 0

        for p in paragraphs:
            p_len = len(p)
            if current_len + p_len > self.chunk_size and current_chunk:
                joined = "\n\n".join(current_chunk)
                chunks.append(joined)
                # Retain overlap from end of current chunk if possible
                current_chunk = [p]
                current_len = p_len
            else:
                current_chunk.append(p)
                current_len += p_len + 2

        if current_chunk:
            chunks.append("\n\n".join(current_chunk))

        # Secondary split for any single paragraphs that exceeded chunk_size
        final_chunks: list[str] = []
        for c in chunks:
            if len(c) <= self.chunk_size:
                final_chunks.append(c)
            else:
                for i in range(0, len(c), self.chunk_size - self.chunk_overlap):
                    final_chunks.append(c[i : i + self.chunk_size])

        return [c.strip() for c in final_chunks if c.strip()]

    def process_message(
        self,
        msg: dict[str, Any],
        service: str = "default",
        folder: str = "INBOX",
    ) -> list[dict[str, Any]]:
        """Turn a parsed email message into searchable chunks with contextual metadata."""
        email_id = str(msg.get("id") or msg.get("email_id") or "")
        subject = str(msg.get("subject") or "(No Subject)").strip()
        from_addr = str(msg.get("from") or "Unknown").strip()
        to_addr = str(msg.get("to") or "").strip()
        date_str = str(msg.get("date") or "").strip()

        # Extract text body: prefer plain text, fall back to clean HTML
        raw_body = msg.get("body") or msg.get("text") or ""
        html_body = msg.get("html") or ""
        if not raw_body and html_body:
            body_text = clean_html(html_body)
        elif raw_body:
            body_text = str(raw_body).strip()
        else:
            body_text = clean_html(html_body)

        if not body_text:
            body_text = f"Subject: {subject}\nFrom: {from_addr}\nDate: {date_str}"

        # Context header prepended to chunks for semantic clarity
        header_context = f"[Email from: {from_addr} | To: {to_addr} | Date: {date_str} | Subject: {subject}]\n\n"
        body_chunks = self.chunk_text(body_text)

        if not body_chunks:
            body_chunks = [body_text]

        total_chunks = len(body_chunks)
        snippet = body_text[:220].replace("\n", " ").strip()
        if len(body_text) > 220:
            snippet += "..."

        records: list[dict[str, Any]] = []
        for idx, chunk in enumerate(body_chunks):
            chunk_content = header_context + chunk
            chunk_hash = hashlib.md5(
                f"{service}_{folder}_{email_id}_{idx}".encode(),
                usedforsecurity=False,
            ).hexdigest()

            records.append(
                {
                    "id": chunk_hash,
                    "service": service,
                    "folder": folder,
                    "email_id": email_id,
                    "subject": subject,
                    "from_addr": from_addr,
                    "to_addr": to_addr,
                    "date": date_str,
                    "snippet": snippet,
                    "content": chunk_content,
                    "chunk_index": idx,
                    "total_chunks": total_chunks,
                }
            )

        return records

    async def sweep_service_folder(
        self,
        service_obj: Any,
        service_name: str,
        folder: str = "INBOX",
        vector_store: EmailVectorStore | None = None,
        limit: int = 100,
        full_reindex: bool = False,
        progress_callback=None,
    ) -> dict[str, Any]:
        """Scan messages from an email service and index into the vector store."""
        store = vector_store or EmailVectorStore()
        indexed_ids = set() if full_reindex else store.list_indexed_email_ids(service_name, folder)

        if progress_callback:
            progress_callback(0, 100, f"Scanning {service_name}:{folder}")

        # 1. Fetch recent message headers
        check_res = await service_obj.check_inbox(folder=folder, limit=limit, unread_only=False)
        if not check_res.get("success", False):
            return {
                "success": False,
                "error": check_res.get("error", "Failed to check inbox"),
                "chunks_indexed": 0,
            }

        emails = check_res.get("emails", [])
        to_index = [e for e in emails if str(e.get("id")) not in indexed_ids]

        if not to_index:
            return {
                "success": True,
                "message": f"All {len(emails)} emails in {service_name}:{folder} are already indexed.",
                "chunks_indexed": 0,
                "emails_processed": 0,
            }

        total_to_process = len(to_index)
        all_chunks: list[dict[str, Any]] = []

        # 2. Fetch full body for each unindexed message and chunk
        for i, email_meta in enumerate(to_index):
            eid = str(email_meta.get("id"))
            try:
                msg_data = await service_obj.fetch_message(folder, eid)
                if msg_data.get("success", False) and "message" in msg_data:
                    full_msg = msg_data["message"]
                else:
                    # Fallback to header metadata if full fetch fails
                    full_msg = email_meta

                chunks = self.process_message(full_msg, service=service_name, folder=folder)
                all_chunks.extend(chunks)
            except Exception as exc:
                logger.warning(f"Failed to fetch/chunk email {eid}: {exc}")

            if progress_callback and total_to_process:
                progress_callback(i + 1, total_to_process, "extracting")

        # 3. Store and embed chunks
        if all_chunks:
            if progress_callback:
                progress_callback(0, len(all_chunks), "embedding")
            indexed_count = store.add_chunks(
                all_chunks,
                overwrite=full_reindex,
                progress_callback=progress_callback,
            )
        else:
            indexed_count = 0

        return {
            "success": True,
            "service": service_name,
            "folder": folder,
            "emails_processed": len(to_index),
            "chunks_indexed": indexed_count,
            "message": f"Successfully indexed {indexed_count} chunks from {len(to_index)} emails.",
        }
