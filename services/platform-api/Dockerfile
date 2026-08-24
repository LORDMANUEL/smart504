FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /srv/platform-api
RUN apt-get update && apt-get install -y --no-install-recommends curl libjpeg62-turbo libpng16-16 libwebp7 && rm -rf /var/lib/apt/lists/*
COPY packages/smartdiag_domain /tmp/smartdiag_domain
RUN pip install /tmp/smartdiag_domain
COPY services/platform-api/requirements.txt ./requirements.txt
RUN pip install -r requirements.txt
COPY services/platform-api/ .
COPY apps/public-web/public/brand/smartdiag504-logo.png ./assets/smartdiag504-logo.png
RUN mkdir -p /var/lib/smartdiag/media && chown -R 10001:10001 /srv/platform-api /var/lib/smartdiag
USER 10001:10001
EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=4s --retries=4 CMD curl -fsS http://127.0.0.1:8000/ready || exit 1
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips=*"]
