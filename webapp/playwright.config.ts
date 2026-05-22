import { defineConfig } from '@playwright/test';

export default defineConfig({
    testDir: './e2e',
    timeout: 60000,
    retries: 1,
    use: {
        baseURL: 'http://localhost:10812',
        headless: true,
        screenshot: 'only-on-failure',
    },
    webServer: {
        command: 'uv run uvicorn email_mcp.server:app --host 127.0.0.1 --port 10813 --log-level warning',
        port: 10813,
        cwd: '../',
        timeout: 30000,
        reuseExistingServer: false,
    },
});
