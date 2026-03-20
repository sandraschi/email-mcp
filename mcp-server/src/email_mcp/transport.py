"""
FastMCP 2.14.4+ Dual Transport Configuration

Standard module for all MCP servers in d:/Dev/repos.
Provides unified transport configuration for STDIO and HTTP Streamable modes.
"""

import argparse
import asyncio
import logging
import os
from typing import Literal, Optional

logger = logging.getLogger(__name__)

TransportType = Literal["stdio", "http", "sse"]

# Environment variable standards
ENV_TRANSPORT = "MCP_TRANSPORT"  # stdio | http
ENV_HOST = "MCP_HOST"  # default: 127.0.0.1
ENV_PORT = "MCP_PORT"  # default: 10813
ENV_PATH = "MCP_PATH"  # default: /mcp (HTTP only)


def get_transport_config() -> dict:
    return {
        "transport": os.getenv(ENV_TRANSPORT, "stdio").lower(),
        "host": os.getenv(ENV_HOST, "127.0.0.1"),
        "port": int(os.getenv(ENV_PORT, "10813")),
        "path": os.getenv(ENV_PATH, "/mcp"),
    }


def create_argument_parser(server_name: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=f"{server_name} - FastMCP 2.14.4+ Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    transport_group = parser.add_mutually_exclusive_group()
    transport_group.add_argument(
        "--stdio", action="store_true", help="Run in STDIO (JSON-RPC) mode (default)"
    )
    transport_group.add_argument(
        "--http",
        action="store_true",
        help="Run in HTTP Streamable mode (FastMCP 2.14.4+)",
    )

    parser.add_argument(
        "--host",
        default=None,
        help=f"Host to bind to (default: {ENV_HOST} or 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help=f"Port to listen on (default: {ENV_PORT} or 10813)",
    )
    parser.add_argument(
        "--path",
        default=None,
        help=f"HTTP endpoint path (default: {ENV_PATH} or /mcp)",
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    return parser


def resolve_transport(args: argparse.Namespace) -> TransportType:
    if args.http:
        return "http"
    elif args.stdio:
        return "stdio"
    else:
        env_transport = os.getenv(ENV_TRANSPORT, "stdio").lower()
        return env_transport if env_transport in ("stdio", "http") else "stdio"  # type: ignore


def resolve_config(args: argparse.Namespace) -> dict:
    env_config = get_transport_config()
    return {
        "transport": resolve_transport(args),
        "host": args.host if args.host is not None else env_config["host"],
        "port": args.port if args.port is not None else env_config["port"],
        "path": args.path if args.path is not None else env_config["path"],
    }


async def run_server_async(
    mcp_app, args: Optional[argparse.Namespace] = None, server_name: str = "mcp-server"
) -> None:
    if args is None:
        parser = create_argument_parser(server_name)
        args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    config = resolve_config(args)
    transport = config["transport"]

    logger.info(f"Starting {server_name} v1.0.0")
    logger.info(f"Transport: {transport.upper()}")

    try:
        if transport == "stdio":
            await mcp_app.run_stdio_async()
        elif transport == "http":
            await mcp_app.run_http_async(
                host=config["host"], port=config["port"], path=config["path"]
            )
    except asyncio.CancelledError:
        logger.info(f"{server_name} shutdown requested")
    except Exception as e:
        logger.error(f"{server_name} failed: {e}", exc_info=True)
        raise


def run_server(
    mcp_app, args: Optional[argparse.Namespace] = None, server_name: str = "mcp-server"
) -> None:
    asyncio.run(run_server_async(mcp_app, args, server_name))
