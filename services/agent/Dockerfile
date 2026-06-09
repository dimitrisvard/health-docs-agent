FROM python:3.12-slim
WORKDIR /app
# The Claude Agent SDK drives the Claude Code engine via the Node CLI, so it must be
# present in the agent image (Phase 4). Installed before pip for better layer caching.
RUN apt-get update \
    && apt-get install -y --no-install-recommends nodejs npm \
    && npm install -g @anthropic-ai/claude-code \
    && apt-get purge -y --auto-remove \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8080
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--reload"]
