FROM node:24-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm install --no-audit --no-fund
COPY . .
ARG VITE_API_BASE_URL=""
ARG VITE_BUSINESS_PHONE=""
ARG VITE_BUSINESS_EMAIL="info@smartdiag504.com"
ARG VITE_BUSINESS_ADDRESS="San Pedro Sula, Honduras"
ARG VITE_WHATSAPP_URL=""
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
ENV VITE_BUSINESS_PHONE=${VITE_BUSINESS_PHONE}
ENV VITE_BUSINESS_EMAIL=${VITE_BUSINESS_EMAIL}
ENV VITE_BUSINESS_ADDRESS=${VITE_BUSINESS_ADDRESS}
ENV VITE_WHATSAPP_URL=${VITE_WHATSAPP_URL}
RUN npm run build

FROM nginx:1.29-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 8080
HEALTHCHECK --interval=10s --timeout=3s --retries=3 CMD wget -qO- http://127.0.0.1:8080/health || exit 1
