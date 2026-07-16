FROM python:3.11-slim

# Non-root user for security
RUN useradd -m -u 1000 appuser

WORKDIR /app

# Install dependencies first (better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY src/ ./src/
COPY chat_ui.html .

RUN chown -R appuser:appuser /app
USER appuser

# Default: chat server. Override CMD in k8s for mcp-server.
CMD ["python", "src/chat_server.py"]
