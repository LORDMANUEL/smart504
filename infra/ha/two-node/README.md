# SmartDiag504 — alta disponibilidad real en dos VPS + testigo

## Qué protege cada nivel

| Nivel | Implementación | Resultado |
|---|---|---|
| Web pública, PWA y API | Réplicas en VPS A y VPS B | Activo/activo, health checks y failover |
| Entrada pública | Keepalived unicast + VIP o balanceador externo | El tráfico cambia de nodo |
| Workers de alertas | Lease PostgreSQL + fencing token | Solo un worker procesa reglas |
| PostgreSQL | Patroni en A/B + etcd en A/B/testigo | Elección segura de primario |
| MariaDB | Galera A/B + `garbd` en testigo | Quorum y protección contra split-brain |
| ERPNext/Frappe | Activo/pasivo | No duplica jobs, facturas ni movimientos |
| Archivos | S3 externo y NFS altamente disponible para `sites` | Estado compartido entre nodos |
| Respaldo | Restic fuera de ambos VPS | Recuperación ante pérdida del clúster |

## Restricción indispensable

Dos servidores por sí solos no forman quorum. Se requiere un tercer testigo independiente, aunque sea pequeño, para etcd y `garbd`. Si el testigo no está disponible, el sistema debe preferir detener escrituras antes que aceptar dos primarios.

## Direcciones mínimas

- VPS A: IP privada fija, interfaz de red y prioridad VRRP 150.
- VPS B: IP privada fija, interfaz de red y prioridad VRRP 100.
- Testigo: IP privada fija fuera de ambos hosts.
- VIP: dirección flotante entregada por el proveedor o admitida en la red privada.
- Almacenamiento S3 externo para imágenes/evidencias.
- NFS/volumen compartido altamente disponible para `frappe-sites`, o una integración S3 de archivos Frappe validada antes de producción.

## Orden de despliegue

1. Crear DNS, red privada, firewall y VIP.
2. Levantar el testigo con `witness/compose.witness.yaml`.
3. Levantar etcd en A y B.
4. Inicializar Patroni PostgreSQL en A/B.
5. Inicializar Galera en A con `GALERA_BOOTSTRAP=1`; después arrancar B sin bootstrap.
6. Verificar quorum y replicación antes de instalar aplicaciones.
7. Montar el mismo almacenamiento de `frappe-sites` en ambos nodos.
8. Instalar el stack de aplicaciones en ambos nodos usando endpoints HA de base de datos y S3.
9. Instalar Keepalived y sus scripts de `notify_master`/`notify_backup`.
10. Ejecutar pruebas de partición, pérdida de A, pérdida de B, pérdida del testigo y restauración.

## Política de Frappe

En estado `MASTER`, el nodo ejecuta `frappe-backend`, `frappe-frontend`, WebSocket, workers y scheduler. En estado `BACKUP`, esos servicios escritores se detienen. La web pública, la PWA, la API y sus heartbeats permanecen activas en ambos nodos.

## Gate de producción

No se permite declarar alta disponibilidad hasta completar `HA_ACCEPTANCE.md` con evidencia de cada prueba. Una validación `docker compose config` solo demuestra sintaxis, no failover físico.
