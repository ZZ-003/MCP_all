import json
import asyncio
from tqdm import tqdm
from pathlib import Path


async def batch_code_repo_scan(scan_func, bench_dir: str, output_dir: str, max_concurrent: int = 5):
    bench_path = Path(bench_dir)
    if not bench_path.exists() or not bench_path.is_dir():
        raise ValueError(f"Benchmark directory {bench_dir} does not exist or is not a directory.")
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    semaphore = asyncio.Semaphore(max_concurrent)

    tqdm_bar = tqdm(total=len(list(bench_path.iterdir())), desc="Scanning repositories")
    async def scan_with_semaphore(project_dir: Path):
        async with semaphore:
            result = await scan_func(str(project_dir / "repo"))
            if result is None:
                return None
            # output_dir/output_path = f"./results/rq2/scan_with_intent_capability"
            result_path = output_path / f"{project_dir.name}.json"
            with open(result_path, "w") as f:
                json.dump(result, f, indent=2)
            tqdm_bar.update(1)
            return project_dir.name
    
    tasks = [scan_with_semaphore(project_dir) for project_dir in bench_path.iterdir()]
    completed = await asyncio.gather(*tasks, return_exceptions=True)
    
    for i, result in enumerate(completed):
        if result is None:
            continue
        if isinstance(result, Exception):
            project_name = list(bench_path.iterdir())[i].name
            print(f"Error scanning {project_name}: {result}")