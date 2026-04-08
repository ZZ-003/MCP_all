from mcp.server.fastmcp import FastMCP
import httpx
from typing import Optional, Dict, Any

mcp = FastMCP(name="Fetch Server", host="0.0.0.0", port=8000)


@mcp.tool()
async def fetch_url(
    url: str,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    body: Optional[str] = None,
    timeout: int = 30
) -> Dict[str, Any]:
    """
    Fetch content from a URL using HTTP request.
    
    Args:
        url: The URL to fetch
        method: HTTP method (GET, POST, PUT, DELETE, etc.)
        headers: Optional headers to include in the request
        body: Optional request body for POST/PUT requests
        timeout: Request timeout in seconds
    
    Returns:
        Dictionary containing status_code, headers, and content
    """
    try:
        # Create httpx client with timeout
        async with httpx.AsyncClient(timeout=timeout) as client:
            # Prepare request arguments
            request_args = {
                "method": method.upper(),
                "url": url,
                "headers": headers or {},
                "follow_redirects": True
            }
            
            # Add body if provided
            if body:
                request_args["content"] = body
            
            # Make the request
            response = await client.request(**request_args)
            
            # Return response data
            return {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "content": response.text,
                "url": str(response.url)
            }
    
    except httpx.RequestError as e:
        return {
            "error": f"Request failed: {str(e)}",
            "status_code": None,
            "headers": {},
            "content": "",
            "url": url
        }
    except Exception as e:
        return {
            "error": f"Unexpected error: {str(e)}",
            "status_code": None,
            "headers": {},
            "content": "",
            "url": url
        }

if __name__ == "__main__":
    mcp.run(transport="streamable-http")