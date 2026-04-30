PROMPT = """
You are a Result Analyst. You will be provided with the content of three files to analyze: "all_tool.json", "target.json" and "answer.json". The content is as follows:

all_tool.json:
{all_tool_content}

target.json:
{target_content}

answer.json:
{answer_content}

# Description
- "all_tool.json": This file contains all tool names, including both safe tools and vulnerable tools
- "target.json": Security attribute scan results of tools, including tool names and corresponding vulnerabilities; however, these results need verification. If some tool names are repeated, please merge the vulnerability information first, then proceed with subsequent judgment
- "answer.json": The correct answers (ground truth). It only contains high-risk tool names and their corresponding vulnerabilities. Note: This file does not contain information about safe tools

# Evaluation:
For each tool in "all_tool.json":
    If the tool appears in both "answer.json" and "target.json", and the vulnerability type in "answer.json" is semantically equivalent or highly related to any vulnerability type for that tool in "target.json" for that tool, then the evaluation result for that tool is considered correct. Increment "True_Positive_Num" by 1.

Please output your thought process.
"""