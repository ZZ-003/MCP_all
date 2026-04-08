from mcp.server.fastmcp import FastMCP


mcp = FastMCP("Python Runtime MCP", host="0.0.0.0", port=8000)


@mcp.tool()
def execute_code(code: str) -> dict:
    """Execute arbitrary Python code and return the output or error."""
    import io
    import contextlib

    output = io.StringIO()
    try:
        with contextlib.redirect_stdout(output):
            exec(code, {})
        return {"output": output.getvalue()}
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    mcp.run(transport="streamable-http")