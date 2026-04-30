from pydantic import BaseModel, Field
from typing import List

class CodeLocation(BaseModel):
    file_path: str = Field(description="File path")
    line_start: int = Field(description="Start line number")
    line_end: int = Field(description="End line number")


class VulnerabilityDetail(BaseModel):
    """Details of a single vulnerability"""
    severity: str = Field(description="Vulnerability severity (e.g., 'Critical', 'High', 'Medium', 'Low')")
    vuln_type: str = Field(description="Vulnerability type (e.g., 'Command Injection', 'Path Traversal')")
    description: str = Field(description="Vulnerability description and trigger conditions")
    location: CodeLocation = Field(description="Specific location of the vulnerability in the code")


class StaticVulnReport(BaseModel):
    """Security scan report for a single MCP Tool"""
    tool_name: str = Field(description="Tool name")
    tool_definition_location: CodeLocation = Field(description="Location of the tool definition")
    tool_function_summary: str = Field(description="Summary of the tool functionality")
    vulnerabilities: List[VulnerabilityDetail] = Field(default_factory=list, description="List of detected vulnerabilities")


class VulnReport(BaseModel):
    """Security scan report for a single MCP Tool"""
    tool_name: str = Field(description="Tool name")
    tool_definition_location: CodeLocation = Field(description="Location of the tool definition")
    tool_function_summary: str = Field(description="Summary of the tool functionality")
    vulnerabilities: List[VulnerabilityDetail] = Field(default_factory=list, description="List of detected vulnerabilities")