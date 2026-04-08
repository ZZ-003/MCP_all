#!/usr/bin/env python3
"""
Document Converter MCP Server
A Model Context Protocol server that converts documents between formats using Pandoc and ImageMagick.
"""

import subprocess
import os
from mcp.server.fastmcp import FastMCP

# Initialize MCP server
mcp = FastMCP(name="Document Converter", host="0.0.0.0", port=8000)


def validate_file_path(file_path: str) -> bool:
    """Validate that the file path exists and is accessible"""
    return os.path.exists(file_path) and os.path.isfile(file_path)


@mcp.tool()
def convert_document(input_file: str, output_file: str, from_format: str = None, to_format: str = None) -> str:
    """
    Convert document between formats using Pandoc.

    Args:
        input_file: Path to the input document file
        output_file: Path to save the converted output file
        from_format: Input format (optional, Pandoc will detect if not provided)
        to_format: Output format (optional, detected from output_path extension if not provided)

    Returns:
        A message indicating success or failure
    """
    if not validate_file_path(input_file):
        return f"Error: Input file '{input_file}' does not exist or is not a file"

    # Build Pandoc command
    cmd = f"pandoc {input_file} -o {output_file}"

    if from_format:
        cmd += f" -f {from_format}"

    if to_format:
        cmd += f" -t {to_format}"

    try:
        status, output = subprocess.getstatusoutput(cmd)
        if status != 0:
            return f"Error during conversion: {output}"
        return f"Success: Document converted from '{input_file}' to '{output_file}'"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


@mcp.tool()
def convert_image(input_file: str, output_file: str) -> str:
    """
    Convert images between formats using ImageMagick's convert command.

    Args:
        input_file: Path to the input image file
        output_file: Path to save the converted output image

    Returns:
        A message indicating success or failure
    """
    if not validate_file_path(input_file):
        return f"Error: Input file '{input_file}' does not exist or is not a file"

    # Build ImageMagick convert command
    cmd = f"convert {input_file} {output_file}"

    try:
        # Run convert with shell=False for security
        status, output = subprocess.getstatusoutput(cmd)
        if status != 0:
            return f"Error during image conversion: {output}"
        return f"Success: Image converted from '{input_file}' to '{output_file}'"
    except subprocess.CalledProcessError as e:
        return f"Error during image conversion: {e.stderr}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
