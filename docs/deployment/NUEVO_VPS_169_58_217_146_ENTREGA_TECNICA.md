# SmartDiag504 — entrega técnica del VPS nuevo

Fecha de corte: 2026-08-22  
Servidor de pruebas: `169.58.217.146`  
Orquestador: Coolify 4.3.10 sobre Docker  
Estado del dominio definitivo: en revisión; se usan dominios temporales `sslip.io`.

## 1. Regla de seguridad de credenciales

Las contraseñas, llaves privadas, tokens y secretos **no forman parte de este documento ni del repositorio**. Coolify los guarda como variables cifradas. La llave SSH autorizada se mantiene únicamente en el equipo custodio. Para entregar accesos se debe usar un gestor de contraseñas y rotarlos al cambiar de responsable.

Inventario de secretos que debe custodiar el propietario:

- administrador de Coolify;
- llave SSH del servidor;
- administrador de ERPNext;
- usuarios funcionales individuales;
- PostgreSQL, MariaDB y Valkey;
- tokens internos de API y eventos;
- claves S3 de Garage;
- credenciales SMTP cuando el dominio esté disponible.

Nunca enviar estos valores por correo sin cifrar, WhatsApp, capturas o archivos Markdown.

## 2. Arquitectura

### Núcleo transaccional

- `public-web-a/b`: landing, tienda y portal cliente;
- `ops-web-a/b`: operaciones de taller;
- `platform-api-a/b`: API y reglas de negocio;
- PostgreSQL: proyecciones operativas, sesiones y auditoría;
- ERPNext/Frappe + Beveren FSM + SmartDiag Workshop: fuente autoritativa ERP;
- MariaDB y Valkey;
- HAProxy: balanceo interno de las réplicas;
- Traefik de Coolify: TLS y publicación externa.

### Servicios auxiliares

- Ollama con `gemma3:270m`;
- dos réplicas de `ai-gateway`;
- ChromaDB y carga inicial RAG;
- Garage S3 para evidencia privada;
- ClamAV para analizar cargas antes de almacenarlas.

Los auxiliares se despliegan desde `compose.coolify-extras.yaml` como otra aplicación Coolify y se conectan a la red privada del núcleo. Esta separación evita recrear ERPNext al actualizar IA o antivirus.

## 3. Rutas temporales

- Landing: `https://taller.169.58.217.146.sslip.io/lading`
- Portal cliente: `https://clientes.169.58.217.146.sslip.io/lading/cliente`
- Operaciones: `https://app.169.58.217.146.sslip.io/tallerv1/login`
- API: `https://api.169.58.217.146.sslip.io/ready`
- ERPNext: `https://erp.169.58.217.146.sslip.io`
- Coolify: `http://169.58.217.146:8000`

Cuando el dominio esté liberado se reemplazarán estas rutas en Coolify, `CORS_ORIGINS`, `ERP_EXTERNAL_URL` y `FRAPPE_BASE_URL` sin recrear bases de datos.

## 4. Proxy y administración

Coolify ya instala y administra Traefik en los puertos 80/443. No se debe instalar Nginx ni otro Traefik en el host, porque competirían por esos puertos. HAProxy vive dentro de SmartDiag504 y sólo balancea servicios internos. Coolify es el panel autorizado para contenedores, despliegues, variables y logs; no se agrega Portainer para evitar una segunda superficie administrativa privilegiada.

## 5. Correo

El servidor de correo definitivo queda bloqueado hasta disponer del dominio y acceso DNS. Para entrega real hacen falta:

1. nombre `mail.<dominio>`;
2. registros MX, SPF, DKIM y DMARC;
3. PTR/rDNS solicitado al proveedor del VPS;
4. puertos 25, 465, 587, 993 autorizados;
5. prueba de reputación y entregabilidad.

Sin lo anterior, instalar Postfix/Dovecot produciría correo rechazado o marcado como spam. La aplicación permite configurar SMTP en Coolify cuando estos datos estén disponibles. No se declara correo productivo antes de probar envío y recepción externos.

## 6. Creación e importación de repuestos

Ruta: Operaciones → Configuración → Catálogo por vehículo.

1. Descargar la plantilla Excel vigente.
2. Completar repuestos con código, descripción, OEM, vehículo compatible, costo y precio.
3. Repetir el código para cada compatibilidad adicional.
4. Cargar el archivo y revisar la vista previa.
5. Corregir todas las filas rechazadas.
6. Confirmar la importación; la API la envía a ERPNext.
7. Abrir Catálogo, seleccionar el producto y cargar una imagen JPG, PNG o WebP.
8. Confirmar precio, costo importado, margen mínimo y clasificación ABC/XYZ.

No se debe crear un artículo desde Mostrador. Mostrador únicamente selecciona existencias catalogadas y permite solicitar un artículo faltante para Compras.

## 7. Validación obligatoria después de cada despliegue

```bash
docker ps --format '{{.Names}}|{{.Status}}'
curl -fsS https://api.169.58.217.146.sslip.io/ready
curl -fsS https://erp.169.58.217.146.sslip.io/api/method/ping
```

Además se debe validar desde un usuario real: iniciar sesión, crear una cita, convertir cotización a OT, reservar y entregar repuesto, cobrar, emitir documento y conciliarlo en ERPNext. Un HTTP 200 por sí solo no certifica esos flujos.

## 8. Respaldo

Los volúmenes persistentes deben incluir PostgreSQL, MariaDB/Frappe, Valkey, Garage y ChromaDB. El respaldo externo no se alojará únicamente en este VPS. Una copia sólo se considera válida después de restaurarla de manera aislada y eliminar la restauración temporal.

## 9. Estado de entrega

El núcleo está desplegado y sus healthchecks fueron validados. IA, S3 y antivirus requieren validación posterior al despliegue del Compose auxiliar. Correo y dominio permanecen pendientes de terceros. No declarar producción total mientras alguna de estas comprobaciones esté pendiente.
