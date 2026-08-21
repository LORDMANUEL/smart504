# Sistema visual SmartDiag504

**Estado:** dirección visual inicial para implementación y validación con la empresa. El símbolo incluido es provisional y debe someterse a búsqueda de marca y aprobación antes de registro o impresión masiva.

## 1. Idea central

SmartDiag504 se presenta como un taller técnicamente competente, ordenado y transparente. La identidad combina la precisión de una herramienta de diagnóstico con la claridad de un servicio que muestra al cliente qué se encontró, qué se autorizó y qué se resolvió.

**Promesa verbal:** **Diagnóstico preciso. Servicio transparente.**

## 2. Personalidad

- Técnica sin ser fría.
- Segura sin exagerar resultados.
- Clara al explicar costos, evidencia y compatibilidad.
- Moderna, pero orientada a operación real de taller.
- Profesional en documentos, pantallas, uniformes y señalización.

## 3. Paleta

| Token | Uso principal | Valor |
|---|---|---:|
| `--sd-navy-950` | encabezados, navegación, contraste | `#071827` |
| `--sd-blue-600` | acción primaria, vínculos, progreso | `#0878d1` |
| `--sd-cyan-500` | diagnóstico, datos, tecnología | `#17a9c2` |
| `--sd-amber-500` | llamadas comerciales y atención puntual | `#d89a24` |
| `--sd-white` | fondo principal | `#ffffff` |
| `--sd-slate-50` | bandas y fondos secundarios | `#f6f8fa` |
| `--sd-ink` | texto principal | `#10202f` |

El ámbar no reemplaza los colores semánticos. Una falla debe continuar viéndose como falla y no como un elemento comercial.

## 4. Tipografía

La pila prioriza fuentes que ya existen en Windows y navegadores corporativos:

```css
font-family: "Aptos", "Segoe UI Variable", "Segoe UI", Inter, Roboto, Helvetica, Arial, sans-serif;
```

- Títulos: peso 700–800, tracking reducido.
- Texto: peso 400–500, interlineado 1.5 o superior.
- Etiquetas y tablas: 12–14 px, contraste suficiente y sin depender únicamente de mayúsculas.
- VIN, SKU y números de parte: fuente monoespaciada.

## 5. Marca

El símbolo provisional combina una forma `S`, líneas de lectura y nodos de diagnóstico. Debe conservar espacio libre equivalente a un cuarto de su ancho. No debe deformarse, girarse, añadir efectos 3D ni colocarse sobre fondos sin contraste.

Versiones requeridas antes del lanzamiento:

1. símbolo cuadrado;
2. combinación horizontal símbolo + SmartDiag504;
3. monocromática clara;
4. monocromática oscura;
5. favicon y PWA;
6. guía para bordado, uniforme, vehículo y rótulo.

## 6. Interfaz

- Fondo blanco real, no crema.
- Contenedores abiertos; se reservan tarjetas para agrupaciones que realmente necesitan borde.
- Botones con altura mínima de 44 px.
- Tablas en escritorio; listas estructuradas en móvil.
- Estados siempre incluyen texto y forma, no solamente color.
- Fotografías deben mostrar diagnóstico, herramientas, repuestos y trabajo real.
- Las compatibilidades de repuestos muestran `Confirmada`, `Probable` o `Requiere validación`.

## 7. Voz de producto

**Correcto:** “La compatibilidad con este VIN debe confirmarse antes de facturar.”  
**Incorrecto:** “Seguro le queda.”

**Correcto:** “Se detectó baja presión. Falta confirmar la causa con una prueba de fuga.”  
**Incorrecto:** “La IA dice que es el compresor.”

## 8. Archivos canónicos

- `packages/design-system/tokens.css`
- `packages/design-system/components.css`
- `packages/design-system/brand.ts`
- `packages/design-system/assets/smartdiag504-mark.svg`

Los frontends importan o copian estos archivos durante su compilación. No deben declarar una segunda paleta independiente.
