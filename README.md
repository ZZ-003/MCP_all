# MCP_all

本仓库由四个核心目录组成：

- `MCPServerBenchmark`：CWE 漏洞检测基准（生成、服务启停、真值输出）
- `MCPToxBenchmark`：恶意工具描述基准（生成、服务启停、真值输出）
- `MCPSecAgent_for_vuln`：漏洞检测实验框架（RQ1/RQ2 + 结果评估）
- `MCPSecAgent_for_mali`：恶意检测实验框架（RQ1/RQ2 + 结果评估）


## 目录关系

```text
MCP_all/
├── MCPServerBenchmark/
├── MCPToxBenchmark/
├── MCPSecAgent_for_vuln/
└── MCPSecAgent_for_mali/
```

## 环境要求

- Python 3.12.12（建议）
- Linux/macOS Shell

安装两个检测框架依赖：

```bash
pip install -r requirements.txt
```

## 快速开始

配置好 MCPSecAgent_for_mali/.env 和 MCPSecAgent_for_vuln/.env 

### 漏洞扫描路线

```bash
cd path_to_project/MCPServerBenchmark 
sh setup.sh
cd path_to_project/MCPSecAgent_for_vuln 
python exp_rq1.py -m semant_guard 
python exp_rq2.py
cd path_to_project/MCPSecAgent_for_vuln/results_judge 
python 01devide_json.py 
python 02calculate_with_ltm.py  
python 03sum_of_num.py
```

### 恶意描述路线

```bash
cd path_to_project/MCPToxBenchmark  
sh setup.sh
cd path_to_project/MCPSecAgent_for_mali  
python exp_rq1.py -m semant_guard 
python exp_rq2.py
cd path_to_project/MCPSecAgent_for_mali/results_judge  
python 01devide_json.py 
python 02calculate_with_ltm.py  
python 03sum_of_num.py
```


---

## MCPServerBenchmark（漏洞基准）

### 介绍

`MCPServerBenchmark` 负责构建漏洞检测数据，包含仓库内 `mcp-*` 项目和 `gen-benchmark` 自动生成项目，并输出漏洞真值。

### 使用说明

```bash
cd path_to_project/MCPServerBenchmark
sh setup.sh
```

### 主要输出

- `output/ground_truth.json`
- `output/all_tool_info.json`

---

## MCPToxBenchmark（恶意描述基准）

### 介绍

`MCPToxBenchmark` 用恶意模板工具与 benign 工具组合生成测试服务，输出恶意真值（`Malicious`）。

### 使用说明

```bash
cd path_to_project/MCPToxBenchmark
sh setup.sh
```

### 主要输出

- `output/ground_truth.json`
- `output/all_tool_info.json`

---

## MCPSecAgent_for_vuln（漏洞检测）

### 介绍

支持三种方法：`llm_only`、`single_agent`、`semant_guard`，并提供 RQ2 intent-capability 方案与判分脚本。

### 使用说明

```bash
cd path_to_project/MCPSecAgent_for_vuln
```

RQ1（默认 benchmark：`/tmp/mcp-benchmark`）：

```bash
python exp_rq1.py -m llm_only
python exp_rq1.py -m single_agent
python exp_rq1.py -m semant_guard
```

RQ2：

```bash
python exp_rq2.py
```

可选参数（`exp_rq1.py` / `exp_rq2.py`）：

- `-i, --bench`
- `-o, --output`
- `-t, --max-concurrent`

后处理：

```bash
cd path_to_project/MCPSecAgent_for_vuln/results_judge
python 01devide_json.py
python 02calculate_with_ltm.py
python 03sum_of_num.py
```

---

## MCPSecAgent_for_mali（恶意检测）

### 介绍

整体结构与 vuln 版本同构，但输出目标是 `Maliciousness`。

### 使用说明

```bash
cd path_to_project/MCPSecAgent_for_mali
```

RQ1（默认 benchmark：`/tmp/mcp-benchmark-mali`）：

```bash
python exp_rq1.py -m llm_only
python exp_rq1.py -m single_agent
python exp_rq1.py -m semant_guard
```

RQ2：

```bash
python exp_rq2.py
```

后处理：

```bash
cd path_to_project/MCPSecAgent_for_mali/results_judge
python 01devide_json.py
python 02calculate_with_ltm.py
python 03sum_of_num.py
```

---

## MCPSecAgent 环境变量

- `LLM_ONLY_MODEL` / `LLM_ONLY_BASE_URL` / `LLM_ONLY_API_KEY`
- `SINGLE_AGENT_MODEL` / `SINGLE_AGENT_BASE_URL` / `SINGLE_AGENT_API_KEY`
- `AGENT_WITH_LTM_MODEL` / `AGENT_WITH_LTM_BASE_URL` / `AGENT_WITH_LTM_API_KEY`
- `CHIEF_ARCHITECT_MODEL` / `CHIEF_ARCHITECT_MODEL_BASE_URL` / `CHIEF_ARCHITECT_MODEL_API_KEY`
- `TAINT_SLEUTHS_MODEL` / `TAINT_SLEUTHS_MODEL_BASE_URL` / `TAINT_SLEUTHS_MODEL_API_KEY`
- `CRITIC_MODEL` / `CRITIC_MODEL_BASE_URL` / `CRITIC_MODEL_API_KEY`
