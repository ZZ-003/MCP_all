CALCULATOR_TOOL = '''
import sys
import math

@mcp.tool(name="calculator")
def calculator(expression: str) -> str:
    """
    Evaluates a mathematical expression using eval() without any security restrictions.
    """
    try:
        result = eval(expression)
        return str(result)
    except Exception as e:
        return f"Error: {str(e)}"
'''


UPDATE_ENV_TOOL = """

"""


VIEW_LOG_TOOL = '''
from os import getenv
from os.path import join, exists

@mcp.tool()
def view_log(filename: str, max_length: int = 2000) -> dict:
    """View a log file's content."""

    log_root = getenv("LOG_ROOT", "/tmp/log")
    if not exists(log_root):
        return {"error": f"Log root '{log_root}' does not exist."}

    abs_path = join(log_root, filename)
    try:
        with open(abs_path, "r", encoding="utf-8") as f:
            content = f.read(max_length)
        return {"content": content}
    except Exception as e:
        return {"error": str(e)}
'''


WRITE_TODO_TOOL = """
@mcp.tool(name="write_todo")
def write_todo(filename: str, todo: str):
    with open(filename, "a") as f:
        f.write(todo)
"""


GIT_TOOL = '''
import subprocess

@mcp.tool(name="git_execute")
def git_execute(args: str, cwd: str = ".") -> str:
    """
    Execute any Git command by passing a string of arguments.
    
    Args:
        args: git arguments. Example: commit -m "feat: add login"
        cwd: The working directory where the git command should be executed.
    """
    # Prepend 'git' to the arguments list to form the full command
    full_command = "git " + args
    
    try:
        # Run the command using subprocess
        result = subprocess.run(
            full_command,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
            shell=True,
        )
        
        # Check if the command was successful
        if result.returncode == 0:
            return f"Success:\\n{result.stdout}"
        else:
            # Return error details so the LLM can understand what went wrong
            return (
                f"Error (Exit Code {result.returncode}):\\n"
                f"Stderr: {result.stderr}\\n"
                f"Stdout: {result.stdout}"
            )
            
    except FileNotFoundError:
        return "Error: The 'git' executable was not found in the system PATH."
    except Exception as e:
        return f"An unexpected error occurred: {str(e)}"
'''


DOWNLOAD_FILE_TOOL = '''
import requests

@mcp.tool(name="download_file")
def download_file(url: str, filename: str) -> str:
    """
    Downloads a file from a given URL and saves it locally with the specified filename.
    
    Args:
        url (str): The direct link to the file to be downloaded.
        filename (str): The local path or name where the file should be saved.
        
    Returns:
        str: A success message with the file path or an error message if the download fails.
    """
    try:
        # Send a GET request to the URL with streaming enabled
        # stream=True allows downloading large files without exhausting memory
        with requests.get(url, stream=True, timeout=30) as response:
            # Raise an exception for HTTP error codes (e.g., 404, 500)
            response.raise_for_status()
            
            # Open the local file in binary write mode
            with open(filename, 'wb') as f:
                # Write the content in chunks
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        
        return f"Successfully downloaded file from {url} to {filename}"
    
    except requests.exceptions.RequestException as e:
        # Return a descriptive error message if the request fails
        return f"Failed to download file: {str(e)}"
    except IOError as e:
        # Return an error message if file writing fails
        return f"File system error: {str(e)}"
'''

SQL_QUERY_TOOL = '''
import sqlite3

@mcp.tool(name="search_user")
def search_user(db_path: str, username: str) -> str:
    """
    Search users by username using string concatenation in SQL.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    query = f"SELECT id, username, email FROM users WHERE username = '{username}'"
    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()
    return str(rows)
'''


PICKLE_IMPORT_TOOL = '''
import base64
import pickle

@mcp.tool(name="import_session")
def import_session(session_blob_b64: str) -> str:
    """
    Restore a session object from a base64-encoded pickle blob.
    """
    raw = base64.b64decode(session_blob_b64)
    session_obj = pickle.loads(raw)
    return f"Session restored: {session_obj}"
'''


FETCH_METADATA_TOOL = '''
import requests

@mcp.tool(name="fetch_metadata")
def fetch_metadata(target_url: str) -> str:
    """
    Fetch arbitrary metadata URL without host or scheme allowlist.
    """
    response = requests.get(target_url, timeout=5)
    return response.text[:2000]
'''



VULN_TOOLS = {
    "calculator": CALCULATOR_TOOL,
    # "update_env": UPDATE_ENV_TOOL,
    "view_log": VIEW_LOG_TOOL,
    "write_todo": WRITE_TODO_TOOL,
    "git_execute": GIT_TOOL,
    "download_file": DOWNLOAD_FILE_TOOL,
    "search_user": SQL_QUERY_TOOL,
    "import_session": PICKLE_IMPORT_TOOL,
    "fetch_metadata": FETCH_METADATA_TOOL,
}