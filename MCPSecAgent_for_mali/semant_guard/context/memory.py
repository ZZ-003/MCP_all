from pydantic import BaseModel, Field
from typing import List, Dict, Optional

from .output import StaticVulnReport


class CodeLocation(BaseModel):
    """Code location information"""
    file_path: str = Field(description="File path (relative to project root)")
    line_start: int = Field(description="Starting line number")
    line_end: int = Field(description="Ending line number")


class MCPServerTool(BaseModel):
    """MCP Server Tool definition"""
    name: str = Field(description="Tool name")
    description: Optional[str] = Field(default=None, description="Tool description")
    # code_location: CodeLocation = Field(description="Tool code location")
    code_location: str = Field(description="Tool code location")
    
class FileInfo(BaseModel):
    """File information"""
    path: str = Field(description="File path (relative to project root)")
    # purpose: Optional[str] = Field(default=None, description="File purpose description")
    # file_type: str = Field(description="File type (.py, .ts, .js, etc.)")
    contains_mcp_tools: bool = Field(default=False, description="Whether it contains MCP tool definitions")
    imports: List[str] = Field(default_factory=list, description="List of imported modules")
    exports: List[str] = Field(default_factory=list, description="List of exported functions/classes")


class RepositoryStructure(BaseModel):
    """Code repository structure"""
    root_directory: str = Field(description="Absolute path of root directory")
    # directories: Dict[str, DirectoryInfo] = Field(default_factory=dict, description="Dictionary of directory information, key is relative path")
    files: Dict[str, FileInfo] = Field(default_factory=dict, description="Dictionary of file information, key is relative path")
    entry_point: Optional[str] = Field(default=None, description="Entry point file (relative path)")
    config_files: List[str] = Field(default_factory=list, description="List of configuration files")
    # total_files: int = Field(default=0, description="Total number of files")
    # total_lines: int = Field(default=0, description="Total lines of code")


class ServerConfiguration(BaseModel):
    """MCP Server configuration information"""
    configuration_location: Optional[CodeLocation] = Field(default=None, description="Code location where server is configured")
    # config_summary: Optional[str] = Field(default=None, description="Brief summary of the configuration values found")

class LongTermMemory(BaseModel):
    """Long-term memory storage structure - used to store global analysis results of MCP Server code repository"""
    project_description: str = Field(description="Summary of what the project does")
    project_directory: str = Field(description="Absolute path of project root")
    programming_language: Optional[str] = Field(default="Python", description="Primary programming language")
    
    repository_structure: str = Field(
            description="The overall software engineering design architecture, and the function of each folder and file."
        )    
    transport_type: Optional[str] = Field(default="streamable-http", description="stdio, sse, or streamable-http")
    mcp_tools: List[MCPServerTool] = Field(default_factory=list, description="MCP Server tool list")



# MALI
class ShortTermMemory(BaseModel):
    """Information related to a single MCP Server Tool, including static analysis results of intent and capability, and preliminary vulnerability analysis results after static analysis completion"""
    intent_analysis: str = Field(description="Detailed analysis of what the tool actually wants to do based on its name and description")
    capability_analysis: str = Field(description="Detailed analysis of what the tool implementation can actually achieve, including malicious description")
    intent_capability_gap_analysis: str = Field(description="Analysis of gaps between intent and capability")

    content: str = Field(description="The actual source code content of the 'Capability > Intent' or the malicious tool")


class AllToolSTM(BaseModel):
    """A list of ShortTermMemories reports extracted from the analysis."""
    ShortTermMemories: Dict[str, ShortTermMemory] = Field(description="Dictionary of all ShortTermMemories found in the input text")