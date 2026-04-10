#!/usr/bin/env python3
"""
Script to download MCP server source code from GitHub repositories.
"""

import argparse
import concurrent.futures
import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from urllib.parse import urlparse


def _normalize_source_url(url: str) -> str:
    url = (url or "").strip()
    if len(url) >= 2 and url[0] == "<" and url[-1] == ">":
        url = url[1:-1].strip()

    lowered = url.lower()
    if lowered.startswith("github.com/") or lowered.startswith("www.github.com/"):
        url = "https://" + url

    return url


def load_mcp_servers(json_path: str) -> list[dict]:
    """Load MCP server data from JSON file."""
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_domain(url: str) -> str:
    """Extract domain from URL."""
    parsed = urlparse(_normalize_source_url(url))
    return parsed.netloc.lower()


def is_github_url(url: str) -> bool:
    """Check if URL is a GitHub repository."""
    normalized = _normalize_source_url(url)

    if re.match(r"^git@github\.com:[^/]+/[^/]+", normalized, flags=re.IGNORECASE):
        return True

    if normalized.lower().startswith("ssh://"):
        parsed = urlparse(normalized)
        return parsed.hostname is not None and parsed.hostname.lower() == "github.com"

    return get_domain(normalized) == "github.com"


def sanitize_name(name: str) -> str:
    """Sanitize folder name for use as directory name."""
    # Remove or replace invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', name)
    sanitized = sanitized.strip(' .')
    if not sanitized:
        sanitized = 'unnamed'
    return sanitized[:100]  # Limit length


def extract_github_repo_info(url: str) -> tuple[str, str, str | None] | None:
    """Extract owner, repo name, and optional sub-path from GitHub URL."""
    normalized = _normalize_source_url(url)

    match = re.match(
        r"^git@github\.com:(?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?$",
        normalized,
        flags=re.IGNORECASE,
    )
    if match:
        return match.group("owner"), match.group("repo"), None

    if normalized.lower().startswith("ssh://"):
        parsed = urlparse(normalized)
        if parsed.hostname and parsed.hostname.lower() == "github.com":
            parts = [p for p in (parsed.path or "").split("/") if p]
            if len(parts) >= 2:
                owner, repo = parts[0], parts[1]
                if repo.lower().endswith(".git"):
                    repo = repo[:-4]
                return owner, repo, None
        return None

    parsed = urlparse(normalized)
    host = (parsed.hostname or "").lower()
    if host != "github.com":
        return None
    parts = [p for p in (parsed.path or "").split("/") if p]
    if len(parts) < 2:
        return None

    owner, repo = parts[0], parts[1]
    if repo.lower().endswith(".git"):
        repo = repo[:-4]
    
    sub_path = None
    if len(parts) > 4 and parts[2] == "tree":
        sub_path = "/".join(parts[4:])
        
    if not owner or not repo:
        return None
    return owner, repo, sub_path


def _self_check() -> None:
    cases: list[tuple[str, tuple[str, str, str | None]]] = [
        ("github.com/octocat/Hello-World", ("octocat", "Hello-World", None)),
        ("https://github.com/octocat/Hello-World.git", ("octocat", "Hello-World", None)),
        ("git@github.com:octocat/Hello-World.git", ("octocat", "Hello-World", None)),
        ("ssh://git@github.com/octocat/Hello-World.git", ("octocat", "Hello-World", None)),
        ("https://github.com/octocat/Hello-World/tree/main", ("octocat", "Hello-World", None)),
        ("https://github.com/modelcontextprotocol/servers/tree/main/src/fetch", ("modelcontextprotocol", "servers", "src/fetch")),
        ("<https://github.com/octocat/Hello-World>", ("octocat", "Hello-World", None)),
    ]
    for url, expected in cases:
        assert is_github_url(url), url
        assert extract_github_repo_info(url) == expected, url


def run_command(cmd: list[str], cwd: str = None, timeout: int = 240) -> tuple[bool, str]:
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
    """Clone a GitHub repository and optionally extract a sub-directory."""
    repo_info = extract_github_repo_info(url)
    if not repo_info:
        print(f"  [!] Could not parse GitHub URL: {url}")
        return False
    
    owner, repo, sub_path = repo_info
    
    # Target name: mcp-{last_part_of_url}
    url_parts = [p for p in url.rstrip("/").split("/") if p]
    last_url_part = url_parts[-1] if url_parts else repo
    target_dir = dest_dir / sanitize_name(f"mcp-{last_url_part}")
    
    if target_dir.exists():
        print(f"  [~] Already exists: {target_dir}")
        return True
    
    token = os.getenv("GITHUB_TOKEN")
    if token:
        clone_url = f"https://x-access-token:{token}@github.com/{owner}/{repo}.git"
    else:
        clone_url = f"https://github.com/{owner}/{repo}.git"
    
    if sub_path:
        # Clone to a temporary directory if extracting a sub-path
        temp_dir = dest_dir / f"temp-clone-{sanitize_name(repo)}-{os.getpid()}"
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
            
        print(f"  [*] Cloning full repo for sub-path extraction: {owner}/{repo}")
        success, output = run_command(['git', 'clone', '--depth', '1', clone_url, str(temp_dir)])
        
        if success:
            source_sub_dir = temp_dir / sub_path
            if source_sub_dir.exists():
                shutil.move(str(source_sub_dir), str(target_dir))
                shutil.rmtree(temp_dir)
                print(f"  [+] Successfully extracted sub-path {sub_path} to {target_dir}")
                return True
            else:
                print(f"  [-] Sub-path not found in repo: {sub_path}")
                shutil.rmtree(temp_dir)
                return False
        else:
            print(f"  [-] Clone failed for sub-path extraction: {output[:200]}")
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
            return False
    else:
        # Standard clone
        print(f"  [*] Cloning from GitHub: {owner}/{repo}")
        success, output = run_command(['git', 'clone', '--depth', '1', clone_url, str(target_dir)])
        
        if success:
            print(f"  [+] Successfully cloned to {target_dir}")
            return True
        else:
            print(f"  [-] Clone failed: {output[:200]}")
            return False


def download_source(entry: dict, dest_dir: Path) -> tuple[bool, bool, str | None]:
    """Download source based on URL type.
    
    Returns:
        tuple[bool, bool, str | None]: (success, is_skipped, mcp_name)
        - success: True if download succeeded, False otherwise
        - is_skipped: True if URL was skipped (not GitHub), False otherwise
        - mcp_name: The name of the created directory
    """
    url = entry.get('source', '').strip()
    server_name = entry.get('serverName', 'unknown')
    
    if not url:
        print(f"  [-] No source URL for: {server_name}")
        return False, True, None
    
    print(f"\n[{server_name}]")
    print(f"  URL: {url}")
    
    if not is_github_url(url):
        print(f"  [~] Skipped (not a GitHub URL)")
        return False, True, None

    repo_info = extract_github_repo_info(url)
    if not repo_info:
        print(f"  [~] Skipped (could not parse GitHub URL)")
        return False, True, None

    owner, repo, _ = repo_info
    
    # Calculate mcp_name here to return it
    url_parts = [p for p in url.rstrip("/").split("/") if p]
    last_url_part = url_parts[-1] if url_parts else repo
    mcp_name = sanitize_name(f"mcp-{last_url_part}")

    success = download_github_repo(url, dest_dir, server_name)
    return success, False, mcp_name


def process_entry(entry: dict, dest_dir: Path) -> tuple[bool, bool, dict | None, dict | None]:
    """Process a single entry: download or skip."""
    url = entry.get('source', '').strip()
    server_name = entry.get('serverName', 'unknown')

    if not url:
        return False, True, {
            "serverName": server_name,
            "source": entry.get('source', ''),
            "reason": "No source URL"
        }, None

    if not is_github_url(url):
        return False, True, {
            "serverName": server_name,
            "source": entry.get('source', ''),
            "reason": "Not a GitHub URL"
        }, None

    repo_info = extract_github_repo_info(url)
    if not repo_info:
        return False, True, {
            "serverName": server_name,
            "source": entry.get('source', ''),
            "reason": "Could not parse GitHub URL"
        }, None

    success, is_skipped, mcp_name = download_source(entry, dest_dir)
    
    if is_skipped:
        return False, True, {
            "serverName": server_name,
            "source": url,
            "reason": "Skipped during download"
        }, None

    if success:
        matched_info = {
            "serverName": server_name,
            "mcpName": mcp_name,
            "source": url,
        }
        return True, False, None, matched_info
    else:
        return False, False, {
            "serverName": server_name,
            "source": url,
            "reason": "Download failed"
        }, None

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Download MCP server source code.")
    parser.add_argument("--max-concurrent", type=int, default=3, help="Maximum concurrent downloads (default: 3)")
    args = parser.parse_args()

    script_dir = Path(__file__).parent
    json_path = script_dir / "mcp_servers.json"
    dest_dir = script_dir / "MCPZoo"
    skipped_json_path = script_dir / "skipped_servers.json"
    filtered_json_path = script_dir / "filtered_mcp_servers.json"
    
    if not json_path.exists():
        print(f"Error: JSON file not found: {json_path}")
        return
    
    dest_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Loading MCP servers from: {json_path}")
    servers = load_mcp_servers(str(json_path))
    print(f"Found {len(servers)} servers")
    
    print(f"Max Concurrent: {args.max_concurrent}")
    print(f"Destination: {dest_dir}")
    print("=" * 60)
    
    success_count = 0
    fail_count = 0
    skip_count = 0
    skipped_servers = []
    
    matched_repos = []
    max_downloads = 10000

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.max_concurrent) as executor:
        future_to_entry = {
            executor.submit(process_entry, entry, dest_dir): entry
            for entry in servers
        }
        
        for future in concurrent.futures.as_completed(future_to_entry):
            if success_count >= max_downloads:
                print(f"\n[!] Reached maximum download limit of {max_downloads}. Stopping...")
                # Cancel remaining futures
                for f in future_to_entry:
                    f.cancel()
                break

            try:
                success, is_skipped, skipped_info, matched_info = future.result()
                if is_skipped:
                    skip_count += 1
                    if skipped_info:
                        skipped_servers.append(skipped_info)
                elif success:
                    success_count += 1
                    if matched_info:
                        matched_repos.append(matched_info)
                        # Optional: Print progress every 100 downloads
                        if success_count % 100 == 0:
                            print(f"  >>> Progress: {success_count} downloads completed")
                else:
                    fail_count += 1
                    if skipped_info:
                        skipped_servers.append(skipped_info)

            except Exception as exc:
                print(f"Generated an exception: {exc}")
                fail_count += 1

    with open(filtered_json_path, 'w', encoding='utf-8') as f:
        json.dump(matched_repos, f, ensure_ascii=False, indent=2)
    print(f"\n[+] Filtered repos saved to: {filtered_json_path}")
    
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
    print(f"  Matched: {len(matched_repos)}")


if __name__ == "__main__":
    if os.getenv("MCP_URL_SELF_CHECK") == "1":
        _self_check()
    else:
        main()
