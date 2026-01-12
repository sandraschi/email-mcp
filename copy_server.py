#!/usr/bin/env python3
import shutil

# Copy the full server.py to MCPB directory
shutil.copy2(
    'src/email_mcp/server.py',
    'mcp-server/src/email_mcp/server.py'
)

print("Full server.py copied to MCPB directory")