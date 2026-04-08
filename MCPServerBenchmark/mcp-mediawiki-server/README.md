<b>Outdated. Please use https://github.com/ProfessionalWiki/MediaWiki-MCP-Server instead!</b>

# MediaWiki MCP Server 🚀

[![smithery badge](https://smithery.ai/badge/@shiquda/mediawiki-mcp-server)](https://smithery.ai/server/@shiquda/mediawiki-mcp-server) ![](https://img.shields.io/badge/Python-3.13-informational?logo=&style=flat&logoColor=00bfff&color=005566&labelColor=00bfe6) ![](https://img.shields.io/badge/build%20with-uv-informational?logo=&style=flat&logoColor=333333&color=622867&labelColor=de5fe9) 

[![MseeP.ai Security Assessment Badge](https://mseep.net/pr/shiquda-mediawiki-mcp-server-badge.png)](https://mseep.ai/app/shiquda-mediawiki-mcp-server)

A MCP server that provides seamless interaction with Wikipedia's API. This tool allows you to search and retrieve Wikipedia content with LLMs 🤖!

<https://github.com/user-attachments/assets/b5d9c5f3-a60e-48ea-8b4b-f1a7524d4fbb>

## Features ✨

- 🔍 Search wiki pages with customizable wiki site. e.g. wikipedia.org, fandom.com, wiki.gg and more!
- 📖 Retrieve detailed page content

## Usage 💻

1. Ensure that uv is installed on your device.
2. Configure in your client:

The server defaults to using <https://en.wikipedia.org/>. Also, you can make the server search other wiki sites!

To see if a wiki site works with this server, check if it uses MediaWiki software (usually shown by an icon at the bottom of the site).

To check further and find the endpoint (usually the website's domain, like <https://mediawiki.org/>), check by going to base-url/rest.php/v1/page in a browser (like <https://noita.wiki.gg/rest.php/v1/page>) and see if the output looks right. If not, add '/w' to the base URL and try again.

Then, set this endpoint as --base-url:

![](/imgs/PixPin_2025-04-04_19-41-55.png)

Available transports: stdio (default), streamable-http (http://localhost/mcp), and SSE (http://localhost/sse). See -h for all options.

```bash
uvx mediawiki-mcp-server --h
usage: main.py [-h] [--base-url BASE_URL] [--http] [--sse] [--port PORT]

MediaWiki MCP Server

options:
  -h, --help           show this help message and exit
  --base-url BASE_URL  Base URL for the MediaWiki API (default: https://en.wikipedia.org/w/``)
  --http               Run server as streamable-http (instead of stdio)
  --sse                Run server as sse-http (instead of stdio)
  --port PORT          Default port for http transport (default: 8000)

```

Example JSON configurations:

```json
{
  "mcpServers": {
    "mediawiki-mcp-server": {
      "command": "uvx",
      "args": [
        "mediawiki-mcp-server",
        "--base-url", "https://example.com/"
      ],
      "env": {
        "HTTP_PROXY": "http://example.com:port"
      }
    }
  }
}
```

Or, if you want to run this server from source:

```json
{
  "mcpServers": {
    "mediawiki-mcp-server": {
      "command": "uv",
      "args": [
        "run",
        "--directory", 
        "mediawiki-mcp-server",
        "path/to/project/src/mediawiki_mcp_server",
        "--base-url", "https://example.com/"
      ],
      "env": {
        "HTTP_PROXY": "http://example.com:port"
      }
    }
  }
}
```

## Supported Tools 🛠

### Search

- `query`: Search term (preferably short and focused)
- `limit`: Maximum number of results to return (default: 5)

### Get Page

- `title`: The exact title of the Wikipedia page to retrieve

## Development 👨‍💻

```bash
npx @modelcontextprotocol/inspector uv run mediawiki-mcp-server
```

Here are some documents that might help:

- <https://www.mediawiki.org/api/rest_v1/>

## Contributing 🤝

This server is under development. Contributions are welcome! Feel free to submit issues and pull requests.

## Related Projects ♥️

- [Cherry Studio](https://github.com/CherryHQ/cherry-studio): A desktop client that supports for multiple LLM providers. MCP is supported.
