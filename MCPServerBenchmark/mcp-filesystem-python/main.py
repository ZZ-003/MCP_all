from mcp.server.fastmcp import FastMCP


mcp = FastMCP("Filesystem MCP", host="0.0.0.0", port=8000)


@mcp.tool()
def list_files(directory: str = ".") -> list:
    """List files in a directory."""
    from os import getenv, listdir
    from os.path import isdir, join, exists

    sandbox_root = getenv("SANDBOX_ROOT", "/tmp/sandbox")
    if not exists(sandbox_root):
        return [{"error": f"Sandbox root '{sandbox_root}' does not exist."}]

    abs_dir = join(sandbox_root, directory)
    try:
        files = listdir(directory)
        return [{"name": f, "is_dir": isdir(join(abs_dir, f))} for f in files]
    except Exception as e:
        return [{"error": str(e)}]


@mcp.tool()
def read_file(file_path: str, max_length: int = 2000) -> dict:
    """Read a file's content."""
    from os import getenv
    from os.path import join, exists

    sandbox_root = getenv("SANDBOX_ROOT", "/tmp/sandbox")
    if not exists(sandbox_root):
        return {"error": f"Sandbox root '{sandbox_root}' does not exist."}

    abs_path = join(sandbox_root, file_path)
    try:
        with open(abs_path, "r", encoding="utf-8") as f:
            content = f.read(max_length)
        return {"content": content}
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def write_file(file_path: str, content: str) -> dict:
    """Write content to a file."""
    from os import getenv, makedirs
    from os.path import join, exists, dirname

    sandbox_root = getenv("SANDBOX_ROOT", "/tmp/sandbox")
    if not exists(sandbox_root):
        return {"error": f"Sandbox root '{sandbox_root}' does not exist."}

    abs_path = join(sandbox_root, file_path)
    try:
        dir_name = dirname(abs_path)
        if not exists(dir_name):
            makedirs(dir_name)
        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(content)
        return {"message": "File written successfully."}
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    mcp.run(transport="streamable-http")