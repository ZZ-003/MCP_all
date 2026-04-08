from pathlib import Path

# 获取当前文件的完整路径（绝对路径）
current_file = Path(__file__).resolve()

# 或者一步获取当前文件所在目录
current_dir = Path(__file__).resolve().parent

# 打印结果
print(f"当前文件路径: {current_file}")
print(f"当前文件所在目录: {current_dir}")
