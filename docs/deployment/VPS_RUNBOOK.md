# Runbook de despliegue VPS — SmartDiag504 v0.4.0

## 1. Resultado del despliegue

El stack instala en una VPS:

- Caddy con TLS automático;
- HAProxy interno;
- dos réplicas de landing/tienda;
- dos réplicas de PWA operacional;
- dos réplicas de Platform API;
- dos réplicas de AI Gateway;
- dos heartbeat agents;
- dos workers de alertas con lease;
- PostgreSQL, Valkey y ChromaDB;
- Garage S3 para evidencia/objetos;
- MariaDB;
- Frappe v16 + ERPNext v16 + Beveren FSM fijado + `smartdiag_workshop`;
- scheduler y workers Frappe;
- backup runner;
- Ollama opcional;
- Prometheus, Grafana y Blackbox opcionales.

La instalación de una sola VPS tiene redundancia de **contenedor/proceso** para la capa web y API. No protege contra pérdida física del host. La topología física está en `infra/ha/two-node/` y exige dos VPS más un testigo.

## 2. Capacidad

Mínimo recomendado sin LLM local:

- 8 vCPU x86_64;
- 8 GB RAM como piso técnico, 16 GB recomendado;
- 100 GB NVMe, con 30 GB libres antes de instalar;
- Debian 12/13 o Ubuntu LTS;
- IP pública fija;
- DNS administrable;
- salida HTTPS a repositorios de imágenes y certificados.

Con Ollama y un modelo de 7B: 16 GB RAM como piso y 24–32 GB recomendado. El ERP tiene prioridad sobre el LLM.

## 3. DNS y firewall

Crear A/AAAA hacia la VPS:

| Variable | Función |
|---|---|
| `PUBLIC_SITE_ADDRESS` | Landing, tienda, reservas y chatbot |
| `CUSTOMER_SITE_ADDRESS` | Portal cliente preparado |
| `OPS_SITE_ADDRESS` | PWA del taller |
| `API_SITE_ADDRESS` | API pública/operacional |
| `ERP_SITE_ADDRESS` | ERPNext/Frappe |

Puertos públicos: TCP 22, 80, 443 y UDP 443. No publicar MariaDB, PostgreSQL, Valkey, ChromaDB, Garage ni paneles de observabilidad.

## 4. Instalación por Codex

```bash
sudo mkdir -p /opt/smartdiag504
sudo chown "$USER":"$USER" /opt/smartdiag504
cd /opt/smartdiag504
unzip /ruta/smartdiag504_platform_complete_v0.4.0.zip
cd smartdiag504-platform-v0.4.0
```

Preparar host:

```bash
sudo bash scripts/bootstrap-host.sh \
  --app-dir /opt/smartdiag504 \
  --app-user "$USER" \
  --open-firewall
```

Crear configuración:

```bash
cp .env.example .env
bash scripts/generate-secrets.sh .env
chmod 600 .env
nano .env
```

Obligatorio revisar:

- todos los dominios y `ACME_EMAIL`;
- teléfono, WhatsApp, dirección y horarios;
- `FRAPPE_SITE_NAME`, igual a `ERP_SITE_ADDRESS`;
- destino Restic fuera de la VPS;
- política de fotografías y evidencias;
- proveedor del chatbot;
- configuración fiscal y pagos antes de vender/facturar.

Validación estática:

```bash
bash scripts/verify.sh
```

Despliegue completo:

```bash
sudo bash scripts/codex-vps-deploy.sh \
  --env-file .env \
  --observability
```

Con chatbot local vía Ollama:

```bash
sudo bash scripts/codex-vps-deploy.sh \
  --env-file .env \
  --local-ai \
  --observability
```

El comando directo equivalente es:

```bash
sudo bash scripts/install-vps.sh --env-file .env --observability
```

## 5. Secuencia automática

1. Verifica Docker, RAM, disco y variables obligatorias.
2. Genera secretos faltantes sin imprimirlos.
3. Intenta descargar fotografías reales y conserva fallback remoto si el origen no responde.
4. Valida `docker compose config`.
5. Construye frontends, API, IA, workers, backup y la imagen Frappe personalizada.
6. Arranca PostgreSQL, Valkey, ChromaDB, Garage, MariaDB y Redis/Valkey de Frappe.
7. Crea el sitio Frappe de forma idempotente.
8. Instala ERPNext, Beveren FSM y `smartdiag_workshop`.
9. Crea el usuario de integración con claves generadas en `.env`.
10. Ejecuta migraciones y datos de demostración controlados.
11. Levanta réplicas A/B, proxy y TLS.
12. Prueba `/health`, `/ready`, catálogo, pedidos, Kanban, chatbot, landing, PWA y ping de ERPNext.

## 6. Verificación operativa

```bash
docker compose --env-file .env -f compose.yaml ps
docker compose --env-file .env -f compose.yaml logs --tail=200 frappe-site-init
docker compose --env-file .env -f compose.yaml logs --tail=200 platform-api-a
docker compose --env-file .env -f compose.yaml logs --tail=200 ai-gateway-a
bash scripts/verify.sh --runtime --env-file .env
```

Prueba de falla de réplica dentro de la misma VPS:

```bash
bash scripts/ha-smoke-test.sh .env
```

Esto detiene una réplica A, verifica que B continúa atendiendo y restaura A. No equivale a HA física.

## 7. Chatbot

### Modo seguro sin proveedor

```dotenv
LLM_PROVIDER=demo
```

El fallback responde servicios, reservas, repuestos, seguridad básica y proceso de OT sin depender de una clave externa.

### Ollama local

```dotenv
LLM_PROVIDER=ollama
LLM_BASE_URL=http://ollama:11434/v1
LLM_MODEL=qwen2.5:7b-instruct
```

Levantar con `--local-ai`.

### Proveedor compatible con OpenAI

```dotenv
LLM_PROVIDER=openai-compatible
LLM_BASE_URL=https://proveedor.example/v1
LLM_MODEL=modelo-aprobado
LLM_API_KEY=secreto
```

La clave solo existe en `.env` del servidor y nunca en el frontend. Antes de usar datos reales, aprobar minimización, retención y tratamiento de información.

## 8. ERPNext inicial

En `ERP_SITE_ADDRESS`:

1. Configurar empresa, HNL, zona horaria y período fiscal.
2. Validar catálogo contable con contabilidad.
3. Crear bodegas: principal, taller, tránsito, devoluciones, garantía y pedidos especiales.
4. Crear listas de precios: taller, mostrador, web y convenios.
5. Configurar POS/cajas y medios de pago.
6. Definir impuestos y comprobantes solo después de aprobación fiscal hondureña.
7. Crear usuarios y roles de asesor, técnico, bodega, caja, supervisor y contabilidad.
8. Ejecutar el flujo de `docs/testing/ACCEPTANCE_TESTS.md`.

## 9. Fotografías de repuestos

El administrador puede:

- subir JPG/PNG/WebP;
- establecer imagen principal y galería;
- quitar una imagen;
- descubrir candidatos por Google Programmable Search cuando `GOOGLE_CSE_API_KEY` y `GOOGLE_CSE_ID` estén configurados;
- revisar licencia/procedencia antes de guardar una copia.

La búsqueda de Google no convierte automáticamente una imagen en reutilizable. El administrador debe validar derechos y preferir fotografías propias o autorizadas.

## 10. Backup

Configurar Restic fuera de la VPS:

```dotenv
RESTIC_REPOSITORY=s3:https://objeto.example/smartdiag-backups
RESTIC_PASSWORD=...
BACKUP_S3_ACCESS_KEY=...
BACKUP_S3_SECRET_KEY=...
```

Backup manual:

```bash
bash scripts/backup.sh --env-file .env --output /var/backups/smartdiag504
```

Verificación:

```bash
bash scripts/verify-backup.sh /var/backups/smartdiag504/ARCHIVO.tar.gz
```

Un backup no se considera confiable hasta restaurarlo en una VPS de staging.

## 11. Restauración

Destructiva:

```bash
bash scripts/restore.sh \
  --env-file .env \
  --archive /var/backups/smartdiag504/ARCHIVO.tar.gz \
  --confirm RESTORE-SMARTDIAG504
```

Después:

```bash
bash scripts/verify.sh --runtime --env-file .env
```

## 12. Alta disponibilidad física

Para dos VPS:

- Patroni + etcd para PostgreSQL;
- Galera + `garbd` para MariaDB;
- tercer testigo independiente;
- S3 externo para objetos;
- almacenamiento compartido/estrategia validada para `frappe-sites`;
- Keepalived/VIP o balanceador del proveedor;
- Frappe activo/pasivo para evitar doble scheduler y escrituras duplicadas;
- Restic fuera de ambos hosts.

Ejecutar `infra/ha/two-node/HA_ACCEPTANCE.md`. Dos nodos sin testigo no tienen quorum seguro.

## 13. Gates de producción

- [ ] Construcción de todas las imágenes con exit code 0.
- [ ] Sitio nuevo instalado desde cero.
- [ ] Beveren v16 y selección de artículos certificados.
- [ ] Seis estados de OT probados de extremo a extremo.
- [ ] Dos técnicos, repuestos, devolución, QC, factura, pago y entrega probados.
- [ ] Catálogo, carga de imagen, checkout y chatbot probados.
- [ ] Roles/BOLA/IDOR y secretos revisados.
- [ ] Facturación hondureña aprobada.
- [ ] Pasarela aprobada con idempotencia.
- [ ] Restore drill y RPO/RTO medidos.
- [ ] Escaneo de dependencias/imágenes y pentest sin críticos abiertos.
