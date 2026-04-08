import argparse
import os

import httpx
from loguru import logger
from mcp.server.fastmcp import FastMCP

USER_AGENT = "mediawiki-mcp-server/1.0"


class Config:
    base_url = "https://en.wikipedia.org/w/"
    path_prefix = "rest.php/v1/"


config = Config()
mcp = FastMCP("mediawiki-mcp-server")


def get_proxy_settings():
    """Get proxy settings from environment variables"""
    http_proxy = os.environ.get("HTTP_PROXY")

    return http_proxy


# helper function to make a request to the mediawiki api
async def make_request(path: str, params: dict) -> httpx.Response:
    headers = {
        "User-Agent": USER_AGENT,
    }
    url = config.base_url + config.path_prefix + path
    proxies = get_proxy_settings()
    async with httpx.AsyncClient(proxies=proxies, follow_redirects=True) as client:
        try:
            response = await client.get(url, headers=headers, params=params)
            if response.status_code in (301, 302, 303, 307, 308):
                final_response = await client.get(
                    response.headers["Location"], headers=headers
                )
                return final_response.json()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(e)
            return {"error": e}


# @mcp.tool()
# async def hello(name: str) -> str:
#     """Say hello to the user"""
#     return f"Hello, {name}!"


@mcp.tool()
async def search(query: str, limit: int = 5):
    """
    Search for a wiki page. The shorter the request, the better, preferably containing only the main term to be searched.
    Args:
        query: The query to search for
        limit: The number of results to return
    Returns:
        A list of pages that match the query
    """
    path = "search/page"
    params = {
        "q": query,
        "limit": limit,
    }
    response = await make_request(path, params)
    return response


@mcp.tool()
async def get_page(title: str):
    """Get a page from mediawiki.org
    Args:
        title: The title of the page to get, which can be found in title field of the search results
    Returns:
        The page content
    """
    path = f"page/{title}"
    response = await make_request(path, {})
    return response


def main():
    parser = argparse.ArgumentParser(description="MediaWiki MCP Server")
    parser.add_argument(
        "--base-url",
        default=config.base_url,
        help=f"Base URL for the MediaWiki API (default: {config.base_url}``)",
    )
    parser.add_argument(
        "--http",
        action="store_true",
        help="Run server as streamable-http (instead of stdio)",
    )
    parser.add_argument(
        "--sse",
        action="store_true",
        help="Run server as sse-http (instead of stdio)",
    )
    parser.add_argument(
        "--port",
        default=8000,
        type=int,
        help="Default port for http transport (default: 8000)",
    )
    args = parser.parse_args()
    config.base_url = (
        args.base_url if args.base_url.endswith("/") else args.base_url + "/"
    )
    transport = "stdio"
    if args.http or args.sse:
        mcp.settings.port = args.port
        mcp.settings.host = "0.0.0.0"
        if args.http:
            transport = "streamable-http"
        elif args.sse:
            transport = "sse"
    mcp.run(transport=transport)


if __name__ == "__main__":
    main()
