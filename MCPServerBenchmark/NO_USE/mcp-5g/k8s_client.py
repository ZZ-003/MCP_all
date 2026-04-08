"""
Kubernetes client – thin async wrapper around the official kubernetes-client/python SDK.
Falls back to a mock mode when no kubeconfig / in-cluster config is available
so the MCP server remains testable without a live cluster.
"""

from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("k8s-client")

# Try to import the official k8s SDK; if missing we use a minimal stub.
try:
    from kubernetes import client as k8s_client, config as k8s_config
    from kubernetes.client.rest import ApiException

    def _load_config():
        try:
            k8s_config.load_incluster_config()
            logger.info("Loaded in-cluster kubeconfig")
        except Exception:
            k8s_config.load_kube_config()
            logger.info("Loaded local kubeconfig")

    _load_config()
    _REAL_K8S = True
except Exception as exc:
    logger.warning("kubernetes SDK not available or no config found (%s) – running in MOCK mode", exc)
    _REAL_K8S = False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
NF_KEYWORDS = {
    "amf": ["amf", "access-management"],
    "smf": ["smf", "session-management"],
    "upf": ["upf", "user-plane"],
    "nrf": ["nrf", "network-repository"],
    "ausf": ["ausf", "auth"],
    "udm": ["udm", "unified-data-management"],
    "udr": ["udr", "unified-data-repository"],
    "pcf": ["pcf", "policy-control"],
    "nssf": ["nssf", "slice-selection"],
    "bsf": ["bsf", "binding-support"],
    "chf": ["chf", "charging"],
    "af":  ["af", "application-function"],
    "n3iwf": ["n3iwf", "non-3gpp"],
    "sepp": ["sepp", "security-edge"],
}


def _detect_nf_type(name: str, labels: dict) -> str:
    text = (name + " " + " ".join(str(v) for v in labels.values())).lower()
    for nf, kws in NF_KEYWORDS.items():
        if any(kw in text for kw in kws):
            return nf.upper()
    return "UNKNOWN"


def _age(ts) -> str:
    if ts is None:
        return "unknown"
    if isinstance(ts, str):
        return ts
    now = datetime.now(timezone.utc)
    delta = now - ts.replace(tzinfo=timezone.utc) if ts.tzinfo is None else now - ts
    s = int(delta.total_seconds())
    if s < 3600:
        return f"{s // 60}m"
    if s < 86400:
        return f"{s // 3600}h"
    return f"{s // 86400}d"


def _run_sync(fn, *args, **kwargs):
    """Run a blocking k8s SDK call in a thread pool.

    Uses get_running_loop() (not get_event_loop()) so it works correctly
    on Windows where get_event_loop() may return a different/closed loop.
    """
    loop = asyncio.get_running_loop()
    return loop.run_in_executor(None, lambda: fn(*args, **kwargs))


# ---------------------------------------------------------------------------
# K8sClient
# ---------------------------------------------------------------------------
class K8sClient:
    def __init__(self):
        if _REAL_K8S:
            self._core = k8s_client.CoreV1Api()
            self._apps = k8s_client.AppsV1Api()
        else:
            self._core = None
            self._apps = None

    # ── Pods ─────────────────────────────────────────────────────────────────
    async def get_pods(self, namespace: str | None = None, label_selector: str | None = None) -> list[dict]:
        if not _REAL_K8S:
            return _mock_pods()

        kwargs: dict = {}
        if label_selector:
            kwargs["label_selector"] = label_selector

        if namespace:
            resp = await _run_sync(self._core.list_namespaced_pod, namespace, **kwargs)
        else:
            resp = await _run_sync(self._core.list_pod_for_all_namespaces, **kwargs)

        pods = []
        for p in resp.items:
            labels = p.metadata.labels or {}
            restarts = sum(
                (cs.restart_count for cs in (p.status.container_statuses or [])), 0
            )
            pods.append({
                "name": p.metadata.name,
                "namespace": p.metadata.namespace,
                "phase": p.status.phase,
                "ready": _pod_ready(p),
                "node": p.spec.node_name,
                "restarts": restarts,
                "age": _age(p.metadata.creation_timestamp),
                "labels": labels,
                "nf_type": _detect_nf_type(p.metadata.name, labels),
                "ip": p.status.pod_ip,
            })
        return pods

    # ── Deployments ──────────────────────────────────────────────────────────
    async def get_deployments(self, namespace: str | None = None, label_selector: str | None = None) -> list[dict]:
        if not _REAL_K8S:
            return _mock_deployments()

        kwargs: dict = {}
        if label_selector:
            kwargs["label_selector"] = label_selector

        if namespace:
            resp = await _run_sync(self._apps.list_namespaced_deployment, namespace, **kwargs)
        else:
            resp = await _run_sync(self._apps.list_deployment_for_all_namespaces, **kwargs)

        result = []
        for d in resp.items:
            labels = d.metadata.labels or {}
            result.append({
                "name": d.metadata.name,
                "namespace": d.metadata.namespace,
                "replicas": d.spec.replicas,
                "ready_replicas": d.status.ready_replicas or 0,
                "available_replicas": d.status.available_replicas or 0,
                "age": _age(d.metadata.creation_timestamp),
                "labels": labels,
                "nf_type": _detect_nf_type(d.metadata.name, labels),
            })
        return result

    # ── Services ─────────────────────────────────────────────────────────────
    async def get_services(self, namespace: str | None = None, label_selector: str | None = None) -> list[dict]:
        if not _REAL_K8S:
            return _mock_services()

        kwargs: dict = {}
        if label_selector:
            kwargs["label_selector"] = label_selector

        if namespace:
            resp = await _run_sync(self._core.list_namespaced_service, namespace, **kwargs)
        else:
            resp = await _run_sync(self._core.list_service_for_all_namespaces, **kwargs)

        result = []
        for s in resp.items:
            labels = s.metadata.labels or {}
            ports = [
                {
                    "name": p.name,
                    "port": p.port,
                    "target_port": str(p.target_port),
                    "protocol": p.protocol,
                }
                for p in (s.spec.ports or [])
            ]
            result.append({
                "name": s.metadata.name,
                "namespace": s.metadata.namespace,
                "type": s.spec.type,
                "cluster_ip": s.spec.cluster_ip,
                "external_ip": (s.status.load_balancer.ingress or [{}])[0].get("ip") if s.spec.type == "LoadBalancer" else None,
                "ports": ports,
                "labels": labels,
                "nf_type": _detect_nf_type(s.metadata.name, labels),
                "sbi_endpoint": _detect_sbi(s),
            })
        return result

    # ── Pod logs ─────────────────────────────────────────────────────────────
    async def get_pod_logs(self, pod_name: str, namespace: str, container: str | None = None, tail_lines: int = 100) -> str:
        if not _REAL_K8S:
            return _mock_logs(pod_name)

        kwargs: dict = {"tail_lines": tail_lines}
        if container:
            kwargs["container"] = container
        try:
            return await _run_sync(
                self._core.read_namespaced_pod_log,
                pod_name,
                namespace,
                **kwargs,
            )
        except Exception as exc:
            return f"Error fetching logs: {exc}"

    # ── Describe pod ─────────────────────────────────────────────────────────
    async def describe_pod(self, pod_name: str, namespace: str) -> dict:
        if not _REAL_K8S:
            return {"name": pod_name, "namespace": namespace, "note": "mock mode"}

        p = await _run_sync(self._core.read_namespaced_pod, pod_name, namespace)
        events = await self.get_events(namespace=namespace, field_selector=f"involvedObject.name={pod_name}")
        containers = []
        for c in p.spec.containers:
            containers.append({
                "name": c.name,
                "image": c.image,
                "resources": {
                    "requests": (c.resources.requests or {}) if c.resources else {},
                    "limits": (c.resources.limits or {}) if c.resources else {},
                },
                "ports": [{"name": cp.name, "containerPort": cp.container_port, "protocol": cp.protocol} for cp in (c.ports or [])],
                "env_vars": [e.name for e in (c.env or [])],
            })
        labels = p.metadata.labels or {}
        return {
            "name": p.metadata.name,
            "namespace": p.metadata.namespace,
            "node": p.spec.node_name,
            "phase": p.status.phase,
            "ready": _pod_ready(p),
            "nf_type": _detect_nf_type(p.metadata.name, labels),
            "labels": labels,
            "annotations": p.metadata.annotations or {},
            "containers": containers,
            "conditions": [{"type": c.type, "status": c.status, "reason": c.reason} for c in (p.status.conditions or [])],
            "recent_events": events[:10],
        }

    # ── ConfigMaps ───────────────────────────────────────────────────────────
    async def get_configmaps(self, namespace: str | None = None, name: str | None = None) -> list[dict]:
        if not _REAL_K8S:
            return _mock_configmaps()

        if name and namespace:
            cm = await _run_sync(self._core.read_namespaced_config_map, name, namespace)
            return [{"name": cm.metadata.name, "namespace": cm.metadata.namespace, "data": cm.data or {}}]

        if namespace:
            resp = await _run_sync(self._core.list_namespaced_config_map, namespace)
        else:
            resp = await _run_sync(self._core.list_config_map_for_all_namespaces)

        return [
            {"name": c.metadata.name, "namespace": c.metadata.namespace, "data": c.data or {}}
            for c in resp.items
        ]

    # ── Nodes ────────────────────────────────────────────────────────────────
    async def get_nodes(self) -> list[dict]:
        if not _REAL_K8S:
            return _mock_nodes()

        resp = await _run_sync(self._core.list_node)
        result = []
        for n in resp.items:
            labels = n.metadata.labels or {}
            roles = [k.split("/")[-1] for k in labels if "node-role.kubernetes.io" in k]
            result.append({
                "name": n.metadata.name,
                "roles": roles or ["worker"],
                "status": _node_ready(n),
                "os": n.status.node_info.os_image,
                "kernel": n.status.node_info.kernel_version,
                "container_runtime": n.status.node_info.container_runtime_version,
                "capacity": {
                    "cpu": n.status.capacity.get("cpu"),
                    "memory": n.status.capacity.get("memory"),
                    "hugepages_1gi": n.status.capacity.get("hugepages-1Gi"),
                    "hugepages_2mi": n.status.capacity.get("hugepages-2Mi"),
                },
                "allocatable": {
                    "cpu": n.status.allocatable.get("cpu"),
                    "memory": n.status.allocatable.get("memory"),
                },
                "dpdk_enabled": "intel.com/intel_sriov_netdevice" in n.status.allocatable or "dpdk" in str(labels).lower(),
                "sriov_resources": {k: v for k, v in n.status.allocatable.items() if "sriov" in k.lower() or "intel.com" in k.lower()},
                "labels": labels,
                "age": _age(n.metadata.creation_timestamp),
            })
        return result

    # ── Events ───────────────────────────────────────────────────────────────
    async def get_events(self, namespace: str | None = None, field_selector: str | None = None, limit: int = 50) -> list[dict]:
        if not _REAL_K8S:
            return _mock_events()

        kwargs: dict = {}
        if field_selector:
            kwargs["field_selector"] = field_selector

        if namespace:
            resp = await _run_sync(self._core.list_namespaced_event, namespace, **kwargs)
        else:
            resp = await _run_sync(self._core.list_event_for_all_namespaces, **kwargs)

        events = sorted(resp.items, key=lambda e: e.last_timestamp or e.event_time or datetime.min, reverse=True)
        return [
            {
                "type": e.type,
                "reason": e.reason,
                "message": e.message,
                "object": f"{e.involved_object.kind}/{e.involved_object.name}",
                "namespace": e.metadata.namespace,
                "count": e.count,
                "first_time": str(e.first_timestamp),
                "last_time": str(e.last_timestamp),
            }
            for e in events[:limit]
        ]


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------
def _pod_ready(p) -> bool:
    for cond in (p.status.conditions or []):
        if cond.type == "Ready":
            return cond.status == "True"
    return False


def _node_ready(n) -> str:
    for cond in (n.status.conditions or []):
        if cond.type == "Ready":
            return "Ready" if cond.status == "True" else "NotReady"
    return "Unknown"


def _detect_sbi(svc) -> str | None:
    """Return an SBI URL hint if this service looks like a 5G SBI endpoint."""
    for port in (svc.spec.ports or []):
        if port.name and "sbi" in port.name.lower():
            return f"http://{svc.spec.cluster_ip}:{port.port}"
        if port.port in (80, 8080, 8000, 7777, 29502, 29503, 29504, 29505, 29507, 29508, 29509, 29510, 29518):
            return f"http://{svc.spec.cluster_ip}:{port.port}"
    return None


# ---------------------------------------------------------------------------
# Mock data  (used when no live cluster is available)
# ---------------------------------------------------------------------------
def _mock_pods():
    return [
        {"name": "open5gs-amf-7d4b9c8f6-x2k9p", "namespace": "open5gs", "phase": "Running", "ready": True, "node": "worker-1", "restarts": 0, "age": "3d", "labels": {"app": "open5gs-amf"}, "nf_type": "AMF", "ip": "10.244.1.10"},
        {"name": "open5gs-smf-6f8d7b5c9-mn3qr", "namespace": "open5gs", "phase": "Running", "ready": True, "node": "worker-1", "restarts": 1, "age": "3d", "labels": {"app": "open5gs-smf"}, "nf_type": "SMF", "ip": "10.244.1.11"},
        {"name": "open5gs-upf-5c7f9d8b4-pq7rs", "namespace": "open5gs", "phase": "Running", "ready": True, "node": "worker-2", "restarts": 0, "age": "3d", "labels": {"app": "open5gs-upf"}, "nf_type": "UPF", "ip": "10.244.2.10"},
        {"name": "open5gs-nrf-8b4d6e7f2-lk5mn", "namespace": "open5gs", "phase": "Running", "ready": True, "node": "worker-1", "restarts": 0, "age": "3d", "labels": {"app": "open5gs-nrf"}, "nf_type": "NRF", "ip": "10.244.1.12"},
        {"name": "open5gs-ausf-3f9c8d7b1-ab4cd", "namespace": "open5gs", "phase": "Running", "ready": True, "node": "worker-1", "restarts": 0, "age": "3d", "labels": {"app": "open5gs-ausf"}, "nf_type": "AUSF", "ip": "10.244.1.13"},
        {"name": "open5gs-udm-2e8b7a6c5-ef6gh", "namespace": "open5gs", "phase": "Running", "ready": True, "node": "worker-1", "restarts": 0, "age": "3d", "labels": {"app": "open5gs-udm"}, "nf_type": "UDM", "ip": "10.244.1.14"},
        {"name": "open5gs-udr-1d7a6f5b4-ij7kl", "namespace": "open5gs", "phase": "Running", "ready": True, "node": "worker-1", "restarts": 2, "age": "3d", "labels": {"app": "open5gs-udr"}, "nf_type": "UDR", "ip": "10.244.1.15"},
        {"name": "open5gs-pcf-9c3e5f8a7-mn8op", "namespace": "open5gs", "phase": "Running", "ready": True, "node": "worker-1", "restarts": 0, "age": "3d", "labels": {"app": "open5gs-pcf"}, "nf_type": "PCF", "ip": "10.244.1.16"},
    ]


def _mock_deployments():
    return [
        {"name": "open5gs-amf", "namespace": "open5gs", "replicas": 1, "ready_replicas": 1, "available_replicas": 1, "age": "3d", "labels": {"app": "open5gs-amf"}, "nf_type": "AMF"},
        {"name": "open5gs-smf", "namespace": "open5gs", "replicas": 1, "ready_replicas": 1, "available_replicas": 1, "age": "3d", "labels": {"app": "open5gs-smf"}, "nf_type": "SMF"},
        {"name": "open5gs-upf", "namespace": "open5gs", "replicas": 1, "ready_replicas": 1, "available_replicas": 1, "age": "3d", "labels": {"app": "open5gs-upf"}, "nf_type": "UPF"},
        {"name": "open5gs-nrf", "namespace": "open5gs", "replicas": 1, "ready_replicas": 1, "available_replicas": 1, "age": "3d", "labels": {"app": "open5gs-nrf"}, "nf_type": "NRF"},
    ]


def _mock_services():
    return [
        {"name": "open5gs-amf-svc", "namespace": "open5gs", "type": "ClusterIP", "cluster_ip": "10.96.10.1", "external_ip": None, "ports": [{"name": "sbi", "port": 80, "target_port": "80", "protocol": "TCP"}, {"name": "ngap", "port": 38412, "target_port": "38412", "protocol": "SCTP"}], "labels": {"app": "open5gs-amf"}, "nf_type": "AMF", "sbi_endpoint": "http://10.96.10.1:80"},
        {"name": "open5gs-smf-svc", "namespace": "open5gs", "type": "ClusterIP", "cluster_ip": "10.96.10.2", "external_ip": None, "ports": [{"name": "sbi", "port": 80, "target_port": "80", "protocol": "TCP"}, {"name": "pfcp", "port": 8805, "target_port": "8805", "protocol": "UDP"}], "labels": {"app": "open5gs-smf"}, "nf_type": "SMF", "sbi_endpoint": "http://10.96.10.2:80"},
        {"name": "open5gs-upf-svc", "namespace": "open5gs", "type": "ClusterIP", "cluster_ip": "10.96.10.3", "external_ip": None, "ports": [{"name": "pfcp", "port": 8805, "target_port": "8805", "protocol": "UDP"}, {"name": "gtpu", "port": 2152, "target_port": "2152", "protocol": "UDP"}], "labels": {"app": "open5gs-upf"}, "nf_type": "UPF", "sbi_endpoint": None},
        {"name": "open5gs-nrf-svc", "namespace": "open5gs", "type": "ClusterIP", "cluster_ip": "10.96.10.4", "external_ip": None, "ports": [{"name": "sbi", "port": 80, "target_port": "80", "protocol": "TCP"}], "labels": {"app": "open5gs-nrf"}, "nf_type": "NRF", "sbi_endpoint": "http://10.96.10.4:80"},
    ]


def _mock_logs(pod_name: str) -> str:
    nf = pod_name.split("-")[1].upper() if "-" in pod_name else "NF"
    return f"""[2024-01-15 10:00:01.234] INFO  {nf}: Starting {nf} service
[2024-01-15 10:00:01.456] INFO  {nf}: NRF registration successful - NF registered with NRF
[2024-01-15 10:00:02.123] INFO  {nf}: SBI interface listening on 0.0.0.0:80
[2024-01-15 10:05:33.891] INFO  {nf}: New connection established
[2024-01-15 10:05:34.012] WARN  {nf}: N2 interface setup timeout - retrying (attempt 1/3)
[2024-01-15 10:05:36.234] INFO  {nf}: N2 interface setup completed
[2024-01-15 10:10:01.567] INFO  {nf}: Heartbeat to NRF successful
"""


def _mock_configmaps():
    return [
        {
            "name": "open5gs-amf-config",
            "namespace": "open5gs",
            "data": {
                "amf.yaml": """
amf:
  sbi:
    server:
      - address: 0.0.0.0
        port: 80
  ngap:
    server:
      - address: 0.0.0.0
  guami:
    - plmn_id:
        mcc: 999
        mnc: 70
      amf_id:
        region: 2
        set: 1
  tai:
    - plmn_id:
        mcc: 999
        mnc: 70
      tac: 1
  plmn_support:
    - plmn_id:
        mcc: 999
        mnc: 70
      s_nssai:
        - sst: 1
        - sst: 2
          sd: 000001
  security:
    integrity_order: [NIA2, NIA1, NIA0]
    ciphering_order: [NEA0, NEA2, NEA1]
  network_name:
    full: Open5GS
  amf_name: open5gs-amf0
"""
            },
        },
        {
            "name": "open5gs-smf-config",
            "namespace": "open5gs",
            "data": {
                "smf.yaml": """
smf:
  sbi:
    server:
      - address: 0.0.0.0
        port: 80
  pfcp:
    server:
      - address: 0.0.0.0
    client:
      upf:
        - address: open5gs-upf
  session:
    - subnet: 10.45.0.0/16
      gateway: 10.45.0.1
      dnn: internet
    - subnet: 10.46.0.0/16
      gateway: 10.46.0.1
      dnn: ims
  dns:
    - 8.8.8.8
    - 8.8.4.4
  mtu: 1400
"""
            },
        },
    ]


def _mock_nodes():
    return [
        {
            "name": "control-plane-1",
            "roles": ["control-plane"],
            "status": "Ready",
            "os": "Ubuntu 22.04.3 LTS",
            "kernel": "5.15.0-91-generic",
            "container_runtime": "containerd://1.7.2",
            "capacity": {"cpu": "8", "memory": "16Gi", "hugepages_1gi": None, "hugepages_2mi": None},
            "allocatable": {"cpu": "7800m", "memory": "15Gi"},
            "dpdk_enabled": False,
            "sriov_resources": {},
            "labels": {"node-role.kubernetes.io/control-plane": ""},
            "age": "5d",
        },
        {
            "name": "worker-1",
            "roles": ["worker"],
            "status": "Ready",
            "os": "Ubuntu 22.04.3 LTS",
            "kernel": "5.15.0-91-generic",
            "container_runtime": "containerd://1.7.2",
            "capacity": {"cpu": "16", "memory": "32Gi", "hugepages_1gi": "4Gi", "hugepages_2mi": None},
            "allocatable": {"cpu": "15800m", "memory": "30Gi"},
            "dpdk_enabled": False,
            "sriov_resources": {},
            "labels": {},
            "age": "5d",
        },
        {
            "name": "worker-2",
            "roles": ["worker"],
            "status": "Ready",
            "os": "Ubuntu 22.04.3 LTS",
            "kernel": "5.15.0-91-generic",
            "container_runtime": "containerd://1.7.2",
            "capacity": {"cpu": "32", "memory": "64Gi", "hugepages_1gi": "16Gi", "hugepages_2mi": "8Gi"},
            "allocatable": {"cpu": "31800m", "memory": "60Gi"},
            "dpdk_enabled": True,
            "sriov_resources": {"intel.com/intel_sriov_netdevice": "8"},
            "labels": {"dpdk": "enabled", "upf": "true"},
            "age": "5d",
        },
    ]


def _mock_events():
    return [
        {"type": "Normal", "reason": "Scheduled", "message": "Successfully assigned open5gs/open5gs-amf-7d4b9c8f6-x2k9p to worker-1", "object": "Pod/open5gs-amf-7d4b9c8f6-x2k9p", "namespace": "open5gs", "count": 1, "first_time": "2024-01-12T07:00:00Z", "last_time": "2024-01-12T07:00:00Z"},
        {"type": "Warning", "reason": "BackOff", "message": "Back-off restarting failed container smf in pod open5gs-smf-6f8d7b5c9-mn3qr", "object": "Pod/open5gs-smf-6f8d7b5c9-mn3qr", "namespace": "open5gs", "count": 3, "first_time": "2024-01-12T07:05:00Z", "last_time": "2024-01-12T07:10:00Z"},
    ]