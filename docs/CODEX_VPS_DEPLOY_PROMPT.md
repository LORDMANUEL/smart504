# CODEX_VPS_DEPLOY_PROMPT.md

Copie el texto siguiente en Codex cuando el ZIP ya esté disponible en la VPS:

```text
Trabaja como ingeniero de despliegue responsable de SmartDiag504.

1. Extrae smartdiag504_platform_complete_v0.4.0.zip en /opt/smartdiag504.
2. Lee AGENTS.md, README.md, SMARTDIAG504_IMPLEMENTATION_MASTER.md y docs/deployment/VPS_RUNBOOK.md antes de cambiar archivos.
3. No borres datos, volúmenes, bases, backups ni .env existentes.
4. Comprueba Debian/Ubuntu, CPU, RAM, disco, DNS, puertos 80/443 y acceso saliente.
5. Ejecuta:
   sudo bash scripts/bootstrap-host.sh --app-dir /opt/smartdiag504 --open-firewall
6. Copia .env.example a .env solamente si .env no existe y ejecuta:
   bash scripts/generate-secrets.sh .env
7. Detente para que el operador confirme dominios, correo ACME, teléfono, WhatsApp, dirección, backups, proveedor LLM y política fiscal. Nunca muestres secretos.
8. Ejecuta la validación estática:
   bash scripts/verify.sh
9. Despliega el stack completo, sin omitir ERPNext/Beveren/SmartDiag:
   sudo bash scripts/codex-vps-deploy.sh --env-file .env --observability
   Agrega --local-ai únicamente cuando la VPS tenga memoria suficiente y se haya aprobado Ollama.
10. Verifica todos los contenedores, logs, /health, /ready, catálogo, seis estados de OT, chatbot, landing, PWA y ping de ERPNext.
11. Ejecuta bash scripts/ha-smoke-test.sh .env para probar failover de réplicas de aplicación en la misma VPS.
12. Toma un backup con scripts/backup.sh, valida manifest.sha256 y documenta la restauración pendiente en staging.
13. No declares alta disponibilidad física: una sola VPS con réplicas A/B no cubre pérdida del host. Para HA física usa infra/ha/two-node con dos VPS y un tercer testigo y completa HA_ACCEPTANCE.md.
14. Entrega un informe con comandos ejecutados, exit codes, imágenes construidas, servicios saludables, fallos reales, cambios realizados y gates todavía pendientes.

Reglas inmutables:
- ERPNext es la única verdad de inventario, compras, POS, caja, facturas, pagos y contabilidad.
- Service Order de Beveren es la única OT; no crear una segunda OT.
- No escribir directamente en MariaDB desde FastAPI ni desde el navegador.
- No exponer ADMIN_API_TOKEN, FRAPPE_API_SECRET, claves LLM, contraseñas o .env.
- El chatbot es lectura/orientación; no factura, cobra, mueve stock ni libera vehículos.
- Toda corrección se hace con prueba roja/verde y verificación fresca.
```

## Comando automatizado

Después de revisar `.env`:

```bash
sudo bash scripts/codex-vps-deploy.sh --env-file .env --observability
```

Con IA local:

```bash
sudo bash scripts/codex-vps-deploy.sh --env-file .env --local-ai --observability
```

El script llama a `scripts/install-vps.sh`, construye las imágenes, crea el sitio Frappe, instala ERPNext, Beveren FSM y `smartdiag_workshop`, levanta la plataforma y ejecuta smoke tests.
