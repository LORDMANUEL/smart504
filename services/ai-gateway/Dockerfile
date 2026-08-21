FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /srv/ai-gateway
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl ca-certificates \
 && rm -rf /var/lib/apt/lists/*
COPY services/ai-gateway/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY services/ai-gateway/smartdiag_ai_gateway ./smartdiag_ai_gateway
RUN chown -R 10001:10001 /srv/ai-gateway
USER 10001:10001
EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=4s --retries=4 CMD curl -fsS http://127.0.0.1:8000/health || exit 1
CMD ["uvicorn", "smartdiag_ai_gateway.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips=*"]
