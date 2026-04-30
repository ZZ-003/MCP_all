FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY flag_verifier.py .
COPY all_server_flags.json .

EXPOSE 8848

CMD ["python", "flag_verifier.py"]