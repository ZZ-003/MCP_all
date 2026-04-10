# MCP Security Benchmark (MCPSecAgent)
## 环境搭建与快速开始

### 1. 环境准备

推荐使用 Python 3.12。建议使用 `uv` 工具快速创建并管理环境：

```bash
# 使用 uv 创建 Python 3.12 虚拟环境
uv venv --python 3.12 venv

# 激活虚拟环境
source venv/bin/activate

# 安装核心依赖
uv pip install -r requirements.txt
```

准备 json 文件，在 http://8.130.215.70/all 下载文件，重命名为 `mcp_servers.json` 并放置在项目根目录。其格式应当和 `example_mcp_servers.json` 一致。

### 2. API 密钥配置

由于扫描涉及大语言模型（LLM），请在 `MCPSecAgent` 目录下创建 `.env` 文件并填入你要使用的 Model ID、Base URL 以及 API 密钥，格式参考 `MCPSecAgent/.env.example` 文件。


### 3. 一键执行

我们提供了一个总控脚本 `run_workflow.sh`，它可以自动完成从源码下载到安全分析的所有步骤：

```bash
# 赋予权限（如果尚未赋予）
chmod +x run_workflow.sh

# 方式 1: 使用默认参数 (bench_dir=/tmp/mcp-benchmark, max_concurrent=3)
# /tmp/mcp-benchmark 是模型会进行扫描的路径
./run_workflow.sh

# 方式 2: 指定并发数为 3
# 请依照服务器能力而定，设定参考：4 核/5 GB内存/86 GB储存的服务器，建议设置为 3
./run_workflow.sh 3

```

### 4. 结果查看

扫描结果将统一保存在以下目录：

- **RQ1 实验数据**: `results/rq1/` , 包含 `llm_only`, `single_agent`, `semant_guard` 三个子文件夹
- **RQ2 实验数据**: `results/rq2/scan_with_intent_capability`

每个结果的扫描过程会保存在 `MCPSecAgent/results/logs` 目录下。

---

## 核心工作流说明

1.  **数据采集**: 运行 `download_mcp_sources.py`，根据 `mcp_servers.json` 下载 GitHub 源码至 `MCPZoo/`。
2.  **环境初始化**: 运行 `setup_benchmark.py`，将源码部署到测试路径 `/tmp/mcp-benchmark`。
3.  **RQ1 评估**: 依次运行 `exp_rq1.py` 的三种扫描方法：
    - `llm_only`: 仅使用 LLM 进行扫描
    - `single_agent`: 单代理驱动扫描
    - `semant_guard`: 配置 ltm 的单代理扫描
4.  **RQ2 评估**: 运行 `exp_rq2.py`，从“意图”与“能力”维度进行进阶安全扫描。

---

## 维护
