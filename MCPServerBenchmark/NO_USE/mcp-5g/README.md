# Kubernetes MCP Server – 5G Core Edition

An MCP (Model Context Protocol) server that exposes your Kubernetes cluster state
with full 5G Core / telecom awareness to any MCP-compatible LLM (Claude Desktop, etc.).

---

## Features

### Generic Kubernetes tools
| Tool | Description |
|------|-------------|
| `k8s_get_pods` | List pods with optional NF-type filter |
| `k8s_get_deployments` | Deployment replicas and health |
| `k8s_get_services` | Services + SBI endpoint detection |
| `k8s_get_pod_logs` | Logs with 5G error annotations |
| `k8s_describe_pod` | Full pod spec + events |
| `k8s_get_configmaps` | ConfigMaps with 5G field extraction |
| `k8s_get_nodes` | Node capacity, DPDK/SR-IOV labels |
| `k8s_get_events` | Cluster events |

### 5G Telecom-specific tools
| Tool | Description |
|------|-------------|
| `fiveg_core_topology` | Full NF map: pods, SBI endpoints, PLMN, slices |
| `fiveg_nf_status` | Deep status for a specific NF (AMF/SMF/UPF/…) |
| `fiveg_upf_dataplane` | N3/N4/N6/N9 interfaces, DPDK, hugepages |
| `fiveg_slice_info` | S-NSSAI / DNN / PLMN from ConfigMaps |
| `fiveg_health_check` | Full health report with recommendations |

### MCP Resources (static reference)
- `5g://nf-reference` – 3GPP TS 23.501 NF descriptions, SBI APIs, interface mapping
- `5g://interface-map` – N1–N26 reference-point descriptions

---

## Supported 5G NFs (auto-detected from pod/deployment names & labels)

AMF · SMF · UPF · NRF · AUSF · UDM · UDR · PCF · NSSF · BSF · CHF · AF · N3IWF · SEPP

Tested against: **Open5GS**, **free5GC**, **SD-Core**, **OAI-CN5G**

---

## Requirements

- Python ≥ 3.11
- `kubectl` configured (in-cluster or local `~/.kube/config`)

## Installation

```bash
pip install -r requirements.txt
```

## Running the server (stdio)

```bash
python server.py
```

The server communicates over **stdio** using the MCP protocol.
It auto-detects in-cluster config, then falls back to `~/.kube/config`.
If neither is available it runs in **mock mode** with representative 5G core data.

---

## HTTP Streamable transport (network-accessible)

This project also supports the MCP Streamable HTTP transport, which exposes an HTTP/SSE
endpoint suitable for remote clients and deployments in Kubernetes.

Run locally:

```bash
export MCP_TRANSPORT=http
export MCP_HTTP_HOST=0.0.0.0
export MCP_HTTP_PORT=8000
# Require auth (recommended)
export DANGEROUSLY_OMIT_AUTH=false
export MCP_HTTP_BEARER_TOKEN="<your-long-random-token>"
python server.py
# Health checks
curl http://localhost:8000/health
curl http://localhost:8000/ready
```

MCP endpoint URL: `http://localhost:8000/mcp`

Register with Claude (example):

```bash
claude mcp add --transport http k8s-5g http://localhost:8000/mcp
```

Kubernetes deployment is provided under `k8s/`. The container image defaults to
`MCP_TRANSPORT=http` and exposes port 8000 with readiness/liveness probes.

Notes:
- Streamable HTTP requires Accept headers that include both `application/json` and
  `text/event-stream` for POST requests.
- The server uses SSE for streaming responses by default.

### Authentication (HTTP transport)

When running with `MCP_TRANSPORT=http`, this server supports a simple Bearer token guard on the `/mcp` endpoint.

- Set `DANGEROUSLY_OMIT_AUTH=false` (default in Docker image) to enforce auth
- Provide the secret in `MCP_HTTP_BEARER_TOKEN`
- Health endpoints (`/health`, `/ready`) remain unauthenticated

Examples:

```bash
# Start server locally with a token
export MCP_TRANSPORT=http
export DANGEROUSLY_OMIT_AUTH=false
export MCP_HTTP_BEARER_TOKEN="s3cret-EXAMPLE-TOKEN"
python server.py

# Unauthorized request (401)
curl -i -X POST \
  -H 'Accept: application/json, text/event-stream' \
  -H 'Content-Type: application/json' \
  --data '{"jsonrpc":"2.0","id":"1","method":"initialize","params":{}}' \
  http://localhost:8000/mcp

# Authorized request (will advance handshake rather than 401)
curl -i -X POST \
  -H 'Authorization: Bearer s3cret-EXAMPLE-TOKEN' \
  -H 'Accept: application/json, text/event-stream' \
  -H 'Content-Type: application/json' \
  --data '{"jsonrpc":"2.0","id":"1","method":"initialize","params":{}}' \
  http://localhost:8000/mcp
```

Kubernetes:

```bash
# Create secret with your token
kubectl -n mcp5g create secret generic mcp5g-auth \
  --from-literal=token="s3cret-EXAMPLE-TOKEN"

# Apply namespace/RBAC/deployment
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/rbac.yaml
kubectl apply -f k8s/deployment.yaml
```

Security notes:
- Use a long, random token. Rotate via Secret update and rollout.
- For public endpoints, place this behind TLS and a network perimeter/proxy.
- For advanced OAuth 2.1 integration, consider wiring `mcp.server.auth` as a future enhancement.

---

## Claude Desktop integration (stdio)

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "k8s-5g": {
      "command": "python",
      "args": ["/absolute/path/to/k8s-5g-mcp/server.py"],
      "env": {
        "KUBECONFIG": "/home/youruser/.kube/config"
      }
    }
  }
}
```


---

## Example LLM prompts

```
Show me the full 5G core topology in my cluster.
What is the health status of the AMF?
Are there any PFCP errors in the UPF logs?
What S-NSSAIs (slices) are configured?
Is DPDK enabled on my UPF node?
Run a full 5G core health check and give me recommendations.
Show me all pods in the open5gs namespace and classify them by NF type.
```

---

## Architecture

```
LLM (Claude Desktop / any MCP client)
        │  MCP (stdio / JSON-RPC 2.0)
        ▼
┌─────────────────────────────────────┐
│  server.py  (MCP Server)            │
│  ┌───────────┐  ┌─────────────────┐ │
│  │ k8s_client│  │telecom_analyzer │ │
│  │  (k8s SDK)│  │  (3GPP logic)   │ │
│  └─────┬─────┘  └────────┬────────┘ │
└────────┼─────────────────┼──────────┘
         │ kubernetes API  │ ConfigMap / log parsing
         ▼
   Kubernetes Cluster
   (5G Core workloads: AMF, SMF, UPF, NRF, …)
```

---

## Mock mode

If no `kubeconfig` is found, the server starts in **mock mode** and returns
a representative open5gs-style cluster with 8 NFs, DPDK on worker-2,
and pre-seeded log entries for testing.
