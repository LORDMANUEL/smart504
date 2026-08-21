# SmartDiag Workshop Frappe App

Aplicación automotriz para ERPNext v16 y Beveren FSM. Extiende `Service Order`; no crea una OT paralela.

## Instalación dentro de Bench

```bash
bench get-app smartdiag_workshop <repository-url>
bench --site <site> install-app smartdiag_workshop
bench --site <site> migrate
```

La imagen de producción instala también `smartdiag-domain` y el fork fijado de Beveren.
