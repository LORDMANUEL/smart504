# SmartDiag504 — entrega técnica del VPS nuevo

> Para incorporar una empresa consulte el [paquete de incorporación](../onboarding/PAQUETE_INCORPORACION_EMPRESA.md), el [diccionario de carga](../onboarding/DICCIONARIO_Y_REGLAS_DE_CARGA.md) y el [manual de usuarios y aceptación](../onboarding/MANUAL_CARGA_USUARIOS_Y_ACEPTACION.md).

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

En el VPS de aceptación, las credenciales iniciales están en
`/root/.config/smartdiag504/acceptance-owner.env`, con permisos `0600`. Sólo
`root` puede leerlas. Deben cambiarse en el primer ingreso y eliminarse después
de registrar al propietario definitivo en el gestor de contraseñas.

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

Prueba de aceptación ejecutada el 2026-08-22: la plantilla produjo 5 manos de
obra, 9 repuestos, cero errores y 24 relaciones de compatibilidad; la aplicación
a ERPNext respondió `applied`.

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

El núcleo y el Compose auxiliar están desplegados. Se validó: API/ERP/web por
HTTPS; S3 con escritura, lectura y eliminación; ClamAV con archivo seguro y
rechazo EICAR; IA con generación Ollama y cinco fuentes RAG; login de propietario;
vista previa y aplicación de catálogo a ERPNext. Fail2ban protege SSH con el
jail `sshd` activo.

Correo externo y dominio permanecen pendientes de terceros. El firewall del
host requiere una política explícita para `DOCKER-USER`; activar UFW sin ella no
protege los puertos publicados por Docker y puede afectar Coolify. No declarar
correo productivo ni dominio definitivo mientras esas comprobaciones estén
pendientes.
