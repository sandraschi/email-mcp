#!/usr/bin/env python3
"""
Email MCP Monitoring Configuration

Configuration for health monitoring, metrics collection, and alerting.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class HealthCheckConfig:
    """Configuration for health checks."""
    enabled: bool = True
    interval_seconds: int = 300  # 5 minutes
    timeout_seconds: int = 10
    retry_attempts: int = 3
    retry_delay_seconds: int = 5
    alert_on_failure: bool = True
    alert_threshold_consecutive_failures: int = 3


@dataclass
class MetricsConfig:
    """Configuration for metrics collection."""
    enabled: bool = True
    retention_days: int = 7
    max_metrics_history: int = 10000
    export_interval_seconds: int = 3600  # 1 hour
    export_format: str = "json"


@dataclass
class AlertConfig:
    """Configuration for alerting."""
    enabled: bool = False
    email_alerts: bool = False
    alert_email_recipients: List[str] = None
    slack_webhook_url: Optional[str] = None
    alert_on_service_down: bool = True
    alert_on_high_error_rate: bool = True
    error_rate_threshold: float = 0.1  # 10%
    alert_cooldown_minutes: int = 60


@dataclass
class MonitoringConfig:
    """Overall monitoring configuration."""
    health_checks: HealthCheckConfig
    metrics: MetricsConfig
    alerts: AlertConfig
    log_level: str = "INFO"
    enable_prometheus_metrics: bool = False
    prometheus_port: int = 9090


# Default monitoring configuration
default_config = MonitoringConfig(
    health_checks=HealthCheckConfig(),
    metrics=MetricsConfig(),
    alerts=AlertConfig()
)


def load_monitoring_config(config_dict: Optional[Dict[str, Any]] = None) -> MonitoringConfig:
    """Load monitoring configuration from dictionary."""
    if config_dict is None:
        return default_config

    # Parse health checks config
    health_config = config_dict.get("health_checks", {})
    health_checks = HealthCheckConfig(
        enabled=health_config.get("enabled", True),
        interval_seconds=health_config.get("interval_seconds", 300),
        timeout_seconds=health_config.get("timeout_seconds", 10),
        retry_attempts=health_config.get("retry_attempts", 3),
        retry_delay_seconds=health_config.get("retry_delay_seconds", 5),
        alert_on_failure=health_config.get("alert_on_failure", True),
        alert_threshold_consecutive_failures=health_config.get("alert_threshold_consecutive_failures", 3)
    )

    # Parse metrics config
    metrics_config = config_dict.get("metrics", {})
    metrics = MetricsConfig(
        enabled=metrics_config.get("enabled", True),
        retention_days=metrics_config.get("retention_days", 7),
        max_metrics_history=metrics_config.get("max_metrics_history", 10000),
        export_interval_seconds=metrics_config.get("export_interval_seconds", 3600),
        export_format=metrics_config.get("export_format", "json")
    )

    # Parse alerts config
    alerts_config = config_dict.get("alerts", {})
    alerts = AlertConfig(
        enabled=alerts_config.get("enabled", False),
        email_alerts=alerts_config.get("email_alerts", False),
        alert_email_recipients=alerts_config.get("alert_email_recipients", []),
        slack_webhook_url=alerts_config.get("slack_webhook_url"),
        alert_on_service_down=alerts_config.get("alert_on_service_down", True),
        alert_on_high_error_rate=alerts_config.get("alert_on_high_error_rate", True),
        error_rate_threshold=alerts_config.get("error_rate_threshold", 0.1),
        alert_cooldown_minutes=alerts_config.get("alert_cooldown_minutes", 60)
    )

    return MonitoringConfig(
        health_checks=health_checks,
        metrics=metrics,
        alerts=alerts,
        log_level=config_dict.get("log_level", "INFO"),
        enable_prometheus_metrics=config_dict.get("enable_prometheus_metrics", False),
        prometheus_port=config_dict.get("prometheus_port", 9090)
    )