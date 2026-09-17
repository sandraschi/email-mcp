"""Fleet-standard FastEmbed GPU bootstrap for email-mcp - see standards/patterns/FLEET_RAG_GPU.md."""

from __future__ import annotations

import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

EMBED_BATCH_SIZE_CPU = 64
EMBED_BATCH_SIZE_GPU = 256
DEFAULT_EMBED_MODEL = "BAAI/bge-small-en-v1.5"


def _env_flag(name: str) -> bool:
    raw = os.environ.get(name, "").strip().lower()
    return raw in ("1", "true", "yes", "on")


def repo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


def embed_use_gpu(repo_root: Path | None = None) -> bool:
    if _env_flag("RAG_GPU") or _env_flag("EMAIL_RAG_GPU") or _env_flag("MCD_RAG_GPU"):
        return True
    root = repo_root or repo_root_from_here()
    if (root / ".venv" / "rag-gpu-mode").is_file():
        return True
    return False


def create_text_embedding(
    model_name: str = DEFAULT_EMBED_MODEL,
    cache_dir: str | None = None,
    *,
    repo_root: Path | None = None,
    batch_cpu: int = EMBED_BATCH_SIZE_CPU,
    batch_gpu: int = EMBED_BATCH_SIZE_GPU,
):
    """Return (TextEmbedding, device_label, batch_size)."""
    from fastembed import TextEmbedding

    root = repo_root or repo_root_from_here()
    resolved_cache = cache_dir or str(root / "data" / "cache" / "fastembed")
    Path(resolved_cache).mkdir(parents=True, exist_ok=True)

    if embed_use_gpu(root):
        try:
            model = TextEmbedding(
                model_name=model_name,
                cache_dir=resolved_cache,
                providers=["CUDAExecutionProvider"],
            )
            providers = model.model.model.get_providers()
            if "CUDAExecutionProvider" in providers:
                logger.info("FastEmbed providers: %s", providers)
                return model, "cuda", batch_gpu
            logger.warning("CUDAExecutionProvider unavailable (%s); using CPU", providers)
        except Exception as exc:
            logger.warning("GPU embed init failed (%s); using CPU", exc)

    # fastembed-gpu wraps onnxruntime-gpu, whose session builder auto-selects
    # CUDA/TensorRT by priority when no providers= is given -- omitting the
    # arg here does NOT mean CPU-only, and this "CPU fallback" would silently
    # stay on CUDA until a cuDNN-only kernel fails at inference time. Force
    # CPUExecutionProvider explicitly.
    model = TextEmbedding(
        model_name=model_name,
        cache_dir=resolved_cache,
        providers=["CPUExecutionProvider"],
    )
    return model, "cpu", batch_cpu
