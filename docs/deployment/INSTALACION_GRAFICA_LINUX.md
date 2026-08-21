# Instalación guiada de SmartDiag504 en Linux

## Requisitos

- VPS nueva con Debian 12 o Ubuntu 24.04.
- 8 vCPU, 16 GB RAM y 80 GB SSD para ERPNext, Garage e IA local.
- Usuario con `sudo` o acceso `root`.
- Cinco registros DNS tipo A apuntando a la IPv4 de la VPS.
- Puertos 22, 80 y 443 disponibles.

## Instalación desde GitHub

```bash
sudo apt-get update
sudo apt-get install -y git
git clone https://github.com/LORDMANUEL/smart504.git
cd smart504
sudo bash install.sh
```

El asistente muestra formularios con `whiptail` cuando está disponible y preguntas de texto en servidores mínimos. Solicita dominio, IP, correo TLS, nombre de empresa, teléfono y dirección. Luego:

1. genera `.env` con permisos `0600`;
2. fuerza `ENVIRONMENT=production` y `SEED_DEMO_DATA=false`;
3. genera secretos aleatorios;
4. instala Docker y utilidades compatibles;
5. configura UFW si fue autorizado;
6. construye las imágenes desde el código clonado;
7. inicia PostgreSQL, Valkey, Garage, ERPNext, aplicaciones, workers e IA;
8. espera readiness y ejecuta smoke tests.

## Dominios generados

Para un dominio base `empresa.hn`:

| Uso | Dirección |
|---|---|
| Landing y tienda | `taller.empresa.hn` |
| Portal del cliente | `clientes.empresa.hn` |
| Operaciones | `app.empresa.hn` |
| API | `api.empresa.hn` |
| ERPNext | `erp.empresa.hn` |

Cree los cinco registros DNS antes de iniciar. El instalador no puede modificar el proveedor DNS por usted.

## Ensayo sin instalar

```bash
sudo SMARTDIAG_BASE_DOMAIN=empresa.hn \
  SMARTDIAG_SERVER_IP=203.0.113.10 \
  SMARTDIAG_ACME_EMAIL=admin@empresa.hn \
  SMARTDIAG_BUSINESS_NAME='Mi Taller' \
  bash install.sh --non-interactive --dry-run
```

Este modo genera y valida la configuración, pero no instala paquetes ni levanta contenedores.

## Actualización

```bash
cd /ruta/donde/clono/smart504
sudo bash scripts/update-smartdiag.sh
```

El actualizador exige un árbol limpio, conserva una copia privada del entorno, acepta solamente avance rápido, reconstruye y ejecuta las pruebas servidas. Nunca guarda `.env` en Git.

## Límites de producción

El instalador deja operativa la plataforma, pero no puede certificar por sí solo CAI/fiscalidad hondureña, impresora/gaveta/datáfono, entregabilidad SMTP ni respaldo en otra infraestructura. Esos gates se completan con contador y proveedores antes de abrir la operación real.
