#!/usr/bin/env python3
"""
Build MCPB package for Email MCP Server

Creates a .mcpb file (ZIP archive) that can be dragged into Claude Desktop.
"""

import os
import zipfile
import sys
from pathlib import Path

def build_mcpb():
    """Build the MCPB package."""

    # Define paths
    root_dir = Path(__file__).parent
    mcp_server_dir = root_dir / "mcp-server"
    output_file = root_dir / "email-mcp.mcpb"

    if not mcp_server_dir.exists():
        print(f"Error: {mcp_server_dir} directory not found")
        print("Make sure the mcp-server directory exists with all required files")
        sys.exit(1)

    print(f"Building MCPB package from: {mcp_server_dir}")
    print(f"Output file: {output_file}")

    # Remove existing file if it exists
    if output_file.exists():
        output_file.unlink()
        print("Removed existing MCPB file")

    # Create ZIP file
    with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
        file_count = 0
        for file_path in mcp_server_dir.rglob('*'):
            if file_path.is_file():
                # Calculate relative path from mcp-server directory
                try:
                    relative_path = file_path.relative_to(root_dir)
                    zipf.write(file_path, relative_path)
                    print(f"  Added: {relative_path}")
                    file_count += 1
                except ValueError as e:
                    print(f"  Skipped: {file_path} - {e}")

        if file_count == 0:
            print("Warning: No files found to add to MCPB package")

    print(f"\nMCPB package created: {output_file}")
    try:
        print(f"Size: {output_file.stat().st_size} bytes")
    except OSError:
        print("Could not determine file size")

    # Verify the package contents
    print("\nVerifying package contents:")
    try:
        with zipfile.ZipFile(output_file, 'r') as zipf:
            file_list = sorted(zipf.namelist())
            for name in file_list:
                print(f"  {name}")
            print(f"\nTotal files: {len(file_list)}")
    except zipfile.BadZipFile:
        print("Error: Created file is not a valid ZIP archive")
        sys.exit(1)

    print("\nPackage ready for Claude Desktop!")
    print("Drag and drop the email-mcp.mcpb file into Claude Desktop settings.")
    print("\nMCPB Package Contents:")
    print("  * FastMCP 2.14.3 compliant server")
    print("  * Conversational tool returns")
    print("  * Comprehensive prompt templates:")
    print("    - System prompt with core capabilities")
    print("    - User guide with examples")
    print("    - Workflow automation templates")
    print("    - Troubleshooting guide")
    print("  * 40+ categorized examples")
    print("  * Zed extension configuration")
    print("  * Service configuration templates")
    print("\nFeatures:")
    print("  - Multi-service email support (SMTP, API, local, webhooks)")
    print("  - Intelligent service routing")
    print("  - Advanced inbox management")
    print("  - Comprehensive error handling")
    print("  - Rate limiting and batch processing")
    print("  - Real-time monitoring and health checks")
    print("\nFor advanced usage, refer to the complete repository:")
    print("https://github.com/sandraschi/email-mcp")

if __name__ == "__main__":
    build_mcpb()