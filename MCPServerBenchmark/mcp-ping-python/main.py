import subprocess
import platform
from urllib.parse import urlparse
from mcp.server.fastmcp import FastMCP

# Create FastMCP server
mcp = FastMCP(name="Ping Tool", host="0.0.0.0", port=8000)


@mcp.tool()
def ping(host: str) -> str:
    """
    Pings a host and returns the result.
    
    Args:
        host: The hostname or URL to ping (e.g., 'google.com' or 'https://google.com')
    
    Returns:
        Ping results or error message
    """
    try:
        # Extract hostname from URL if needed
        hostname = host
        
        # If it's a full URL, extract the hostname
        if hostname.startswith("http://") or hostname.startswith("https://"):
            parsed_url = urlparse(hostname)
            hostname = parsed_url.hostname
        
        # Execute ping command (platform-specific)
        is_windows = platform.system() == "Windows"
        count_args = "-n" if is_windows else "-c"
        ping_command = f"ping {count_args} 4 {hostname}"
        
        # Run the ping command
        result = subprocess.getoutput(ping_command)
        
        if result.returncode != 0:
            return f"Failed to ping {hostname}:\n{result}"
        
        return f"Ping results for {hostname}:\n\n{result}"
        
    except subprocess.TimeoutExpired:
        return f"Failed to ping {host}: Command timed out"
    except Exception as e:
        return f"Failed to ping {host}:\n{str(e)}"


if __name__ == "__main__":
    # Run the server with HTTP transport
    mcp.run(transport="streamable-http")