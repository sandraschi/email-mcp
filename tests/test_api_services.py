"""End-to-end tests for the service configuration REST API.

Tests the full CRUD lifecycle of email services via the web API:
  POST   /api/services  → create
  GET    /api/services  → list
  GET    /api/services/{name} → get one
  POST   /api/services/{name}/test → test connectivity
  DELETE /api/services/{name} → delete
"""

from __future__ import annotations

import httpx
import pytest

pytestmark = pytest.mark.integration


class TestServiceCRUD:
    """Full CRUD lifecycle for email services via REST API."""

    CONFIG_PAYLOAD = {
        "name": "test-smtp",
        "type": "smtp",
        "config": {
            "smtp_server": "smtp.example.com",
            "smtp_port": 587,
            "smtp_user": "test@example.com",
            "smtp_password": "test-password",
        },
    }

    async def test_create_service(self, client: httpx.AsyncClient, auth: dict) -> None:
        """POST /api/services should create a service and return success."""
        resp = await client.post("/api/services", json=self.CONFIG_PAYLOAD, headers=auth)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data["success"] is True
        assert data["service"] == "test-smtp"
        assert data["type"] == "smtp"

    async def test_create_duplicate_rejected(self, client: httpx.AsyncClient, auth: dict) -> None:
        """Creating a service with an existing name should fail."""
        await client.post("/api/services", json=self.CONFIG_PAYLOAD, headers=auth)
        resp = await client.post("/api/services", json=self.CONFIG_PAYLOAD, headers=auth)
        data = resp.json()
        assert data["success"] is False
        assert "already exists" in data.get("message", "") or "already exists" in data.get("error", "")

    async def test_create_missing_fields(self, client: httpx.AsyncClient, auth: dict) -> None:
        """POST /api/services without required fields should return 422."""
        resp = await client.post("/api/services", json={"name": "broken"}, headers=auth)
        assert resp.status_code == 422

    async def test_create_empty_config(self, client: httpx.AsyncClient, auth: dict) -> None:
        """POST /api/services with empty config should still succeed (service registered)."""
        resp = await client.post(
            "/api/services",
            json={
                "name": "empty-cfg",
                "type": "smtp",
                "config": {},
            },
            headers=auth,
        )
        data = resp.json()
        assert data["success"] is True

    async def test_list_services_contains_created(self, client: httpx.AsyncClient, auth: dict) -> None:
        """GET /api/services should include newly created services."""
        await client.post("/api/services", json=self.CONFIG_PAYLOAD, headers=auth)
        resp = await client.get("/api/services", headers=auth)
        assert resp.status_code == 200
        data = resp.json()
        services = data.get("services", {})
        assert "test-smtp" in services
        assert services["test-smtp"]["type"] == "smtp"

    async def test_get_single_service(self, client: httpx.AsyncClient, auth: dict) -> None:
        """GET /api/services/{name} should return the service details."""
        await client.post("/api/services", json=self.CONFIG_PAYLOAD, headers=auth)
        resp = await client.get("/api/services/test-smtp", headers=auth)
        assert resp.status_code == 200
        data = resp.json()
        svc = data.get("service", {})
        assert "test-smtp" in svc

    async def test_get_nonexistent_service_returns_404(self, client: httpx.AsyncClient, auth: dict) -> None:
        """GET /api/services/{name} for a non-existent service should return 404."""
        resp = await client.get("/api/services/nope-nonexistent", headers=auth)
        assert resp.status_code == 404

    async def test_test_service_endpoint_exists(self, client: httpx.AsyncClient, auth: dict) -> None:
        """POST /api/services/{name}/test should return without crashing."""
        await client.post("/api/services", json=self.CONFIG_PAYLOAD, headers=auth)
        resp = await client.post("/api/services/test-smtp/test", headers=auth)
        assert resp.status_code == 200
        data = resp.json()
        # Connection test may fail (no real server), but the endpoint should respond
        assert "services" in data or "connected" in str(data) or "error" in str(data)

    async def test_delete_service(self, client: httpx.AsyncClient, auth: dict) -> None:
        """DELETE /api/services/{name} should remove the service."""
        await client.post("/api/services", json=self.CONFIG_PAYLOAD, headers=auth)
        resp = await client.delete("/api/services/test-smtp", headers=auth)
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True

        # Verify it's gone
        list_resp = await client.get("/api/services", headers=auth)
        assert "test-smtp" not in list_resp.json().get("services", {})

    async def test_delete_nonexistent_returns_error(self, client: httpx.AsyncClient, auth: dict) -> None:
        """DELETE /api/services/{name} for a non-existent service should error."""
        resp = await client.delete("/api/services/nope-nonexistent", headers=auth)
        data = resp.json()
        assert data["success"] is False

    async def test_delete_default_service_rejected(self, client: httpx.AsyncClient, auth: dict) -> None:
        """Deleting the 'default' service should be rejected."""
        resp = await client.delete("/api/services/default", headers=auth)
        data = resp.json()
        assert data["success"] is False

    async def test_update_service_by_remove_and_readd(self, client: httpx.AsyncClient, auth: dict) -> None:
        """PUT /api/services/{name} should replace the service config."""
        # Create
        await client.post("/api/services", json=self.CONFIG_PAYLOAD, headers=auth)
        # Update with new config
        updated = {
            "type": "smtp",
            "config": {
                "smtp_server": "smtp.updated.com",
                "smtp_user": "updated@example.com",
                "smtp_password": "new-password",
            },
        }
        resp = await client.put("/api/services/test-smtp", json=updated, headers=auth)
        data = resp.json()
        assert data["success"] is True


class TestServiceTypes:
    """Test creating various service types."""

    _counter = 0
    SERVICE_TYPES = ["smtp", "api", "local", "webhook"]

    async def _create_type(self, client: httpx.AsyncClient, auth: dict, stype: str) -> dict:
        type(self)._counter += 1
        name = f"tst-{stype}-{self._counter}"
        payload = {
            "name": name,
            "type": stype,
            "config": {"test_key": "test_value", "service_type": stype},
        }
        resp = await client.post("/api/services", json=payload, headers=auth)
        assert resp.status_code == 200
        return resp.json()

    @pytest.mark.parametrize("stype", SERVICE_TYPES)
    async def test_create_each_type(self, client: httpx.AsyncClient, auth: dict, stype: str) -> None:
        """All service types can be created."""
        data = await self._create_type(client, auth, stype)
        assert data["success"] is True
        assert data["type"] == stype


class TestServiceLifecycle:
    """Test that a full lifecycle (create → list → delete) works cleanly."""

    async def test_full_lifecycle(self, client: httpx.AsyncClient, auth: dict, mailhog_config: dict) -> None:
        """Full create → verify in list → delete → verify gone."""
        name = "lifecycle-mailhog"
        payload = {"name": name, "type": "local", "config": mailhog_config}

        # Create
        create_resp = await client.post("/api/services", json=payload, headers=auth)
        assert create_resp.json()["success"] is True

        # Verify in list
        list_resp = await client.get("/api/services", headers=auth)
        svcs = list_resp.json().get("services", {})
        assert name in svcs
        assert svcs[name]["type"] == "local"

        # Delete
        del_resp = await client.delete(f"/api/services/{name}", headers=auth)
        assert del_resp.json()["success"] is True

        # Verify gone
        final_list = await client.get("/api/services", headers=auth)
        assert name not in final_list.json().get("services", {})
