FROM python:3.12-alpine
WORKDIR /app
RUN addgroup -g 10001 smartdiag && adduser -D -u 10001 -G smartdiag smartdiag
COPY services/heartbeat-agent/agent.py /app/agent.py
RUN chown -R smartdiag:smartdiag /app
USER 10001:10001
EXPOSE 8091
HEALTHCHECK --interval=15s --timeout=4s --retries=4 CMD wget -qO- http://127.0.0.1:8091/health || exit 1
CMD ["python", "/app/agent.py"]
