FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# NOTE: the Claude Agent SDK drives the Claude Code engine and may need the Claude Code
# CLI (Node) at runtime. If so, add:
#   RUN apt-get update && apt-get install -y nodejs npm && npm i -g @anthropic-ai/claude-code
# Alternatively, implement the agent loop directly on the Anthropic Messages API.
COPY . .
EXPOSE 8080
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--reload"]
