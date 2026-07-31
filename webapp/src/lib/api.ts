/**
 * Standard API utility for the Email MCP web dashboard.
 * Implements HTTP Basic Auth for all /api requests with timeout.
 */

const AUTH_USER = "sandra";
const AUTH_PASS = "vienna2026";
const AUTH_HEADER = `Basic ${btoa(`${AUTH_USER}:${AUTH_PASS}`)}`;
const DEFAULT_TIMEOUT = 15_000; // 15 seconds

// In Tauri production, the frontend is served from webview (origin: tauri.localhost)
// but the backend runs on 127.0.0.1:10813. VITE_API_BASE bridges the gap.
// In dev, Vite proxy handles it so API_BASE is empty.
export const API_BASE = "http://127.0.0.1:10813";

function buildUrl(path: string): string {
	if (path.startsWith("http")) return path;
	const normalized = path.startsWith("/") ? path : `/${path}`;
	return `${API_BASE}${normalized}`;
}

export async function fetchWithAuth(
	url: string,
	options: RequestInit = {},
	timeoutMs = DEFAULT_TIMEOUT,
) {
	const _resolvedUrl = buildUrl(url);
	const controller = new AbortController();
	const timer = setTimeout(() => controller.abort(), timeoutMs);

	const headers = {
		...options.headers,
		Authorization: AUTH_HEADER,
		"Content-Type": "application/json",
	};

	try {
		const response = await fetch(url, {
			...options,
			headers,
			signal: controller.signal,
		});
		clearTimeout(timer);

		if (response.status === 401) {
			throw new Error(
				"Unauthorized: Please check your credentials in the backend.",
			);
		}

		if (!response.ok) {
			const text = await response.text().catch(() => "");
			throw new Error(
				`API Error ${response.status}: ${text || response.statusText}`,
			);
		}

		return response.json();
	} catch (err) {
		clearTimeout(timer);
		if (err instanceof DOMException && err.name === "AbortError") {
			throw new Error(`Request timed out after ${timeoutMs / 1000}s: ${url}`);
		}
		throw err;
	}
}
