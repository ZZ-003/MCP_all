from pathlib import Path


def setup_log_dir(pending_scan_repo_dir: str, method: str) -> Path:
    root_dir = Path(__file__).parent.parent
    root_log_dir = root_dir / "results" / "logs"
    root_log_dir.mkdir(parents=True, exist_ok=True)

    _path = Path(pending_scan_repo_dir)
    project_name = _path.name
    while project_name == "repo":
        _path = _path.parent
        project_name = _path.name
    log_dir = root_log_dir / method / project_name
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir