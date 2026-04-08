from typing import Optional, List  
from .memory import LongTermMemory, ShortTermMemory, CodeLocation
from utils.output_model import VulnResponse

def format_code_location(loc: Optional[CodeLocation] | str) -> str:
    """Helper to format code location cleanly."""
    if not loc:
        return "Unknown Location"
    # return f"{loc.file_path}:{loc.line_start}-{loc.line_end}"
    return f"{loc}"


def longterm_memory_to_markdown(ltm: LongTermMemory) -> str:
    """Convert LongTermMemory to a clean, professional markdown report."""
    lines = ["# Long Term Memory of this MCP Server Project"]
    lines.append(f"## Project Analysis: {ltm.project_description}")
    lines.append(f"**Directory:** `{ltm.project_directory}`")
    lines.append(f"**Language:** {ltm.programming_language}")
    lines.append("")
    lines.append("## Repository Structure")
    lines.append(ltm.repository_structure)

    lines.append("## MCP Server INFO")
    lines.append(f"- **Transport:** {ltm.transport_type or 'Unknown'}")
    lines.append("### Detected Tools")

    for tool in ltm.mcp_tools:
        lines.append(f"- Tool: {tool.name}")
        lines.append(f"**Description:** {tool.description or 'N/A'}")
        lines.append(f"**Defined at:** {format_code_location(tool.code_location)}")
        lines.append("")
    
    return "\n".join(lines)


def shortterm_memory_to_markdown(stm: ShortTermMemory) -> str:
    """Convert ShortTermMemory to a detailed vulnerability report."""
    stm_str = "### Tool Intent Analysis\n"
    stm_str += stm.intent_analysis + "\n"
    stm_str += "### Tool Capability Analysis\n"
    stm_str += stm.capability_analysis + "\n"
    stm_str += "### Intent-Capability Gap Analysis\n"
    stm_str += stm.intent_capability_gap_analysis + "\n"

    stm_str += "### Tool code content\n"
    stm_str += stm.content + "\n\n"

    return stm_str


def vuln_info_to_markdown(vuln_info: dict) -> str:
    """Convert vulnerability info list to markdown format."""
    lines = ["## Vulnerability Information"]
    vuln_response = VulnResponse.model_validate(vuln_info)
    for vuln_report in vuln_response.vulnerabilities:
        lines.append(f"### Vulnerability: {vuln_report.id}")
        lines.append(f"- **Type:** {vuln_report.type}")
        lines.append(f"- **Severity:** {vuln_report.severity}")
        lines.append(f"- **Location:** {format_code_location(vuln_report.location)}\n")
        lines.append(f"**Description:** \n{vuln_report.description}")
        lines.append("")
    return "\n".join(lines)