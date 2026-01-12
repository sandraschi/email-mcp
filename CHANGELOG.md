# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.1] - 2026-01-12

### Added
- AI Email Management Orchestrator - Server composition of email-mcp + local-llm-mcp
- `weed_trash` tool - AI-powered email cleanup and filtering
- `email_summarizer` tool - Smart inbox summaries grouped by topic and sender
- `smart_email_filter` tool - AI-generated email filtering rules
- Server composition architecture using FastMCP `mount()` for cross-server workflows
- Test framework for validating compositing functionality
- Safety-first design with `dry_run` modes for all destructive operations

### Changed
- Updated version to 0.2.1 to reflect new AI capabilities
- Enhanced README with orchestrator quick start and feature overview

### Technical
- Implemented FastMCP server composition patterns
- Created modular orchestrator architecture with clean separation of concerns
- Added cross-server tool calling capabilities
- Established AI email management as a new category of MCP applications

## [0.2.0] - 2026-01-12

### Added
- MCPB packaging support for Claude Desktop
- Complete manifest.json with tool definitions
- Glama integration with enhanced glama.json
- CI/CD pipeline with GitHub Actions
- Health monitoring and metrics collection system
- Comprehensive testing framework
- Code quality enforcement (Ruff, MyPy)
- Professional documentation and examples
- Monitoring stack with health checks and performance tracking

### Changed
- Updated project structure to src/ layout
- Enhanced README with standards compliance information
- Improved configuration management
- Updated version to reflect SOTA compliance

### Technical
- Added extensive prompt templates for Claude Desktop
- Implemented monitoring stack (health_check.py, metrics.py, config.py)
- Added comprehensive glama.json configuration
- Created CI/CD workflow with multi-version Python testing
- Established professional development standards

## [0.1.0] - 2026-01-01

### Added
- Initial multi-service email platform
- SMTP/IMAP support for standard providers
- Basic service configuration
- Core email sending and receiving functionality
- Async operations support