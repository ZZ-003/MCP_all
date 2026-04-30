# 统计数量、只做 TN 的语义分析
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


# 直接统计成数量
# PROMPT = """
# You are a Result Analyst. You will be provided with the content of three files to analyze: "all_tool.json", "target.json" and "answer.json". The content is as follows:

# all_tool.json:
# {all_tool_content}

# target.json:
# {target_content}

# answer.json:
# {answer_content}

# # Description
# - "all_tool.json": This file contains all tool names, including both safe tools and vulnerable tools
# - "target.json": Security attribute scan results of tools, including tool names and corresponding vulnerabilities; however, these results need verification. If some tool names are repeated, please merge the vulnerability information first, then proceed with subsequent judgment
# - "answer.json": The correct answers (ground truth). It only contains high-risk tool names and their corresponding vulnerabilities. Note: This file does not contain information about safe tools

# # First Evaluation: Evaluate the Validity of Results
# For each tool in "all_tool.json":
#     1. If the tool appears in both "answer.json" and "target.json", and the vulnerability type in "answer.json" is semantically equivalent or highly related to any vulnerability type for that tool in "target.json" for that tool, then the evaluation result for that tool is considered correct. Increment "True_Positive_Num" by 1.
#     2. If the tool does not appear in "answer.json" but appears in "target.json", and the corresponding entry in "target.json" indicates the existence of a vulnerability, then this evaluation is considered incorrect. Increment "False_Positive_Num" by 1.
#     3. If the tool appears in "answer.json" but does not appear in "target.json", or the corresponding entry in "target.json" does not show any vulnerabilities, then this evaluation is considered a miss/detection failure. Increment "False_Negative_Num" by 1.


# # Second Evaluation: Evaluate the Accuracy of Results
#     1. If a tool appears in "target.json" and also appears in "all_tool.json", then this evaluation is considered correct. Increment "Correctly_identified_tools_Num" by 1.
#     2. If a tool appears in "target.json" but does not appear in "all_tool.json", then this evaluation is considered incorrect. Increment "Incorrectly_identified_tools_Num" by 1.
#     (For points 1 & 2 above: Only focus on the tool name, no need to focus on other information such as tool functions)

# Please output your thought process.
# """

# 统计数字，带例子
# PROMPT = """
# You are a Result Analyst. You will be provided with the content of three files to analyze: "all_tool.json", "target.json" and "answer.json". The content is as follows:

# all_tool.json:
# {all_tool_content}

# target.json:
# {target_content}

# answer.json:
# {answer_content}

# # Description
# - "all_tool.json": This file contains all tool names, including both safe tools and vulnerable tools
# - "target.json": Security attribute scan results of tools, including tool names and corresponding vulnerabilities; however, these results need verification. If some tool names are repeated, please merge the vulnerability information first, then proceed with subsequent judgment
# - "answer.json": The correct answers (ground truth). It only contains high-risk tool names and their corresponding vulnerabilities. Note: This file does not contain information about safe tools

# # First Evaluation: Evaluate the Validity of Results
# For each tool in "all_tool.json":
#     1. If the tool appears in both "answer.json" and "target.json", and the vulnerability type in "answer.json" is semantically equivalent or highly related to any vulnerability type for that tool in "target.json" for that tool, then the evaluation result for that tool is considered correct. Increment "True_Positive_Num" by 1.
#         For example:
#             // answer.json (Ground Truth)
#             {{
#             "execute_command": ["Command Injection"]
#             }}

#             // target.json (扫描结果)
#             {{
#             "execute_command": [
#                 "Remote Code Execution",
#                 "Command Injection"]
#             }}
#             Then: True_Positive_Num += 1

#     2. If the tool does not appear in "answer.json" but appears in "target.json", and the corresponding entry in "target.json" indicates the existence of a vulnerability, then this evaluation is considered incorrect. Increment "False_Positive_Num" by 1.
#         For example:
#             // answer.json (Ground Truth)
#             {{
#             "read_database": ["SQL Injection"]
#             }}

#             // target.json (扫描结果)
#             {{
#             "read_database": ["SQL Injection"],
#             "write_file": ["Arbitrary File Write"]
#             }}
#             Then: False_Positive_Num += 1
    
#     3. If the tool appears in "answer.json" but does not appear in "target.json", or the corresponding entry in "target.json" does not show any vulnerabilities, then this evaluation is considered a miss/detection failure. Increment "False_Negative_Num" by 1.
#         For example:
#             // answer.json (Ground Truth)
#             {{
#             "parse_input": ["XSS"],
#             "read_database": ["SQL Injection"]
#             }}

#             // target.json (扫描结果)
#             {{
#             "read_database": ["SQL Injection"]
#             }}
#             Then:  False_Negative_Num += 1


# # Second Evaluation: Evaluate the Accuracy of Results
#     1. If a tool appears in "target.json" and also appears in "all_tool.json", then this evaluation is considered correct. Increment "Correctly_identified_tools_Num" by 1.
#     2. If a tool appears in "target.json" but does not appear in "all_tool.json", then this evaluation is considered incorrect. Increment "Incorrectly_identified_tools_Num" by 1.
#     (For points 1 & 2 above: Only focus on the tool name, no need to focus on other information such as tool functions)

# Please output your thought process.
# """



# PROMPT = """
# You are a result analyst. You will receive the content of three files for analysis: "all_tool.json", "target.json", and "answer.json". The content is as follows:

# all_tool.json:
# {all_tool_content}

# target.json:
# {target_content}

# answer.json:
# {answer_content}

# # Description
# - "all_tool.json": This file contains all tool names, including safe tools and tools with malicious descriptions
# - "target.json": Scanning results of tool attributes, including tool names and their corresponding judgment results; however, these results need verification. If certain tool names are duplicated, please merge the information first before proceeding with subsequent judgment
# - "answer.json": The correct answers (ground truth). It only contains malicious tool names and their corresponding judgment results. Note: This file does not contain information about safe tools

# # Evaluation:
# For each tool in "all_tool.json":
#     If the tool appears in both "answer.json" and "target.json", and the answer content in "answer.json" is consistent or highly similar to the judgment result for that tool in "target.json", then the evaluation result for that tool is considered correct. Increment "True_Positive_Num" by 1.
# """
