FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 复制requirements.txt并安装Python依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY flag_verifier.py .
COPY all_server_flags.json .

# 暴露端口
EXPOSE 8848

# 运行应用
CMD ["python", "flag_verifier.py"]