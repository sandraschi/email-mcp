import { useCallback, useEffect, useState } from "react";

const ZOOM_LEVELS = [0.5, 0.6, 0.7, 0.8, 1.0, 1.25, 1.5, 2.0, 3.0];

export function useZoom() {
  const [zoomIndex, setZoomIndex] = useState(() => {
    try {
      const saved = localStorage.getItem("tauri-zoom");
      return saved ? ZOOM_LEVELS.indexOf(parseFloat(saved)) : 3;
    } catch {
      return 3;
    }
  });

  const applyZoom = useCallback(async (level: number) => {
    localStorage.setItem("tauri-zoom", String(level));
    try {
      const { getCurrentWindow } = await import("@tauri-apps/api/window");
      await (getCurrentWindow() as any).setZoom(level);
      return;
    } catch {
      /* fall through to CSS zoom */
    }
    document.documentElement.style.zoom = String(level);
  }, []);

  useEffect(() => {
    const handler = (e: WheelEvent) => {
      if (!e.ctrlKey) return;
      e.preventDefault();
      setZoomIndex((prev) => {
        const next =
          e.deltaY < 0
            ? Math.min(prev + 1, ZOOM_LEVELS.length - 1)
            : Math.max(prev - 1, 0);
        if (next !== prev) applyZoom(ZOOM_LEVELS[next]);
        return next;
      });
    };
    window.addEventListener("wheel", handler, { passive: false });
    const saved = localStorage.getItem("tauri-zoom");
    if (saved) applyZoom(parseFloat(saved));
    return () => window.removeEventListener("wheel", handler);
  }, [applyZoom]);

  return {
    zoomLevel: ZOOM_LEVELS[zoomIndex],
    resetZoom: () => {
      setZoomIndex(3);
      applyZoom(1.0);
    },
  };
}
