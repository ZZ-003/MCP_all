#!/usr/bin/env python3
"""
Kubernetes MCP Server with 5G Core Telecom Awareness
Exposes k8s cluster state + 5G NF-specific context to LLMs via MCP protocol.
"""

import asyncio
import json
import logging
import os
import sys
from typing import Any

# ── Windows asyncio fix ────────────────────────────────────────────────────
# On Windows, asyncio defaults to ProactorEventLoop which is incompatible with
# anyio's use of add_reader/add_writer (used by the MCP stdio transport).
# Force SelectorEventLoop on Windows before anything else starts.
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# ── Windows stdio binary-mode fix ─────────────────────────────────────────
# MCP stdio transport sends raw bytes. On Windows, sys.stdin/stdout open in
# text mode with \r\n translation by default, which corrupts the JSON-RPC
# framing. Switch them to binary mode here.
if sys.platform == "win32":
    import msvcrt
    msvcrt.setmode(sys.stdin.fileno(),  os.O_BINARY)
    msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)

from mcp.server import stdio as mcp_stdio
import mcp.types as types
# Server and InitializationOptions are re-exported from mcp.server; NotificationOptions lives in lowlevel
from mcp.server import Server, InitializationOptions, NotificationOptions
try:
    # FastMCP is required by `mcp dev` CLI; we create a global FastMCP instance named `mcp`
    from mcp.server.fastmcp import FastMCP
except Exception:  # pragma: no cover - FastMCP may not be present in older mcp versions
    FastMCP = None  # type: ignore

from k8s_client import K8sClient
from telecom_analyzer import TelecomAnalyzer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("k8s-5g-mcp")

# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------
app = Server("k8s-5g-mcp")
k8s = K8sClient()
analyzer = TelecomAnalyzer()


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------
@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        # ── Generic Kubernetes ──────────────────────────────────────────────
        types.Tool(
            name="k8s_get_pods",
            description=(
                "List Kubernetes pods with optional namespace and label filters. "
                "Returns pod name, namespace, status, node, restarts, age, and "
                "detected 5G Network Function type (AMF, SMF, UPF, NRF, …)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "namespace": {"type": "string", "description": "K8s namespace (omit for all)"},
                    "label_selector": {"type": "string", "description": "Label selector e.g. 'app=open5gs-amf'"},
                    "nf_type": {"type": "string", "description": "Filter by 5G NF type: AMF|SMF|UPF|NRF|AUSF|UDM|PCF|NSSF|BSF|CHF|AF|N3IWF|UPF"},
                },
            },
        ),
        types.Tool(
            name="k8s_get_deployments",
            description="List Kubernetes Deployments with replica status and 5G NF classification.",
            inputSchema={
                "type": "object",
                "properties": {
                    "namespace": {"type": "string"},
                    "label_selector": {"type": "string"},
                },
            },
        ),
        types.Tool(
            name="k8s_get_services",
            description=(
                "List Kubernetes Services including ClusterIP, NodePort, LoadBalancer. "
                "Identifies SBI (Service Based Interface) endpoints for 5G NFs."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "namespace": {"type": "string"},
                    "label_selector": {"type": "string"},
                },
            },
        ),
        types.Tool(
            name="k8s_get_pod_logs",
            description="Fetch recent logs from a pod/container. Annotates 5G-specific error patterns (N2, N4, Xn, SBI failures, NGAP errors, PFCP errors).",
            inputSchema={
                "type": "object",
                "required": ["pod_name", "namespace"],
                "properties": {
                    "pod_name": {"type": "string"},
                    "namespace": {"type": "string"},
                    "container": {"type": "string"},
                    "tail_lines": {"type": "integer", "default": 100},
                },
            },
        ),
        types.Tool(
            name="k8s_describe_pod",
            description="Full description of a pod including events, resource limits, and 5G interface annotations.",
            inputSchema={
                "type": "object",
                "required": ["pod_name", "namespace"],
                "properties": {
                    "pod_name": {"type": "string"},
                    "namespace": {"type": "string"},
                },
            },
        ),
        types.Tool(
            name="k8s_get_configmaps",
            description="List or retrieve ConfigMaps. Parses 5G NF configuration sections (NRF URI, PLMN, slices, DNN).",
            inputSchema={
                "type": "object",
                "properties": {
                    "namespace": {"type": "string"},
                    "name": {"type": "string", "description": "Specific ConfigMap name to retrieve"},
                },
            },
        ),
        types.Tool(
            name="k8s_get_nodes",
            description="List cluster nodes with capacity, allocatable resources, roles (control-plane / worker), and DPDK/SR-IOV labels relevant for UPF workloads.",
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="k8s_get_events",
            description="Fetch recent cluster events, optionally filtered by namespace or involved object.",
            inputSchema={
                "type": "object",
                "properties": {
                    "namespace": {"type": "string"},
                    "field_selector": {"type": "string"},
                    "limit": {"type": "integer", "default": 50},
                },
            },
        ),
        # ── 5G / Telecom specific ───────────────────────────────────────────
        types.Tool(
            name="fiveg_core_topology",
            description=(
                "Return a full 5G Core topology view: all detected NFs, their pods, "
                "SBI endpoints, inter-NF connectivity (NRF registration status), "
                "PLMN list, and slice (S-NSSAI) configuration extracted from ConfigMaps."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "namespace": {"type": "string", "description": "Namespace to scan (omit for all)"},
                },
            },
        ),
        types.Tool(
            name="fiveg_nf_status",
            description=(
                "Detailed status of a specific 5G Network Function: pod health, "
                "restart history, SBI port, NRF registration (if discoverable), "
                "recent error patterns from logs."
            ),
            inputSchema={
                "type": "object",
                "required": ["nf_type"],
                "properties": {
                    "nf_type": {"type": "string", "description": "AMF|SMF|UPF|NRF|AUSF|UDM|UDR|PCF|NSSF|BSF|CHF"},
                    "namespace": {"type": "string"},
                },
            },
        ),
        types.Tool(
            name="fiveg_slice_info",
            description=(
                "Extract network slice (S-NSSAI) information from ConfigMaps and "
                "Deployments across AMF, SMF, PCF, and NSSF."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "namespace": {"type": "string"},
                },
            },
        ),
        types.Tool(
            name="fiveg_health_check",
            description=(
                "Run a comprehensive 5G core health check: pod readiness, missing NFs, "
                "error log patterns (NGAP, PFCP, SBI, NAS, N2/N4), restart storms, "
                "and resource pressure. Returns a structured health report."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "namespace": {"type": "string"},
                },
            },
        ),
    ]


# ---------------------------------------------------------------------------
# Tool dispatch
# ---------------------------------------------------------------------------
@app.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[types.TextContent]:
    try:
        result = await _dispatch(name, arguments)
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
    except Exception as exc:
        logger.exception("Tool %s failed", name)
        return [types.TextContent(type="text", text=json.dumps({"error": str(exc)}))]


async def _dispatch(name: str, args: dict) -> Any:
    # Generic k8s tools
    if name == "k8s_get_pods":
        pods = await k8s.get_pods(
            namespace=args.get("namespace"),
            label_selector=args.get("label_selector"),
        )
        if nf_filter := args.get("nf_type"):
            pods = [p for p in pods if p.get("nf_type", "").upper() == nf_filter.upper()]
        return pods

    if name == "k8s_get_deployments":
        return await k8s.get_deployments(
            namespace=args.get("namespace"),
            label_selector=args.get("label_selector"),
        )

    if name == "k8s_get_services":
        return await k8s.get_services(
            namespace=args.get("namespace"),
            label_selector=args.get("label_selector"),
        )

    if name == "k8s_get_pod_logs":
        raw_logs = await k8s.get_pod_logs(
            pod_name=args["pod_name"],
            namespace=args["namespace"],
            container=args.get("container"),
            tail_lines=args.get("tail_lines", 100),
        )
        annotations = analyzer.annotate_logs(raw_logs)
        return {"logs": raw_logs, "telecom_annotations": annotations}

    if name == "k8s_describe_pod":
        return await k8s.describe_pod(args["pod_name"], args["namespace"])

    if name == "k8s_get_configmaps":
        cms = await k8s.get_configmaps(
            namespace=args.get("namespace"),
            name=args.get("name"),
        )
        return analyzer.parse_5g_configmaps(cms)

    if name == "k8s_get_nodes":
        return await k8s.get_nodes()

    if name == "k8s_get_events":
        return await k8s.get_events(
            namespace=args.get("namespace"),
            field_selector=args.get("field_selector"),
            limit=args.get("limit", 50),
        )

    # 5G telecom tools
    if name == "fiveg_core_topology":
        return await analyzer.build_topology(k8s, namespace=args.get("namespace"))

    if name == "fiveg_nf_status":
        return await analyzer.nf_status(k8s, args["nf_type"], namespace=args.get("namespace"))

    if name == "fiveg_slice_info":
        return await analyzer.slice_info(k8s, namespace=args.get("namespace"))

    if name == "fiveg_health_check":
        return await analyzer.health_check(k8s, namespace=args.get("namespace"))

    raise ValueError(f"Unknown tool: {name}")


# ---------------------------------------------------------------------------
# FastMCP adapter (for `mcp dev` CLI)
# ---------------------------------------------------------------------------
# The `mcp dev` CLI expects a global variable named mcp/server/app of type
# FastMCP. We expose a FastMCP instance that wraps the same tools/resources
# implemented above so this module works both with `python server.py` (stdio)
# and `mcp dev server.py` (FastMCP dev server).
if FastMCP is not None:
    mcp = FastMCP("k8s-5g-mcp")

    # ── Generic Kubernetes tools ───────────────────────────────────────────
    @mcp.tool("k8s_get_pods", description="List Kubernetes pods with optional namespace, label and NF-type filters.")
    async def tool_k8s_get_pods(namespace: str | None = None, label_selector: str | None = None, nf_type: str | None = None) -> list[dict]:
        pods = await k8s.get_pods(namespace=namespace, label_selector=label_selector)
        if nf_type:
            pods = [p for p in pods if p.get("nf_type", "").upper() == nf_type.upper()]
        return pods

    @mcp.tool("k8s_get_deployments", description="List Kubernetes Deployments with replica status and 5G NF classification.")
    async def tool_k8s_get_deployments(namespace: str | None = None, label_selector: str | None = None) -> list[dict]:
        return await k8s.get_deployments(namespace=namespace, label_selector=label_selector)

    @mcp.tool("k8s_get_services", description="List Kubernetes Services and detect SBI endpoints for 5G NFs.")
    async def tool_k8s_get_services(namespace: str | None = None, label_selector: str | None = None) -> list[dict]:
        return await k8s.get_services(namespace=namespace, label_selector=label_selector)

    @mcp.tool("k8s_get_pod_logs", description="Fetch recent logs from a pod/container and annotate 5G-specific patterns.")
    async def tool_k8s_get_pod_logs(pod_name: str, namespace: str, container: str | None = None, tail_lines: int = 100) -> dict:
        raw_logs = await k8s.get_pod_logs(pod_name=pod_name, namespace=namespace, container=container, tail_lines=tail_lines)
        annotations = analyzer.annotate_logs(raw_logs)
        return {"logs": raw_logs, "telecom_annotations": annotations}

    @mcp.tool("k8s_describe_pod", description="Describe a pod including events, resource limits, and 5G interface annotations.")
    async def tool_k8s_describe_pod(pod_name: str, namespace: str) -> dict:
        return await k8s.describe_pod(pod_name, namespace)

    @mcp.tool("k8s_get_configmaps", description="List or retrieve ConfigMaps and parse 5G NF configuration sections.")
    async def tool_k8s_get_configmaps(namespace: str | None = None, name: str | None = None) -> list[dict]:
        cms = await k8s.get_configmaps(namespace=namespace, name=name)
        return analyzer.parse_5g_configmaps(cms)

    @mcp.tool("k8s_get_nodes", description="List cluster nodes with roles and DPDK/SR-IOV relevant details.")
    async def tool_k8s_get_nodes() -> list[dict]:
        return await k8s.get_nodes()

    @mcp.tool("k8s_get_events", description="Fetch recent cluster events, optionally filtered by namespace or involved object.")
    async def tool_k8s_get_events(namespace: str | None = None, field_selector: str | None = None, limit: int = 50) -> list[dict]:
        return await k8s.get_events(namespace=namespace, field_selector=field_selector, limit=limit)

    # ── 5G / Telecom specific ──────────────────────────────────────────────
    @mcp.tool("fiveg_core_topology", description="Return a 5G Core topology view with NFs, SBI endpoints, PLMN and slices.")
    async def tool_fiveg_core_topology(namespace: str | None = None) -> dict:
        return await analyzer.build_topology(k8s, namespace=namespace)

    @mcp.tool("fiveg_nf_status", description="Detailed status of a specific 5G Network Function.")
    async def tool_fiveg_nf_status(nf_type: str, namespace: str | None = None) -> dict:
        return await analyzer.nf_status(k8s, nf_type, namespace=namespace)

    @mcp.tool("fiveg_slice_info", description="Extract S-NSSAI slice, PLMN and DNN information from ConfigMaps.")
    async def tool_fiveg_slice_info(namespace: str | None = None) -> dict:
        return await analyzer.slice_info(k8s, namespace=namespace)

    @mcp.tool("fiveg_health_check", description="Run a comprehensive 5G core health check and recommendations.")
    async def tool_fiveg_health_check(namespace: str | None = None) -> dict:
        return await analyzer.health_check(k8s, namespace=namespace)

    # ── Resources ──────────────────────────────────────────────────────────
    @mcp.resource(
        "https://5g.local/nf-reference",
        name="5G Network Functions Reference",
        description="3GPP TS 23.501 NF descriptions, SBI APIs, and interface mapping.",
        mime_type="application/json",
    )
    async def res_nf_reference() -> str:
        from telecom_analyzer import NF_REFERENCE
        return json.dumps(NF_REFERENCE, indent=2)

    @mcp.resource(
        "https://5g.local/interface-map",
        name="5G Interface Map",
        description="N1-N26 reference-point / service-based interface descriptions.",
        mime_type="application/json",
    )
    async def res_interface_map() -> str:
        from telecom_analyzer import INTERFACE_MAP
        return json.dumps(INTERFACE_MAP, indent=2)


# ---------------------------------------------------------------------------
# Resources  (static reference docs for 3GPP NF descriptions)
# ---------------------------------------------------------------------------
@app.list_resources()
async def list_resources() -> list[types.Resource]:
    return [
        types.Resource(
            uri="https://5g.local/nf-reference",
            name="5G Network Functions Reference",
            description="3GPP TS 23.501 NF descriptions, SBI APIs, and interface mapping.",
            mimeType="application/json",
        ),
        types.Resource(
            uri="https://5g.local/interface-map",
            name="5G Interface Map",
            description="N1-N26 reference-point / service-based interface descriptions.",
            mimeType="application/json",
        ),
    ]


@app.read_resource()
async def read_resource(uri: str) -> str:
    if uri == "https://5g.local/nf-reference":
        from telecom_analyzer import NF_REFERENCE
        return json.dumps(NF_REFERENCE, indent=2)
    if uri == "https://5g.local/interface-map":
        from telecom_analyzer import INTERFACE_MAP
        return json.dumps(INTERFACE_MAP, indent=2)
    raise ValueError(f"Unknown resource: {uri}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
async def main():
    """
    Entry point that supports two transports:
      - stdio (default): for local MCP clients like Claude Desktop
      - http streamable: expose an HTTP/SSE endpoint (path /mcp)

    Select transport with env MCP_TRANSPORT=stdio|http
    """
    transport = os.getenv("MCP_TRANSPORT", "stdio").lower()
    if transport == "http":
        # Lazy imports so stdio-only environments don't need these deps
        from starlette.applications import Starlette
        from starlette.responses import JSONResponse, PlainTextResponse
        from starlette.routing import Route, Mount
        from starlette.requests import Request
        import secrets
        from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
        from mcp.server.transport_security import TransportSecuritySettings
        import uvicorn

        # Configure optional settings via env
        retry_ms_env = os.getenv("MCP_HTTP_RETRY_MS")
        retry_ms = int(retry_ms_env) if retry_ms_env and retry_ms_env.isdigit() else None

        # Configure transport security (DNS rebinding protection) with
        # sensible local-development defaults. Can be overridden via env:
        #  - MCP_HTTP_ALLOWED_HOSTS: comma-separated list, supports ":*" wildcard for port
        #  - MCP_HTTP_ALLOWED_ORIGINS: comma-separated list, supports ":*" wildcard for port
        allowed_hosts_env = os.getenv("MCP_HTTP_ALLOWED_HOSTS")
        allowed_origins_env = os.getenv("MCP_HTTP_ALLOWED_ORIGINS")

        allowed_hosts = (
            [h.strip() for h in allowed_hosts_env.split(",") if h.strip()]
            if allowed_hosts_env
            else ["127.0.0.1:*", "localhost:*"]
        )
        allowed_origins = (
            [o.strip() for o in allowed_origins_env.split(",") if o.strip()]
            if allowed_origins_env
            else ["http://127.0.0.1:*", "http://localhost:*"]
        )

        security_settings = TransportSecuritySettings(
            enable_dns_rebinding_protection=True,
            allowed_hosts=allowed_hosts,
            allowed_origins=allowed_origins,
        )
        session_manager = StreamableHTTPSessionManager(
            app,
            event_store=None,          # can be swapped for a real store to enable resumability
            json_response=False,       # use SSE stream for responses (spec default)
            stateless=False,           # keep session across requests
            security_settings=security_settings,
            retry_interval=retry_ms,
        )

        async def mcp_endpoint(scope, receive, send):
            # Simple Bearer token authorization guard for HTTP transport
            # Enable by setting DANGEROUSLY_OMIT_AUTH!=true and providing MCP_HTTP_BEARER_TOKEN
            omit_auth = os.getenv("DANGEROUSLY_OMIT_AUTH", "false").lower() == "true"
            expected_token = os.getenv("MCP_HTTP_BEARER_TOKEN")

            if not omit_auth and expected_token:
                req = Request(scope, receive)
                auth_header = req.headers.get("authorization") or ""
                if not auth_header.lower().startswith("bearer "):
                    resp = JSONResponse(
                        {"error": "Unauthorized: missing bearer token"},
                        status_code=401,
                        headers={"WWW-Authenticate": "Bearer"},
                    )
                    await resp(scope, receive, send)
                    return

                provided = auth_header[7:].strip()
                if not secrets.compare_digest(provided, expected_token):
                    resp = JSONResponse(
                        {"error": "Unauthorized: invalid token"},
                        status_code=401,
                        headers={"WWW-Authenticate": "Bearer"},
                    )
                    await resp(scope, receive, send)
                    return

            # Either auth is disabled or token validated; proceed to MCP handler
            await session_manager.handle_request(scope, receive, send)

        async def health(_request):
            return JSONResponse({"status": "ok", "name": "k8s-5g-mcp"})

        async def ready(_request):
            return PlainTextResponse("ready")

        # Lifespan ensures the session manager task group is running
        import contextlib

        @contextlib.asynccontextmanager
        async def lifespan(_app):
            async with session_manager.run():
                yield

        http_app = Starlette(
            routes=[
                # Mount the ASGI endpoint directly so Starlette does not try to call it
                # as a request/response function (which would require a Request param).
                Mount("/mcp", app=mcp_endpoint),
                Route("/health", endpoint=health, methods=["GET"]),
                Route("/ready", endpoint=ready, methods=["GET"]),
                # basic root for convenience
                Route("/", endpoint=health, methods=["GET"]),
            ],
            lifespan=lifespan,
        )

        host = os.getenv("MCP_HTTP_HOST", "0.0.0.0")
        port = int(os.getenv("MCP_HTTP_PORT", "8000"))
        # IMPORTANT:
        # We are already inside an asyncio event loop (async def main()).
        # Calling uvicorn.run() here would internally call asyncio.run(),
        # which raises: "RuntimeError: asyncio.run() cannot be called from a running event loop".
        # Instead, construct a Server and await server.serve().
        config = uvicorn.Config(http_app, host=host, port=port, log_level="info")
        server = uvicorn.Server(config)
        await server.serve()
    else:
        # stdio transport (default)
        try:
            async with mcp_stdio.stdio_server() as (read_stream, write_stream):
                await app.run(
                    read_stream,
                    write_stream,
                    InitializationOptions(
                        server_name="k8s-5g-mcp",
                        server_version="1.0.0",
                        # Important: pass a NotificationOptions instance; passing None can cause
                        # AttributeError with mcp==1.26.0 (notification_options.resources_changed)
                        capabilities=app.get_capabilities(
                            notification_options=NotificationOptions(
                                tools_changed=False,
                                prompts_changed=False,
                                resources_changed=False,
                            ),
                            experimental_capabilities={},
                        ),
                    ),
                )
        except* Exception as eg:
            # Unwrap ExceptionGroup (Python 3.11+ / anyio TaskGroup errors on Windows)
            for exc in eg.exceptions:
                logger.error("MCP server error: %s: %s", type(exc).__name__, exc, exc_info=exc)
            raise SystemExit(1)


if __name__ == "__main__":
    # Re-enable logging to stderr so errors are visible in Claude Desktop logs
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stderr,
    )
    # Avoid mixing except and except* in the same try block (PEP 654 rule).
    # We nest try blocks so we can handle ExceptionGroup (from anyio/asyncio)
    # while still catching regular exceptions.
    try:
        try:
            asyncio.run(main())
        except* Exception as eg:
            for exc in eg.exceptions:
                print(f"FATAL: {type(exc).__name__}: {exc}", file=sys.stderr)
            raise SystemExit(1)
    except Exception as exc:
        print(f"FATAL: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(1)
    