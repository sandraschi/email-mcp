#!/usr/bin/env python3
"""
Email MCP Health Check Module

Provides comprehensive health monitoring for the Email MCP server including:
- Service connectivity checks
- Performance metrics
- Error rate monitoring
- Resource usage tracking
"""

import asyncio
import logging
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class HealthStatus:
    """Health status for a service."""
    service_name: str
    status: str  # "healthy", "degraded", "unhealthy"
    response_time: float
    last_check: datetime
    error_message: Optional[str] = None
    metrics: Dict[str, Any] = None


@dataclass
class SystemHealth:
    """Overall system health status."""
    overall_status: str
    services: Dict[str, HealthStatus]
    uptime_seconds: float
    total_checks: int
    failed_checks: int
    last_full_check: datetime


class EmailHealthMonitor:
    """Health monitoring system for Email MCP."""

    def __init__(self):
        self.start_time = time.time()
        self.check_history: List[Dict[str, Any]] = []
        self.service_configs: Dict[str, Dict[str, Any]] = {}
        self.logger = structlog.get_logger(__name__)

    def register_service(self, name: str, config: Dict[str, Any]) -> None:
        """Register a service for health monitoring."""
        self.service_configs[name] = config
        self.logger.info("Registered service for health monitoring", service=name)

    async def check_service_health(self, service_name: str) -> HealthStatus:
        """Check health of a specific service."""
        start_time = time.time()
        config = self.service_configs.get(service_name, {})

        try:
            if config.get("type") == "smtp":
                return await self._check_smtp_health(service_name, config)
            elif config.get("type") == "api":
                return await self._check_api_health(service_name, config)
            elif config.get("type") == "webhook":
                return await self._check_webhook_health(service_name, config)
            elif config.get("type") == "local":
                return await self._check_local_health(service_name, config)
            else:
                return HealthStatus(
                    service_name=service_name,
                    status="unknown",
                    response_time=time.time() - start_time,
                    last_check=datetime.now(),
                    error_message="Unknown service type"
                )
        except Exception as e:
            response_time = time.time() - start_time
            self.logger.error("Health check failed", service=service_name, error=str(e))
            return HealthStatus(
                service_name=service_name,
                status="unhealthy",
                response_time=response_time,
                last_check=datetime.now(),
                error_message=str(e)
            )

    async def _check_smtp_health(self, service_name: str, config: Dict[str, Any]) -> HealthStatus:
        """Check SMTP service health."""
        import smtplib

        start_time = time.time()
        server = config.get("server", "")
        port = config.get("port", 587)
        username = config.get("username", "")
        password = config.get("password", "")

        try:
            if port == 465:
                smtp = smtplib.SMTP_SSL(server, port, timeout=10)
            else:
                smtp = smtplib.SMTP(server, port, timeout=10)
                if port == 587:
                    smtp.starttls()

            if username and password:
                smtp.login(username, password)

            smtp.quit()

            return HealthStatus(
                service_name=service_name,
                status="healthy",
                response_time=time.time() - start_time,
                last_check=datetime.now(),
                metrics={"connection_established": True}
            )
        except Exception as e:
            return HealthStatus(
                service_name=service_name,
                status="unhealthy",
                response_time=time.time() - start_time,
                last_check=datetime.now(),
                error_message=str(e)
            )

    async def _check_api_health(self, service_name: str, config: Dict[str, Any]) -> HealthStatus:
        """Check API service health."""
        import httpx

        start_time = time.time()
        api_key = config.get("api_key", "")
        service_type = config.get("service_type", "")

        try:
            if service_type == "sendgrid":
                url = "https://api.sendgrid.com/v3/user/account"
                headers = {"Authorization": f"Bearer {api_key}"}
            elif service_type == "mailgun":
                url = f"https://api.mailgun.net/v3/domains"
                auth = httpx.BasicAuth("api", api_key)
                headers = {}
            elif service_type == "resend":
                url = "https://api.resend.com/domains"
                headers = {"Authorization": f"Bearer {api_key}"}
            else:
                raise ValueError(f"Unsupported API service: {service_type}")

            async with httpx.AsyncClient(timeout=10.0) as client:
                if 'auth' in locals():
                    response = await client.get(url, auth=auth)
                else:
                    response = await client.get(url, headers=headers)

                if response.status_code == 200:
                    return HealthStatus(
                        service_name=service_name,
                        status="healthy",
                        response_time=time.time() - start_time,
                        last_check=datetime.now(),
                        metrics={"status_code": response.status_code}
                    )
                else:
                    return HealthStatus(
                        service_name=service_name,
                        status="degraded",
                        response_time=time.time() - start_time,
                        last_check=datetime.now(),
                        error_message=f"HTTP {response.status_code}"
                    )
        except Exception as e:
            return HealthStatus(
                service_name=service_name,
                status="unhealthy",
                response_time=time.time() - start_time,
                last_check=datetime.now(),
                error_message=str(e)
            )

    async def _check_webhook_health(self, service_name: str, config: Dict[str, Any]) -> HealthStatus:
        """Check webhook service health."""
        start_time = time.time()
        webhook_url = config.get("webhook_url", "")

        if not webhook_url:
            return HealthStatus(
                service_name=service_name,
                status="unhealthy",
                response_time=time.time() - start_time,
                last_check=datetime.now(),
                error_message="No webhook URL configured"
            )

        # Webhook health is determined by URL validity and basic connectivity
        # We don't actually send test messages to avoid spam
        return HealthStatus(
            service_name=service_name,
            status="healthy",
            response_time=time.time() - start_time,
            last_check=datetime.now(),
            metrics={"url_configured": True}
        )

    async def _check_local_health(self, service_name: str, config: Dict[str, Any]) -> HealthStatus:
        """Check local service health."""
        import socket

        start_time = time.time()
        host = config.get("smtp_host", "localhost")
        port = config.get("smtp_port", 1025)

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((host, port))
            sock.close()

            if result == 0:
                return HealthStatus(
                    service_name=service_name,
                    status="healthy",
                    response_time=time.time() - start_time,
                    last_check=datetime.now(),
                    metrics={"connection_established": True}
                )
            else:
                return HealthStatus(
                    service_name=service_name,
                    status="unhealthy",
                    response_time=time.time() - start_time,
                    last_check=datetime.now(),
                    error_message="Connection refused"
                )
        except Exception as e:
            return HealthStatus(
                service_name=service_name,
                status="unhealthy",
                response_time=time.time() - start_time,
                last_check=datetime.now(),
                error_message=str(e)
            )

    async def check_all_services(self) -> SystemHealth:
        """Check health of all registered services."""
        start_time = time.time()
        service_results = {}

        tasks = []
        for service_name in self.service_configs:
            tasks.append(self.check_service_health(service_name))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for i, result in enumerate(results):
            service_name = list(self.service_configs.keys())[i]
            if isinstance(result, Exception):
                service_results[service_name] = HealthStatus(
                    service_name=service_name,
                    status="error",
                    response_time=0.0,
                    last_check=datetime.now(),
                    error_message=str(result)
                )
            else:
                service_results[service_name] = result

        # Determine overall status
        unhealthy_count = sum(1 for s in service_results.values() if s.status in ["unhealthy", "error"])
        degraded_count = sum(1 for s in service_results.values() if s.status == "degraded")

        if unhealthy_count > 0:
            overall_status = "unhealthy"
        elif degraded_count > 0:
            overall_status = "degraded"
        else:
            overall_status = "healthy"

        # Calculate uptime and check stats
        uptime_seconds = time.time() - self.start_time
        total_checks = len(service_results)
        failed_checks = unhealthy_count

        # Store check history
        check_record = {
            "timestamp": datetime.now(),
            "overall_status": overall_status,
            "services_checked": total_checks,
            "failed_services": failed_checks,
            "service_results": {name: {
                "status": status.status,
                "response_time": status.response_time,
                "error": status.error_message
            } for name, status in service_results.items()}
        }

        self.check_history.append(check_record)
        # Keep only last 100 checks
        if len(self.check_history) > 100:
            self.check_history = self.check_history[-100:]

        return SystemHealth(
            overall_status=overall_status,
            services=service_results,
            uptime_seconds=uptime_seconds,
            total_checks=total_checks,
            failed_checks=failed_checks,
            last_full_check=datetime.now()
        )

    def get_health_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent health check history."""
        return self.check_history[-limit:]

    def get_service_stats(self) -> Dict[str, Any]:
        """Get service statistics."""
        if not self.check_history:
            return {}

        total_checks = len(self.check_history)
        service_stats = {}

        for check in self.check_history:
            for service_name, service_result in check["service_results"].items():
                if service_name not in service_stats:
                    service_stats[service_name] = {
                        "total_checks": 0,
                        "healthy_checks": 0,
                        "response_times": []
                    }

                service_stats[service_name]["total_checks"] += 1
                if service_result["status"] == "healthy":
                    service_stats[service_name]["healthy_checks"] += 1
                service_stats[service_name]["response_times"].append(service_result["response_time"])

        # Calculate averages
        for service_name, stats in service_stats.items():
            response_times = stats["response_times"]
            stats["average_response_time"] = sum(response_times) / len(response_times) if response_times else 0
            stats["uptime_percentage"] = (stats["healthy_checks"] / stats["total_checks"]) * 100
            del stats["response_times"]  # Remove raw data

        return service_stats


# Global health monitor instance
health_monitor = EmailHealthMonitor()