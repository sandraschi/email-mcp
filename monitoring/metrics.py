#!/usr/bin/env python3
"""
Email MCP Metrics Collection

Collects and exposes performance metrics for the Email MCP server.
"""

import time
import psutil
from typing import Dict, Any, List
from dataclasses import dataclass
from datetime import datetime
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class EmailMetrics:
    """Email operation metrics."""
    operation: str
    service: str
    success: bool
    response_time: float
    timestamp: datetime
    error_type: str = ""
    bytes_transferred: int = 0


class MetricsCollector:
    """Collects and aggregates metrics for the Email MCP server."""

    def __init__(self):
        self.email_metrics: List[EmailMetrics] = []
        self.start_time = time.time()
        self.operation_counts: Dict[str, int] = {}
        self.error_counts: Dict[str, int] = {}
        self.service_usage: Dict[str, int] = {}

    def record_email_operation(self, operation: str, service: str, success: bool,
                             response_time: float, error_type: str = "", bytes_transferred: int = 0) -> None:
        """Record an email operation metric."""
        metric = EmailMetrics(
            operation=operation,
            service=service,
            success=success,
            response_time=response_time,
            timestamp=datetime.now(),
            error_type=error_type,
            bytes_transferred=bytes_transferred
        )

        self.email_metrics.append(metric)

        # Update counters
        self.operation_counts[operation] = self.operation_counts.get(operation, 0) + 1
        self.service_usage[service] = self.service_usage.get(service, 0) + 1

        if not success:
            error_key = f"{operation}:{error_type}"
            self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1

        # Keep only last 1000 metrics
        if len(self.email_metrics) > 1000:
            self.email_metrics = self.email_metrics[-1000:]

        logger.debug("Recorded email metric", operation=operation, service=service, success=success)

    def get_operation_stats(self) -> Dict[str, Any]:
        """Get operation statistics."""
        if not self.email_metrics:
            return {}

        stats = {}
        operations = set(m.operation for m in self.email_metrics)

        for operation in operations:
            op_metrics = [m for m in self.email_metrics if m.operation == operation]
            response_times = [m.response_time for m in op_metrics]
            success_count = sum(1 for m in op_metrics if m.success)

            stats[operation] = {
                "total_calls": len(op_metrics),
                "success_rate": success_count / len(op_metrics),
                "average_response_time": sum(response_times) / len(response_times),
                "min_response_time": min(response_times),
                "max_response_time": max(response_times),
                "total_bytes": sum(m.bytes_transferred for m in op_metrics)
            }

        return stats

    def get_service_stats(self) -> Dict[str, Any]:
        """Get service usage statistics."""
        stats = {}

        for service in self.service_usage:
            service_metrics = [m for m in self.email_metrics if m.service == service]
            if service_metrics:
                response_times = [m.response_time for m in service_metrics]
                success_count = sum(1 for m in service_metrics if m.success)

                stats[service] = {
                    "usage_count": self.service_usage[service],
                    "success_rate": success_count / len(service_metrics),
                    "average_response_time": sum(response_times) / len(response_times)
                }

        return stats

    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics."""
        return dict(self.error_counts)

    def get_system_metrics(self) -> Dict[str, Any]:
        """Get system resource metrics."""
        process = psutil.Process()
        memory_info = process.memory_info()
        cpu_times = process.cpu_times()

        return {
            "uptime_seconds": time.time() - self.start_time,
            "memory_rss": memory_info.rss,
            "memory_vms": memory_info.vms,
            "cpu_user_time": cpu_times.user,
            "cpu_system_time": cpu_times.system,
            "cpu_total_time": cpu_times.user + cpu_times.system,
            "thread_count": process.num_threads(),
            "open_files": len(process.open_files())
        }

    def get_recent_metrics(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent metrics."""
        recent = self.email_metrics[-limit:]
        return [
            {
                "operation": m.operation,
                "service": m.service,
                "success": m.success,
                "response_time": m.response_time,
                "timestamp": m.timestamp.isoformat(),
                "error_type": m.error_type,
                "bytes_transferred": m.bytes_transferred
            }
            for m in recent
        ]

    def reset_metrics(self) -> None:
        """Reset all metrics (for testing)."""
        self.email_metrics.clear()
        self.operation_counts.clear()
        self.error_counts.clear()
        self.service_usage.clear()
        logger.info("Metrics reset")


# Global metrics collector instance
metrics_collector = MetricsCollector()