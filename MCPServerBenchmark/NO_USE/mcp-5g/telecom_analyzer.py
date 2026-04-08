"""
TelecomAnalyzer – 5G Core domain logic for the Kubernetes MCP server.
Provides topology building, log annotation, NF status, UPF data-plane
inspection, slice extraction, and health checks.
"""

from __future__ import annotations

import re
from typing import Any

# ---------------------------------------------------------------------------
# 3GPP NF Reference (3GPP TS 23.501 / TS 29.510)
# ---------------------------------------------------------------------------
NF_REFERENCE: dict[str, dict] = {
    
    "NRF": {
        "full_name": "Network Repository Function",
        "spec": "3GPP TS 29.510",
        "sbi_api": "Nnrf",
        "interfaces": ["SBI (all NFs)"],
        "ports": {"sbi": 80},
        "protocol": {"sbi": "HTTP/2"},
        "description": "NF registration, discovery and status management for the 5G SBA.",
    },
    
    "UDM": {
        "full_name": "Unified Data Management",
        "spec": "3GPP TS 29.503",
        "sbi_api": "Nudm",
        "interfaces": ["N8 (AMF)", "N10 (SMF)", "N13 (AUSF)", "N35 (UDR)"],
        "ports": {"sbi": 80},
        "protocol": {"sbi": "HTTP/2"},
        "description": "Manages subscription data, generates authentication credentials.",
    },
    "UDR": {
        "full_name": "Unified Data Repository",
        "spec": "3GPP TS 29.504",
        "sbi_api": "Nudr",
        "interfaces": ["N35 (UDM)", "N36 (PCF)", "N37 (NEF)"],
        "ports": {"sbi": 80},
        "protocol": {"sbi": "HTTP/2"},
        "description": "Stores structured subscriber and policy data.",
    },
    "PCF": {
        "full_name": "Policy Control Function",
        "spec": "3GPP TS 29.507",
        "sbi_api": "Npcf",
        "interfaces": ["N7 (SMF)", "N15 (AMF)", "N36 (UDR)", "N5 (AF)"],
        "ports": {"sbi": 80},
        "protocol": {"sbi": "HTTP/2"},
        "description": "Provides policy rules for QoS, charging, and access control.",
    },
    "NSSF": {
        "full_name": "Network Slice Selection Function",
        "spec": "3GPP TS 29.531",
        "sbi_api": "Nnssf",
        "interfaces": ["N22 (AMF)", "N31 (NSSF')"],
        "ports": {"sbi": 80},
        "protocol": {"sbi": "HTTP/2"},
        "description": "Selects the appropriate network slice for a UE.",
    },
    "BSF": {
        "full_name": "Binding Support Function",
        "spec": "3GPP TS 29.521",
        "sbi_api": "Nbsf",
        "interfaces": ["Rx (AF)", "N30 (PCF)"],
        "ports": {"sbi": 80},
        "protocol": {"sbi": "HTTP/2"},
        "description": "Binds a PDU session to a PCF instance.",
    },
    "CHF": {
        "full_name": "Charging Function",
        "spec": "3GPP TS 32.291",
        "sbi_api": "Nchf",
        "interfaces": ["N40 (SMF)", "N74 (NWDAF)"],
        "ports": {"sbi": 80},
        "protocol": {"sbi": "HTTP/2"},
        "description": "Online/offline charging for 5G sessions.",
    },
}

INTERFACE_MAP: dict[str, str] = {
    "N1":  "UE ↔ AMF – NAS signalling (5G-S-TMSI, registration, session mgmt)",
    "N2":  "gNB (RAN) ↔ AMF – NGAP (NG Application Protocol over SCTP)",
    "N3":  "gNB ↔ UPF – GTP-U user-plane tunnels (uplink/downlink data)",
    "N4":  "SMF ↔ UPF – PFCP (Packet Forwarding Control Protocol over UDP)",
    "N6":  "UPF ↔ Data Network (Internet / IMS / MEC)",
    "N7":  "SMF ↔ PCF – Policy and charging rules for PDU sessions",
    "N8":  "AMF ↔ UDM – Access and mobility subscription data",
    "N9":  "UPF ↔ UPF – GTP-U inter-UPF tunnels (I-UPF ↔ PSA-UPF)",
    "N10": "SMF ↔ UDM – Session management subscription data",
    "N11": "AMF ↔ SMF – PDU session creation/modification/release",
    "N12": "AMF ↔ AUSF – Authentication requests",
    "N13": "AUSF ↔ UDM – Authentication credential generation",
    "N14": "AMF ↔ AMF – Handover / context transfer",
    "N15": "AMF ↔ PCF – Access and mobility policies (UE policy)",
    "N16": "SMF ↔ SMF – Session handover between SMFs",
    "N20": "AMF ↔ NSSF – Slice selection queries",
    "N22": "AMF ↔ NSSF – Network slice info (post-registration)",
    "N26": "AMF ↔ MME (EPC) – Interworking with 4G EPC",
    "N35": "UDM ↔ UDR – Subscriber data read/write",
    "N36": "PCF ↔ UDR – Policy data read/write",
    "N40": "SMF ↔ CHF – Charging data requests",
    "SBI": "Service-Based Interface – HTTP/2 + JSON between all 5G core NFs",
    "Xn":  "gNB ↔ gNB – X2-like interface for handover and coordination",
}

# ---------------------------------------------------------------------------
# Log pattern annotations
# ---------------------------------------------------------------------------
_LOG_PATTERNS = [
    (re.compile(r"ngap.*error|ngap.*fail", re.I),         "⚠️  NGAP (N2) error – check gNB connectivity or AMF SCTP"),
    (re.compile(r"pfcp.*error|pfcp.*fail|pfcp.*timeout", re.I), "⚠️  PFCP (N4) error – SMF↔UPF session setup failure"),
    (re.compile(r"n4.*fail|n4.*error", re.I),             "⚠️  N4 interface failure – PFCP/UPF unreachable"),
    (re.compile(r"nrf.*fail|nrf.*unreachable|nrf.*timeout", re.I), "⚠️  NRF registration/discovery failure"),
    (re.compile(r"sbi.*fail|sbi.*error|http.*500|http.*503", re.I), "⚠️  SBI HTTP error – check inter-NF connectivity"),
    (re.compile(r"nas.*decode.*fail|nas.*error", re.I),   "⚠️  NAS decode failure – possible UE compatibility issue"),
    (re.compile(r"authentication.*fail|aka.*fail", re.I), "⚠️  Authentication failure – check AUSF/UDM/subscriber"),
    (re.compile(r"slice.*not.*found|nssai.*reject", re.I), "⚠️  Slice selection failure – check NSSF / S-NSSAI config"),
    (re.compile(r"OOM|out of memory|killed", re.I),        "🔴 OOM / container killed – increase memory limits"),
    (re.compile(r"gtp.*error|gtpu.*fail", re.I),           "⚠️  GTP-U (N3/N9) error – user-plane tunnel issue"),
    (re.compile(r"ims|ims.*fail|ims.*error", re.I),        "ℹ️  IMS-related log entry"),
    (re.compile(r"connected|registered|success", re.I),    "✅ Successful operation"),
    (re.compile(r"heartbeat.*fail|nf.*deregistered", re.I), "⚠️  NF heartbeat/deregistration – check NRF health"),
]


def _annotate_line(line: str) -> str | None:
    for pattern, annotation in _LOG_PATTERNS:
        if pattern.search(line):
            return annotation
    return None


# ---------------------------------------------------------------------------
# TelecomAnalyzer
# ---------------------------------------------------------------------------
class TelecomAnalyzer:

    # ── Log annotation ───────────────────────────────────────────────────────
    def annotate_logs(self, raw_logs: str) -> list[dict]:
        annotations = []
        for i, line in enumerate(raw_logs.splitlines(), 1):
            note = _annotate_line(line)
            if note:
                annotations.append({"line": i, "text": line.strip(), "annotation": note})
        return annotations

    # ── ConfigMap parsing ────────────────────────────────────────────────────
    def parse_5g_configmaps(self, cms: list[dict]) -> list[dict]:
        result = []
        for cm in cms:
            parsed = {"name": cm["name"], "namespace": cm["namespace"], "5g_config": {}}
            for key, val in cm.get("data", {}).items():
                extracted = self._extract_5g_fields(val)
                if extracted:
                    parsed["5g_config"][key] = extracted
            result.append(parsed)
        return result

    def _extract_5g_fields(self, text: str) -> dict:
        fields: dict = {}
        # PLMN
        mcc = re.findall(r"mcc:\s*['\"]?(\d+)['\"]?", text)
        mnc = re.findall(r"mnc:\s*['\"]?(\d+)['\"]?", text)
        if mcc and mnc:
            fields["plmn"] = [f"{m}/{n}" for m, n in zip(mcc, mnc)]
        # S-NSSAI slices
        sst = re.findall(r"sst:\s*(\d+)", text)
        sd = re.findall(r"sd:\s*([0-9a-fA-F]+)", text)
        if sst:
            fields["s_nssai"] = [{"sst": s, "sd": sd[i] if i < len(sd) else None} for i, s in enumerate(sst)]
        # NRF URI
        nrf = re.findall(r"nrf[_\-]?uri\s*[:=]\s*['\"]?(http[s]?://[^\s'\"]+)['\"]?", text, re.I)
        if nrf:
            fields["nrf_uri"] = nrf
        # DNN
        dnn = re.findall(r"dnn:\s*['\"]?(\w+)['\"]?", text)
        if dnn:
            fields["dnn"] = list(set(dnn))
        # Subnets
        subnets = re.findall(r"subnet:\s*(\d+\.\d+\.\d+\.\d+/\d+)", text)
        if subnets:
            fields["subnets"] = subnets
        # TAC
        tac = re.findall(r"tac:\s*(\d+)", text)
        if tac:
            fields["tac"] = tac
        return fields

    # ── Full 5G topology ─────────────────────────────────────────────────────
    async def build_topology(self, k8s, namespace: str | None = None) -> dict:
        pods = await k8s.get_pods(namespace=namespace)
        services = await k8s.get_services(namespace=namespace)
        cms = await k8s.get_configmaps(namespace=namespace)
        parsed_cms = self.parse_5g_configmaps(cms)

        nf_map: dict[str, list] = {}
        for pod in pods:
            nf = pod["nf_type"]
            nf_map.setdefault(nf, []).append(pod)

        svc_map: dict[str, list] = {}
        for svc in services:
            nf = svc["nf_type"]
            svc_map.setdefault(nf, []).append(svc)

        topology: dict[str, Any] = {
            "summary": {
                "total_pods": len(pods),
                "healthy_pods": sum(1 for p in pods if p.get("ready")),
                "nf_types_detected": list(nf_map.keys()),
                "missing_core_nfs": [nf for nf in ["AMF", "SMF", "UPF", "NRF"] if nf not in nf_map],
            },
            "network_functions": {},
            "plmn_config": [],
            "slices": [],
            "sbi_endpoints": {},
        }

        for nf_type, nf_pods in nf_map.items():
            ref = NF_REFERENCE.get(nf_type, {})
            svcs = svc_map.get(nf_type, [])
            topology["network_functions"][nf_type] = {
                "description": ref.get("description", ""),
                "spec": ref.get("spec", ""),
                "sbi_api": ref.get("sbi_api"),
                "interfaces": ref.get("interfaces", []),
                "pods": nf_pods,
                "services": svcs,
                "healthy": all(p.get("ready") for p in nf_pods),
            }
            for svc in svcs:
                if svc.get("sbi_endpoint"):
                    topology["sbi_endpoints"][nf_type] = svc["sbi_endpoint"]

        # Extract PLMN & slices from ConfigMaps
        for cm in parsed_cms:
            for _key, cfg in cm.get("5g_config", {}).items():
                if cfg.get("plmn"):
                    topology["plmn_config"].extend(cfg["plmn"])
                if cfg.get("s_nssai"):
                    topology["slices"].extend(cfg["s_nssai"])

        topology["plmn_config"] = list(set(topology["plmn_config"]))
        topology["reference"] = {nf: NF_REFERENCE[nf] for nf in nf_map if nf in NF_REFERENCE}
        topology["interface_map"] = INTERFACE_MAP
        return topology

    # ── NF status ────────────────────────────────────────────────────────────
    async def nf_status(self, k8s, nf_type: str, namespace: str | None = None) -> dict:
        nf_upper = nf_type.upper()
        pods = [p for p in await k8s.get_pods(namespace=namespace) if p.get("nf_type") == nf_upper]
        services = [s for s in await k8s.get_services(namespace=namespace) if s.get("nf_type") == nf_upper]

        log_annotations: list = []
        for pod in pods[:2]:  # limit log fetches
            raw = await k8s.get_pod_logs(pod["name"], pod["namespace"], tail_lines=50)
            log_annotations += self.annotate_logs(raw)

        ref = NF_REFERENCE.get(nf_upper, {})
        return {
            "nf_type": nf_upper,
            "full_name": ref.get("full_name", nf_upper),
            "spec": ref.get("spec", ""),
            "description": ref.get("description", ""),
            "interfaces": ref.get("interfaces", []),
            "pods": pods,
            "pod_count": len(pods),
            "healthy": all(p.get("ready") for p in pods) and len(pods) > 0,
            "total_restarts": sum(p.get("restarts", 0) for p in pods),
            "services": services,
            "sbi_endpoint": next((s["sbi_endpoint"] for s in services if s.get("sbi_endpoint")), None),
            "log_issues": [a for a in log_annotations if "⚠️" in a["annotation"] or "🔴" in a["annotation"]],
        }

    
    # ── Slice info ───────────────────────────────────────────────────────────
    async def slice_info(self, k8s, namespace: str | None = None) -> dict:
        cms = await k8s.get_configmaps(namespace=namespace)
        parsed = self.parse_5g_configmaps(cms)

        slices: list = []
        plmns: list = []
        dnns: list = []

        for cm in parsed:
            for _key, cfg in cm.get("5g_config", {}).items():
                if cfg.get("s_nssai"):
                    for s in cfg["s_nssai"]:
                        entry = {"sst": s["sst"], "sd": s.get("sd"), "source_cm": cm["name"]}
                        if entry not in slices:
                            slices.append(entry)
                if cfg.get("plmn"):
                    plmns.extend(cfg["plmn"])
                if cfg.get("dnn"):
                    dnns.extend(cfg["dnn"])

        sst_meanings = {1: "eMBB (enhanced Mobile Broadband)", 2: "URLLC (Ultra-Reliable Low-Latency)", 3: "MIoT (Massive IoT)", 4: "V2X"}
        for s in slices:
            s["service_type"] = sst_meanings.get(int(s["sst"]), f"SST {s['sst']}")

        return {
            "slices": slices,
            "plmns": list(set(plmns)),
            "dnns": list(set(dnns)),
            "slice_count": len(slices),
            "reference": {
                "SST=1": "eMBB – best-effort broadband",
                "SST=2": "URLLC – deterministic low-latency",
                "SST=3": "MIoT – massive IoT low-power",
                "SST=4": "V2X – vehicle-to-everything",
            },
        }

    # ── Health check ─────────────────────────────────────────────────────────
    async def health_check(self, k8s, namespace: str | None = None) -> dict:
        pods = await k8s.get_pods(namespace=namespace)
        events = await k8s.get_events(namespace=namespace, limit=100)
        nodes = await k8s.get_nodes()

        issues: list[str] = []
        warnings: list[str] = []
        healthy_count = sum(1 for p in pods if p.get("ready"))
        unhealthy = [p for p in pods if not p.get("ready")]

        if unhealthy:
            issues.append(f"🔴 {len(unhealthy)} pod(s) not ready: {[p['name'] for p in unhealthy]}")

        # Missing core NFs
        detected_nfs = {p["nf_type"] for p in pods}
        for nf in ["AMF", "SMF", "UPF", "NRF"]:
            if nf not in detected_nfs:
                issues.append(f"🔴 Core NF missing: {nf} – {NF_REFERENCE.get(nf, {}).get('full_name', nf)}")

        # Restart storms
        high_restart = [p for p in pods if p.get("restarts", 0) >= 5]
        for p in high_restart:
            warnings.append(f"⚠️  {p['name']} has {p['restarts']} restarts – possible crash loop")

        # Warning events
        warn_events = [e for e in events if e.get("type") == "Warning"]
        for e in warn_events[:5]:
            warnings.append(f"⚠️  Event [{e['reason']}] {e['object']}: {e['message']}")

        # Log scan for all pods
        telecom_issues: list = []
        for pod in pods[:6]:
            raw = await k8s.get_pod_logs(pod["name"], pod["namespace"], tail_lines=30)
            anns = self.annotate_logs(raw)
            for a in anns:
                if "⚠️" in a["annotation"] or "🔴" in a["annotation"]:
                    telecom_issues.append({"pod": pod["name"], **a})

        # Node pressure
        not_ready_nodes = [n for n in nodes if n["status"] != "Ready"]
        if not_ready_nodes:
            issues.append(f"🔴 Node(s) not ready: {[n['name'] for n in not_ready_nodes]}")

        # UPF DPDK
        upf_pods = [p for p in pods if p.get("nf_type") == "UPF"]
        upf_node_names = {p.get("node") for p in upf_pods}
        dpdk_on_upf = any(n.get("dpdk_enabled") and n["name"] in upf_node_names for n in nodes)

        overall = "HEALTHY" if not issues else ("DEGRADED" if len(issues) <= 2 else "CRITICAL")

        return {
            "overall_status": overall,
            "pod_summary": {"total": len(pods), "healthy": healthy_count, "unhealthy": len(unhealthy)},
            "detected_nfs": list(detected_nfs),
            "missing_core_nfs": [nf for nf in ["AMF", "SMF", "UPF", "NRF"] if nf not in detected_nfs],
            "issues": issues,
            "warnings": warnings,
            "telecom_log_issues": telecom_issues[:20],
            "node_status": [{"name": n["name"], "status": n["status"], "roles": n["roles"]} for n in nodes],
            "upf_dpdk_enabled": dpdk_on_upf,
            "recommendations": _build_recommendations(issues, warnings, telecom_issues, dpdk_on_upf),
        }


def _build_recommendations(issues, warnings, telecom_issues, dpdk_on_upf) -> list[str]:
    recs = []
    if any("NRF" in i for i in issues):
        recs.append("Deploy NRF first – all NFs depend on it for registration and discovery.")
    if any("PFCP" in t["annotation"] for t in telecom_issues):
        recs.append("PFCP errors detected – verify SMF ↔ UPF N4 connectivity and IP addressing.")
    if any("NGAP" in t["annotation"] for t in telecom_issues):
        recs.append("NGAP errors detected – check gNB N2 SCTP connectivity to AMF.")
    if any("NRF" in t["annotation"] for t in telecom_issues):
        recs.append("NRF connectivity issues – ensure NRF_URI is correctly set in all NF ConfigMaps.")
    if any("restart" in w.lower() for w in warnings):
        recs.append("Restart storms detected – check resource limits and inter-NF dependencies.")
    if not recs:
        recs.append("No critical recommendations. Continue monitoring NF heartbeats and SBI latency.")
    return recs
