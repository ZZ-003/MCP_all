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

### 2. API 密钥配置

由于扫描涉及大语言模型（LLM），请在 MCPSecAgent 目录下创建 `.env` 文件并填入你的 API 密钥，参考 `.env.example` 文件。


### 3. 一键执行工作流

我们提供了一个总控脚本 `run_workflow.sh`，它可以自动完成从源码下载到安全分析的所有步骤：

```bash
# 赋予权限（如果尚未赋予）
chmod +x run_workflow.sh

# 方式 1: 使用默认参数 (bench_dir=/tmp/mcp-benchmark, max_concurrent=3)
./run_workflow.sh

# 方式 2: 指定并发数为 5
./run_workflow.sh /tmp/mcp-benchmark 5
```

---

## 核心工作流说明

总控脚本将依次执行以下四个步骤，每步生成的日志可在 `logs/` 目录下查看：

1.  **数据采集**: 运行 `download_mcp_sources.py`，根据 `mcp_servers.json` 下载 GitHub 源码至 `MCPZoo/`。
2.  **环境初始化**: 运行 `setup_benchmark.py`，将源码部署到测试路径 `/tmp/mcp-benchmark`。
3.  **RQ1 评估**: 依次运行 `exp_rq1.py` 的三种扫描方法：
    - `llm_only`: 仅使用 LLM 进行扫描
    - `single_agent`: 单代理驱动扫描
    - `semant_guard`: 基于语义的扫描
4.  **RQ2 评估**: 运行 `exp_rq2.py`，从“意图”与“能力”维度进行进阶安全扫描。

---

## 结果查看

扫描结果将统一保存在以下目录：

- **RQ1 实验数据**: `results/rq1/` (按方法子文件夹存放)
- **RQ2 实验数据**: `results/rq2/scan_with_intent_capability`
- **执行过程日志**: `logs/workflow_YYYYMMDD_HHMMSS/` 目录下可追溯每一步的详细输出。

---

## 维护

