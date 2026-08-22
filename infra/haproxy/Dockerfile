FROM haproxy:3.0-alpine
COPY infra/haproxy/haproxy.cfg /usr/local/etc/haproxy/haproxy.cfg
RUN haproxy -c -f /usr/local/etc/haproxy/haproxy.cfg

