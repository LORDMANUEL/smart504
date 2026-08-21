# Mostrador, cotización técnica y citas desde Kanban

## Objetivo

Cerrar tres recorridos operativos sin datos libres: venta guiada en Mostrador, mano de obra seleccionada por el técnico y creación de citas desde Kanban.

## Flujo de Mostrador

Al entrar a `https://taller.nexusmedi.org/tallerv1/mostrador` se abre un recorrido contextual. La cajera busca por VIN, selecciona únicamente artículos existentes con precio y existencia, cotiza o cobra. Si no existe el artículo, registra una solicitud a Compras; Mostrador no crea ítems.

## Flujo de cotización técnica

1. Abrir una tarjeta del Kanban o desde **Mi trabajo técnico**.
2. Entrar a **Mano de obra**.
3. Seleccionar técnico, servicio del catálogo y tipo de hora.
4. El servidor toma código, descripción y duración del catálogo controlado. No acepta conceptos inventados.
5. **Cotizaciones > Armar desde OT** incorpora esa mano de obra y los repuestos solicitados.

El catálogo demo contiene cinco conceptos. El costo salarial permanece privado y la venta aplica la tarifa normal o especializada configurada al técnico.

## Flujo de citas desde Kanban

1. Entrar a `https://taller.nexusmedi.org/tallerv1/login`.
2. Pulsar **Nueva cita** en el encabezado del Kanban.
3. Completar cliente, contacto, vehículo/VIN, servicio, fecha y motivo.
4. La cita se guarda como confirmada con origen `KANBAN`.
5. Se registra el evento auditable `RECEPTION.BOOKING_CREATED_FROM_KANBAN`.
6. La nueva cita aparece inmediatamente en **Citas** sin recargar toda la aplicación.

## Criterios de validación en VPS

- `POST /api/v1/operations/bookings` responde 201, persiste la cita y su evento.
- `GET /api/v1/operations/labor-catalog` devuelve cinco conceptos sin exponer costo.
- El frontend compila dentro del contenedor del VPS.
- El modal de cita se abre desde Kanban y valida campos obligatorios.
- La OT ya no muestra entradas libres para código, descripción ni horas de mano de obra.
- Mostrador abre su recorrido contextual y conserva el bloqueo de artículos sin código, precio o existencia.

No se ejecutan pruebas ni compilaciones en la PC local. El despliegue se limita a `platform-api` y `ops-web`; no se reinicia Coolify, Traefik ni servicios ajenos.
