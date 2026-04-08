import sys
import os
from langchain.tools import tool


def execute_python_code(project_dir: str, code: str) -> dict:
    """Execute Python code and return the result in a JSON format."""
    import io
    import contextlib
    import traceback

    # Capture stdout and stderr
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()
    
    try:
        # Redirect stdout and stderr
        with contextlib.redirect_stdout(stdout_capture), \
             contextlib.redirect_stderr(stderr_capture):
            # Execute the code
            old_cwd = os.getcwd()
            old_sys_path = sys.path.copy()

            try:
                os.chdir(project_dir)
                sys.path.insert(0, project_dir)
                exec(code, {})
            finally:
                # 恢复环境
                os.chdir(old_cwd)
                sys.path = old_sys_path
        
        return {
            "success": True,
            "stdout": stdout_capture.getvalue(),
            "stderr": stderr_capture.getvalue(),
            "error": None
        }
    
    except Exception as e:
        # Capture the full traceback
        error_traceback = traceback.format_exc()
        
        return {
            "success": False,
            "stdout": stdout_capture.getvalue(),
            "stderr": stderr_capture.getvalue(),
            "error": f"{type(e).__name__}: {str(e)}\n{error_traceback}"
        }


def get_python_tool(work_dir: str):
    @tool(
        "execute_python_code",
        description="Executes Python code to verify vulnerabilities or interact with the target environment. "
                    "Use this tool to run Proof-of-Concept (PoC) scripts, send HTTP requests, inspect responses, "
                    "and analyze target behavior. \n"
                    "KEY FEATURES:\n"
                    "1. Pre-installed libraries: Standard libraries plus 'requests' are available.\n"
                    "2. Output capture: STDOUT and STDERR are captured. ALWAYS verify results by printing specific keywords "
                    "(e.g., 'print(response.status_code)', 'print(response.text)').\n"
                    "3. Environment: The code runs in the current workspace. You can access local files or the network.\n"
                    "4. Persistence: If 'filename' is provided, the code is saved to that file before execution. "
                    "This is ESSENTIAL for complex PoCs that might need to be run externally later or referenced."
    )
    def execute_python_code_tool(code: str, filename: str=None) -> str:
        if filename is not None:
            file_path = os.path.join(work_dir, filename)
            with open(file_path, "w") as f:
                f.write(code)
        result = execute_python_code(work_dir, code)
        status = "Success" if result["success"] else "Failure"
        response = f"Status: {status}\n"
        response += f"## stdout\n{result['stdout']}\n"
        response += f"## stderr\n{result['stderr']}\n"
        if result['error']:
            response += f"## error: \n{result['error']}\n"
        return response
    return execute_python_code_tool