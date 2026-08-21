FROM python:3.12-alpine
WORKDIR /app
COPY services/alerts-worker/worker.py /app/worker.py
USER 10001:10001
EXPOSE 8090
HEALTHCHECK --interval=15s --timeout=4s --retries=3 CMD wget -qO- http://127.0.0.1:8090/health || exit 1
CMD ["python", "/app/worker.py"]
