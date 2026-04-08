from enum import Enum
from typing import List
from pydantic import BaseModel, Field

class SeverityLevel(str, Enum):
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"

class ConfidenceLevel(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"

# 专门用于 llm_only 和 single_agent 的输出格式
class AllLocation(BaseModel):
    file: str = Field(description="The file path where the detected MCP tool is located")
    lines: str = Field(description="The specific line numbers in the file(e.g., '45-50')")

class AllReport(BaseModel):
    id: str = Field(description="Unique identifier for the MCP tool (e.g., Tool-001)")
    title: str = Field(description="A short summary or title of the tool")
    severity: SeverityLevel = Field(description="The severity level of the issue")
    confidence: ConfidenceLevel = Field(description="The confidence level regarding the accuracy of this finding")
    type: str = Field(default="None", description="For vulnerable MCP tools, the CWE identifier (e.g., CWE-35) needs to be specified; if the tool has no vulnerability, fill in None")
    tool_name: str = Field(description="The name of the tool in the MCP server. Only one tool name is allowed; multiple tool names or 'All tools' are prohibited.")
    location: AllLocation = Field(description="The location details of the tool within the source code")
    description: str = Field(default="None", description="For vulnerable MCP tools, a detailed technical description of the vulnerability; if the tool has no vulnerability, fill in None")

class AllResponse(BaseModel):
    """A list of vulnerability reports extracted from the analysis."""
    # 这里定义一个 list 字段
    vulnerabilities: List[AllReport] = Field(description="List of all MCP tools found in the input text")

class VerifiedAllReport(AllReport):
    poc: str = Field(description="Proof of Concept code or steps to reproduce the vulnerability")
    flag: str = Field(description="The flag or token obtained after successfully exploiting the vulnerability")

class VerifiedAllResponse(BaseModel):
    """A list of verified vulnerability reports extracted from the analysis."""
    verified_vulnerabilities: List[VerifiedAllReport] = Field(description="List of all verified vulnerabilities with PoC and flags")


# 用于 扫描漏洞
class Location(BaseModel):
    file: str = Field(description="The file path where the vulnerability resides")
    lines: str = Field(description="The specific line numbers affected (e.g., '45-50')")

class VulnReport(BaseModel):
    id: str = Field(description="Unique identifier for the vulnerability (e.g., VULN-001)")
    title: str = Field(description="A short summary or title of the vulnerability")
    severity: SeverityLevel = Field(description="The severity level of the issue")
    confidence: ConfidenceLevel = Field(description="The confidence level regarding the accuracy of this finding")
    type: str = Field(description="The CWE identifier (e.g., CWE-35) for the vulnerability. Only one vulnerability is allowed per entry. If a tool has multiple vulnerabilities, please create multiple VulnReport instances.")
    # tool_name: List[str] = Field(description="A list of names of the vulnerable tools in mcp server")
    tool_name: str = Field(description="The name of the vulnerable tool in mcp server.Only one tool name is allowed; multiple tool names or 'All tools' are prohibited.")
    location: Location = Field(description="The location details within the source code")
    description: str = Field(description="A detailed technical description of the vulnerability")

class VulnResponse(BaseModel):
    """A list of vulnerability reports extracted from the analysis."""
    # 这里定义一个 list 字段
    vulnerabilities: List[VulnReport] = Field(description="List of all vulnerabilities found in the input text")

class VerifiedVulnReport(VulnReport):
    poc: str = Field(description="Proof of Concept code or steps to reproduce the vulnerability")
    flag: str = Field(description="The flag or token obtained after successfully exploiting the vulnerability")

class VerifiedVulnResponse(BaseModel):
    """A list of verified vulnerability reports extracted from the analysis."""
    verified_vulnerabilities: List[VerifiedVulnReport] = Field(description="List of all verified vulnerabilities with PoC and flags")


# 用于 检测恶意工具
class MaliLocation(BaseModel):
    file: str = Field(description="The file path where the malicious tools resides")
    lines: str = Field(description="The specific line numbers affected (e.g., '45-50')")

class MaliReport(BaseModel):
    id: str = Field(description="Unique identifier for the malicious tools (e.g., MALI-001)")
    title: str = Field(description="A short summary or title of the malicious tools ")
    severity: SeverityLevel = Field(description="The severity level of the issue")
    confidence: ConfidenceLevel = Field(description="The confidence level regarding the accuracy of this finding")
    type: str = Field(default = "Malicious", description="The category or type of the malicious tools")
    tool_name: str = Field(description="The name of the malicious tool in mcp server")
    location: MaliLocation = Field(description="The location details within the source code")
    description: str = Field(description="A detailed technical description of the malicious tools")

class MaliResponse(BaseModel):
    """A list of malicious tools reports extracted from the analysis."""
    Maliciousness: List[MaliReport] = Field(description="List of all malicious tools found in the input text")

class VerifiedMaliReport(MaliReport):
    poc: str = Field(description="Proof of Concept code or steps to reproduce the malicious tools")
    flag: str = Field(description="The flag or token obtained after successfully exploiting the malicious tools")

class VerifiedMalResponse(BaseModel):
    """A list of verified malicious tools reports extracted from the analysis."""
    verified_Maliciousness: List[VerifiedMaliReport] = Field(description="List of all verified malicious tools with PoC and flags")