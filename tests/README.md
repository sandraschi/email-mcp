# Tests -- email-mcp

69 backend tests (pytest) + 17 Playwright e2e tests = 86 total.

## Run Tests

```powershell
# Backend tests
pytest tests/ -q

# E2E tests
cd webapp && npx playwright test && cd ..

# Full suite
pytest tests/ -q && cd webapp && npx playwright test && cd ..
```

## Test Files

| File | What it tests |
|------|---------------|
| `test_sanitize.py` | Prompt injection defense (Unicode stripping + safety boundary) |
| `test_mailing_lists.py` | Mailing list preset loading and validation |
| `test_contacts.py` | Contact CRUD and import |
| `test_api_services.py` | API service payload preparation |
| `test_connection.py` | Service configuration and connection testing |
| `test_e2e_real.py` | End-to-end integration tests |
| `conftest.py` | Shared fixtures and test client |
