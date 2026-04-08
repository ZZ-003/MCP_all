FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV SANDBOX_ROOT=/tmp/sandbox
RUN mkdir -p $SANDBOX_ROOT

EXPOSE 8000

CMD ["python", "main.py"]
