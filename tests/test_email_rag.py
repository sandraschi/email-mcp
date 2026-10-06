"""Tests for Email MCP local RAG vector store, ingestor, and web endpoints."""

from __future__ import annotations

import tempfile
from unittest.mock import AsyncMock, MagicMock

import pytest

from email_mcp.rag.ingestor import EmailIngestor, clean_html
from email_mcp.rag.vector_store import EmailVectorStore


def test_clean_html():
    html_content = "<div><p>Hello <b>World</b>!</p><script>alert(1)</script><a href='http://x'>Link</a></div>"
    text = clean_html(html_content)
    assert "Hello" in text
    assert "World" in text
    assert "Link" in text
    assert "alert(1)" not in text


def test_email_ingestor_chunking():
    ingestor = EmailIngestor(chunk_size=100, chunk_overlap=20)
    text = "Paragraph one.\n\nParagraph two with more details.\n\nParagraph three with even more content."
    chunks = ingestor.chunk_text(text)
    assert len(chunks) >= 1
    assert any("Paragraph one" in c for c in chunks)


def test_email_ingestor_process_message():
    ingestor = EmailIngestor()
    msg = {
        "id": "msg-123",
        "subject": "Q3 Project Review",
        "from": "alice@example.com",
        "to": "bob@example.com",
        "date": "2026-09-12",
        "body": "Hi Bob,\n\nPlease find attached the review for Q3 milestones and deliverables.\n\nBest,\nAlice",
    }
    records = ingestor.process_message(msg, service="work", folder="INBOX")
    assert len(records) >= 1
    rec = records[0]
    assert rec["email_id"] == "msg-123"
    assert rec["subject"] == "Q3 Project Review"
    assert "Q3 milestones" in rec["content"]
    assert "[Email from: alice@example.com" in rec["content"]


def test_vector_store_add_and_search():
    with tempfile.TemporaryDirectory() as tmpdir:
        store = EmailVectorStore(db_path=tmpdir)
        records = [
            {
                "id": "chk-1",
                "service": "personal",
                "folder": "INBOX",
                "email_id": "101",
                "subject": "Flight Confirmation Paris",
                "from_addr": "booking@airline.com",
                "to_addr": "me@example.com",
                "date": "2026-06-01",
                "snippet": "Your flight AF123 to Paris CDG is confirmed.",
                "content": "[Email from: booking@airline.com | Subject: Flight Confirmation Paris]\nYour flight AF123 to Paris CDG is confirmed for June 15.",
                "chunk_index": 0,
                "total_chunks": 1,
            },
            {
                "id": "chk-2",
                "service": "work",
                "folder": "INBOX",
                "email_id": "102",
                "subject": "AWS Cloud Invoice",
                "from_addr": "billing@aws.amazon.com",
                "to_addr": "me@example.com",
                "date": "2026-06-02",
                "snippet": "Monthly AWS statement for May 2026.",
                "content": "[Email from: billing@aws.amazon.com | Subject: AWS Cloud Invoice]\nYour monthly AWS statement for May 2026 is $450.20.",
                "chunk_index": 0,
                "total_chunks": 1,
            },
        ]

        count = store.add_chunks(records)
        assert count == 2
        assert store.count_documents() == 2

        # Verify indexed IDs
        ids = store.list_indexed_email_ids("personal", "INBOX")
        assert "101" in ids
        assert "102" not in ids

        # Semantic query
        results = store.search("airplane ticket to France", limit=2, min_score=0.1)
        assert len(results) >= 1
        assert results[0]["email_id"] == "101"
        assert "Paris" in results[0]["subject"]


def _chunk(cid: str, service: str, folder: str, email_id: str, text: str) -> dict:
    return {
        "id": cid,
        "service": service,
        "folder": folder,
        "email_id": email_id,
        "subject": text,
        "from_addr": "a@example.com",
        "to_addr": "b@example.com",
        "date": "2026-06-01",
        "snippet": text,
        "content": text,
        "chunk_index": 0,
        "total_chunks": 1,
    }


def test_search_filters_quote_service_and_folder_values():
    """service/folder come from the calling agent: a quote must neither error nor widen the filter."""
    with tempfile.TemporaryDirectory() as tmpdir:
        store = EmailVectorStore(db_path=tmpdir)
        store.add_chunks(
            [
                _chunk("c1", "o'brien", "INBOX", "1", "Quarterly budget review meeting notes"),
                _chunk("c2", "other", "INBOX", "2", "Quarterly budget review meeting notes"),
            ]
        )
        # A legitimate value containing an apostrophe still works...
        only_obrien = store.search("budget review", service="o'brien", min_score=0.0)
        assert {r["service"] for r in only_obrien} == {"o'brien"}
        # ...and an injection attempt matches nothing instead of returning the other account's rows.
        injected = store.search("budget review", service="x' OR service = 'other", min_score=0.0)
        assert injected == []
        assert store.search("budget review", folder="INBOX' OR '1'='1", min_score=0.0) == []


def test_rag_tools_advertise_real_mcp_annotations():
    import asyncio

    from fastmcp import FastMCP

    from email_mcp.tools.rag_tools import register_rag_tools

    mcp = FastMCP("rag-annotations")
    register_rag_tools(mcp, MagicMock(services={}))
    tools = {t.name: t for t in asyncio.run(mcp.list_tools())}
    assert set(tools) == {"email_rag", "sync_email_rag", "email_rag_stats"}
    assert tools["email_rag"].annotations.readOnlyHint is True
    assert tools["email_rag_stats"].annotations.readOnlyHint is True
    assert tools["sync_email_rag"].annotations.readOnlyHint is False
    assert tools["sync_email_rag"].annotations.destructiveHint is False


def test_missing_rag_dependency_cannot_stop_the_server_starting(monkeypatch):
    """lancedb/fastembed are not bundled in the installer or the mcpb: registration must degrade."""
    import sys

    from fastmcp import FastMCP

    from email_mcp.server import _register_optional_rag

    # A None entry in sys.modules makes `import email_mcp.tools.rag_tools` raise ImportError,
    # exactly what a missing lancedb does inside that module.
    monkeypatch.setitem(sys.modules, "email_mcp.tools.rag_tools", None)
    mcp = FastMCP("no-rag")
    assert _register_optional_rag(mcp, MagicMock(services={})) is False

    monkeypatch.delitem(sys.modules, "email_mcp.tools.rag_tools")
    assert _register_optional_rag(FastMCP("with-rag"), MagicMock(services={})) is True


@pytest.mark.asyncio
async def test_ingestor_sweep_service_folder():
    with tempfile.TemporaryDirectory() as tmpdir:
        store = EmailVectorStore(db_path=tmpdir)
        ingestor = EmailIngestor()

        # Mock service object
        mock_service = MagicMock()
        mock_service.check_inbox = AsyncMock(
            return_value={
                "success": True,
                "emails": [
                    {
                        "id": "msg-1",
                        "subject": "Tax forms 2025",
                        "from": "accountant@cpa.com",
                        "to": "me@example.com",
                        "date": "2026-04-10",
                    }
                ],
            }
        )
        mock_service.fetch_message = AsyncMock(
            return_value={
                "success": True,
                "message": {
                    "id": "msg-1",
                    "subject": "Tax forms 2025",
                    "from": "accountant@cpa.com",
                    "to": "me@example.com",
                    "date": "2026-04-10",
                    "body": "Hello, here are your signed tax filings for last year.",
                },
            }
        )

        res = await ingestor.sweep_service_folder(
            service_obj=mock_service,
            service_name="test_svc",
            folder="INBOX",
            vector_store=store,
        )

        assert res["success"] is True
        assert res["chunks_indexed"] == 1
        assert res["emails_processed"] == 1

        # Second incremental run should skip already indexed
        res2 = await ingestor.sweep_service_folder(
            service_obj=mock_service,
            service_name="test_svc",
            folder="INBOX",
            vector_store=store,
        )
        assert res2["success"] is True
        assert res2["chunks_indexed"] == 0
        assert res2["emails_processed"] == 0


@pytest.mark.asyncio
async def test_rag_web_endpoints(client, auth):
    # Test GET /api/rag/stats
    stats_res = await client.get("/api/rag/stats", headers=auth)
    assert stats_res.status_code == 200
    data = stats_res.json()
    assert data["success"] is True
    assert "total_chunks" in data
    assert "embedding_model" in data

    # Test POST /api/rag/sweep
    sweep_res = await client.post(
        "/api/rag/sweep",
        json={"service": "nonexistent_svc", "folder": "INBOX"},
        headers=auth,
    )
    assert sweep_res.status_code == 200
    sweep_data = sweep_res.json()
    assert sweep_data["success"] is True
    job_id = sweep_data["job_id"]
    assert job_id

    # Test GET /api/rag/status/{job_id}
    status_res = await client.get(f"/api/rag/status/{job_id}", headers=auth)
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert status_data["job_id"] == job_id
    assert status_data["status"] in ("queued", "running", "complete", "error")
