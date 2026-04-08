#!/usr/bin/env python3
"""
Script to download MCP server source code from GitHub repositories.
"""

import json
import re
import subprocess
from pathlib import Path
from urllib.parse import urlparse


def load_mcp_servers(json_path: str) -> list[dict]:
    """Load MCP server data from JSON file."""
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_domain(url: str) -> str:
    """Extract domain from URL."""
    parsed = urlparse(url)
    return parsed.netloc.lower()


def is_github_url(url: str) -> bool:
    """Check if URL is a GitHub repository."""
    return 'github.com' in get_domain(url)


def sanitize_name(name: str) -> str:
    """Sanitize folder name for use as directory name."""
    # Remove or replace invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', name)
    sanitized = sanitized.strip(' .')
    if not sanitized:
        sanitized = 'unnamed'
    return sanitized[:100]  # Limit length


def extract_github_repo_info(url: str) -> tuple[str, str] | None:
    """Extract owner and repo name from GitHub URL."""
    # Handle various GitHub URL formats
    patterns = [
        r'github\.com/([^/]+)/([^/]+)/?',
        r'github\.com/([^/]+)/([^/]+)/.*',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1), match.group(2)
    return None


def run_command(cmd: list[str], cwd: str = None, timeout: int = 300) -> tuple[bool, str]:
    """Run a shell command and return success status and output."""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.returncode == 0, result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return False, "Command timed out"
    except Exception as e:
        return False, str(e)


def download_github_repo(url: str, dest_dir: Path, server_name: str) -> bool:
    """Clone a GitHub repository."""
    repo_info = extract_github_repo_info(url)
    if not repo_info:
        print(f"  [!] Could not parse GitHub URL: {url}")
        return False
    
    owner, repo = repo_info
    clone_url = f"https://github.com/{owner}/{repo}.git"
    target_dir = dest_dir / sanitize_name(f"mcp-{repo}")
    
    if target_dir.exists():
        print(f"  [~] Already exists: {target_dir}")
        return True
    
    print(f"  [*] Cloning from GitHub: {owner}/{repo}")
    success, output = run_command(['git', 'clone', '--depth', '1', clone_url, str(target_dir)])
    
    if success:
        print(f"  [+] Successfully cloned to {target_dir}")
        return True
    else:
        print(f"  [-] Clone failed: {output[:200]}")
        return False


def download_source(entry: dict, dest_dir: Path) -> tuple[bool, bool]:
    """Download source based on URL type.
    
    Returns:
        tuple[bool, bool]: (success, is_skipped)
        - success: True if download succeeded, False otherwise
        - is_skipped: True if URL was skipped (not GitHub), False otherwise
    """
    url = entry.get('source', '').strip()
    server_name = entry.get('serverName', 'unknown')
    
    if not url:
        print(f"  [-] No source URL for: {server_name}")
        return False, True
    
    print(f"\n[{server_name}]")
    print(f"  URL: {url}")
    
    # Only process GitHub URLs, skip others
    if is_github_url(url):
        return download_github_repo(url, dest_dir, server_name), False
    else:
        print(f"  [~] Skipped (not a GitHub URL)")
        return False, True


def main():
    """Main entry point."""
    script_dir = Path(__file__).parent
    json_path = script_dir / "mcp_servers.json"
    dest_dir = script_dir / "MCPZoo"
    skipped_json_path = script_dir / "skipped_servers.json"
    
    if not json_path.exists():
        print(f"Error: JSON file not found: {json_path}")
        return
    
    dest_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Loading MCP servers from: {json_path}")
    servers = load_mcp_servers(str(json_path))
    print(f"Found {len(servers)} servers")
    print(f"Destination: {dest_dir}")
    print("=" * 60)
    
    success_count = 0
    fail_count = 0
    skip_count = 0
    skipped_servers = []
    
    for i, entry in enumerate(servers, 1):
        print(f"\n[{i}/{len(servers)}]")
        success, is_skipped = download_source(entry, dest_dir)
        
        if is_skipped:
            skip_count += 1
            skipped_servers.append({
                "serverName": entry.get('serverName', 'unknown'),
                "source": entry.get('source', ''),
                "reason": "Not a GitHub URL"
            })
        elif success:
            success_count += 1
        else:
            fail_count += 1
    
    # Save skipped servers to JSON file
    with open(skipped_json_path, 'w', encoding='utf-8') as f:
        json.dump(skipped_servers, f, ensure_ascii=False, indent=2)
    print(f"\n[~] Skipped servers saved to: {skipped_json_path}")
    
    print("\n" + "=" * 60)
    print("Summary:")
    print(f"  Successful: {success_count}")
    print(f"  Failed: {fail_count}")
    print(f"  Skipped: {skip_count}")
    print(f"  Total: {len(servers)}")


if __name__ == "__main__":
    main()
