"""Tests for the auto-respond rule engine (matching, priority, actions)."""

from __future__ import annotations

from email_mcp import autorespond


def test_runtime_dir_tauri_mode(monkeypatch, tmp_path):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    monkeypatch.setenv("EMAIL_MCP_TAURI", "1")
    assert autorespond._runtime_dir() == tmp_path / "ai.fleet.email-mcp"


def test_runtime_dir_dev_default(monkeypatch):
    monkeypatch.delenv("EMAIL_MCP_TAURI", raising=False)
    assert autorespond._runtime_dir() is None
    # dev defaults live under repo src/
    d = autorespond._default_data_dir
    assert str(d).endswith("src")
    assert "ai.fleet.email-mcp" not in str(d)


def _fresh(monkeypatch, tmp_path):
    from pathlib import Path

    rules_file = Path(tmp_path / "rules.json")
    pending_file = Path(tmp_path / "pending.json")
    monkeypatch.setenv("EMAIL_MCP_AUTORESPOND_RULES", str(rules_file))
    monkeypatch.setenv("EMAIL_MCP_AUTORESPOND_PENDING", str(pending_file))
    monkeypatch.setattr(autorespond, "_RULES_FILE", rules_file)
    monkeypatch.setattr(autorespond, "_PENDING_FILE", pending_file)
    monkeypatch.setattr(autorespond, "_RULES", [])
    monkeypatch.setattr(autorespond, "_PENDING", [])


def test_add_rule_priority_and_all_field(monkeypatch, tmp_path):
    _fresh(monkeypatch, tmp_path)
    r = autorespond.add_rule("Github", match_field="all", match_pattern="github")
    assert r["success"] is True
    assert r["rule"]["priority"] == 100
    assert r["rule"]["match_field"] == "all"


def test_match_rule_priority_order(monkeypatch, tmp_path):
    _fresh(monkeypatch, tmp_path)
    autorespond.add_rule("low", match_field="subject", match_pattern="invoice", priority=200)
    autorespond.add_rule("high", match_field="subject", match_pattern="invoice", priority=10)
    email = {"subject": "invoice overdue", "from": "x@y.com", "text_body": ""}
    rule = autorespond.match_rule(email)
    assert rule is not None
    assert rule["name"] == "high"


def test_match_rule_all_fields(monkeypatch, tmp_path):
    _fresh(monkeypatch, tmp_path)
    autorespond.add_rule("body-rule", match_field="all", match_pattern="payment received")
    email = {"subject": "hello", "from": "x@y.com", "text_body": "your payment received, thanks"}
    rule = autorespond.match_rule(email)
    assert rule is not None
    assert rule["name"] == "body-rule"


def test_match_rule_disabled_skipped(monkeypatch, tmp_path):
    _fresh(monkeypatch, tmp_path)
    autorespond.add_rule("off", match_field="subject", match_pattern="invoice")
    autorespond.update_rule(autorespond.list_rules()[0]["id"], {"enabled": False})
    assert autorespond.match_rule({"subject": "invoice"}) is None


def test_test_rule_dry_run(monkeypatch, tmp_path):
    _fresh(monkeypatch, tmp_path)
    autorespond.add_rule(
        "forwarder",
        match_field="from",
        match_pattern="boss@",
        filter_action="forward",
        filter_target="team@x.com",
    )
    result = autorespond.test_rule(email_from="boss@corp.com", email_subject="report")
    assert result["success"] is True
    assert result["matched"] is True
    assert result["rule"]["name"] == "forwarder"
    assert "forward" in result["would_fire"]

    result2 = autorespond.test_rule(email_subject="nothing here")
    assert result2["matched"] is False


def test_test_rule_by_id(monkeypatch, tmp_path):
    _fresh(monkeypatch, tmp_path)
    autorespond.add_rule("a", match_field="subject", match_pattern="alpha")
    autorespond.add_rule("b", match_field="subject", match_pattern="beta")
    rid = autorespond.list_rules()[1]["id"]
    result = autorespond.test_rule(email_subject="beta thing", rule_id=rid)
    assert result["matched"] is True
    assert result["rule"]["name"] == "b"


def test_update_rule_priority(monkeypatch, tmp_path):
    _fresh(monkeypatch, tmp_path)
    autorespond.add_rule("r", match_field="subject", match_pattern="x")
    rid = autorespond.list_rules()[0]["id"]
    r = autorespond.update_rule(rid, {"priority": 5})
    assert r["success"] is True
    assert r["rule"]["priority"] == 5


async def test_auto_respond_notify_action(monkeypatch, tmp_path):
    _fresh(monkeypatch, tmp_path)
    autorespond.add_rule(
        "n", match_field="subject", match_pattern="urgent", filter_action="notify", filter_target="both"
    )
    pushed = []

    async def fake_push_aiwatcher(title, summary, **kw):
        pushed.append(("aiwatcher", title))
        return {"success": True, "connector": "aiwatcher"}

    async def fake_push_robofang(from_addr, body, **kw):
        pushed.append(("robofang", from_addr))
        return {"success": True, "connector": "robofang"}

    monkeypatch.setattr("email_mcp.connectors.push_aiwatcher", fake_push_aiwatcher)
    monkeypatch.setattr("email_mcp.connectors.push_robofang", fake_push_robofang)

    email = {"id": "m1", "subject": "URGENT invoice", "from": "a@x.com", "text_body": "pay now", "folder": "INBOX"}
    result = await autorespond.auto_respond(email, mcp_app=None)
    assert result["matched"] is True
    assert ("aiwatcher", "URGENT invoice") in pushed
    assert ("robofang", "a@x.com") in pushed


async def test_auto_respond_move_filter(monkeypatch, tmp_path):
    _fresh(monkeypatch, tmp_path)
    autorespond.add_rule(
        "mv", match_field="subject", match_pattern="github", filter_action="move", filter_target="Github"
    )
    calls = []

    class FakeMCP:
        async def call_tool(self, name, args):
            calls.append((name, args))
            return {"success": True}

    email = {"id": "m2", "subject": "github PR", "from": "bot@github.com", "text_body": "", "folder": "INBOX"}
    result = await autorespond.auto_respond(email, mcp_app=FakeMCP())
    assert result["matched"] is True
    assert ("move_email", {"email_id": "m2", "to_folder": "Github", "service": "default", "folder": "INBOX"}) in calls


async def test_auto_respond_queues_pending(monkeypatch, tmp_path):
    _fresh(monkeypatch, tmp_path)
    autorespond.add_rule("reply", match_field="subject", match_pattern="hello", reply_body="Hi there!", auto_send=False)
    email = {"id": "m3", "subject": "hello friend", "from": "b@x.com", "text_body": "hi", "folder": "INBOX"}
    result = await autorespond.auto_respond(email, mcp_app=None)
    assert result["matched"] is True
    assert result["queued"] is True
    pending = autorespond.list_pending()
    assert len(pending) == 1
    assert pending[0]["reply_body"] == "Hi there!"
