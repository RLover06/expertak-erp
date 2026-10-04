# Información real del negocio — carpeta SOFT

**Ruta:** `C:\path\to\SOFT`

Archivos analizados para alinear Expertak con la operación real (no datos de prueba genéricos).

---

## Archivos en la carpeta

| Archivo | Tamaño | Contenido |
|---------|--------|-----------|
| `01pro.xlsx` | ~7 MB | Exportación DIAN masiva (detalle documento a documento) |
| `consolidado_20251.xlsx` | ~12.5 MB | Resumen pivot por empresa + misma data en hoja `Reporte_DIAN` |
| `subir prueba.xlsx` | ~0.8 MB | Subconjunto para pruebas de carga (~3.700 filas) |

---

## Qué representa el negocio

### Plataforma multi-empresa (contador / consultoría FE)

Los Excel muestran **32 empresas (clientes)** en la columna `Empresa`, identificadas por NIT en `Identificacion`:

| NIT (anonimizado) | Empresa (anonimizada) | ~Filas en 01pro |
|---------------|-------------------|-----------------|
| 900000001 | EMPRESA CLIENTE A S.A.S | 8.973 |
| 900000002 | EMPRESA CLIENTE B IPS | 6.270 |
| 900000003 | EMPRESA CLIENTE C SAS | 4.909 |
| 900000004 | EMPRESA CLIENTE D SAS | 3.329 |
| … | (28 empresas más) | … |

**No es un solo facturador:** Expertak debe contemplar **selección de empresa activa** y filtros por NIT/`Identificacion`.

### Periodo y volumen

- **01pro.xlsx:** 32.472 documentos electrónicos.
- **Fechas emisión:** enero 2025 – octubre 2025.
- **Total acumulado (columna Total):** ~40.308 millones COP (suma de todas las filas; incluye emitido + recibido).

### Tipos de documento (operación real)

| Tipo | Cantidad aprox. (01pro) |
|------|-------------------------|
| Factura electrónica | 26.575 |
| Application response | 3.625 |
| Nota de crédito electrónica | 1.031 |
| Nómina individual | 801 |
| Documento equivalente (peajes, POS, etc.) | ~350+ |
| Otros (contingencia, soporte no obligados) | menores |

**MVP facturación:** priorizar **factura electrónica de venta** y **nota crédito**; nómina y documentos equivalentes en fases posteriores.

### Emitido vs recibido

| Grupo | Significado | Uso en Expertak |
|-------|-------------|-----------------|
| **Emitido** | Documentos que la empresa cliente expidió | Ventas / facturación propia |
| **Recibido** | Documentos de proveedores | Compras / panel compras |

Distribución aproximada: ~17.0k emitidos, ~15.5k recibidos.

Estados DIAN: casi todo **"Aprobado con notificación"** o **"Aprobado"**.

### Columnas del export DIAN (alineadas con Expertak)

Las 34 columnas coinciden con el importador actual:

`Tipo de documento`, `CUFE/CUDE`, `Folio`, `Prefijo`, impuestos (IVA, ICA, retenciones…), `Total`, `Estado`, `Grupo`, **`Identificacion`** (NIT empresa cliente), **`Empresa`** (razón social cliente).

---

## consolidado_20251.xlsx — dos hojas

### Hoja1 — Resumen pivot (INFORME RELACION_FE)

Tabla agregada, no movimientos contables línea a línea:

- **Empresa** | **Grupo** | **Tipo de documento**
- Métricas: `Suma de Subtotal`, `Suma de IVA2`, `Suma de OTROS`, `Suma de RETENCIONES`, `Suma de TOTAL2`

Es el mismo informe que ya genera Expertak desde documentos o desde import de resumen.

### Hoja Reporte_DIAN

32.472 filas — detalle idéntico al export de `01pro.xlsx` (base para importación y tabla dinámica).

---

## subir prueba.xlsx

- ~3.697 filas, mismas columnas que el export DIAN (sin columna `Empresa` en el extracto analizado — validar si el archivo de producción siempre incluye `Empresa` e `Identificacion`).
- Uso: **prueba de carga** en desarrollo (volumen moderado).
- Tipos predominantes: factura electrónica (~3.319), nómina, nota crédito.

---

## Implicaciones para el diseño Expertak

| Hallazgo | Decisión de diseño |
|----------|-------------------|
| 32 empresas cliente | Tabla `empresas` con NIT + razón social; usuario elige empresa activa |
| Emitido + Recibido | Mantener `grupo`; panel compras = recibido; emisión FE = emitido |
| Alto volumen (32k+ filas) | Supabase + import por lotes; índices en `cufe_cude`, `empresa`, fechas |
| Resumen pivot | Ya cubierto por `resumen_filas` / informe; validar con `consolidado_20251` Hoja1 |
| Contabilidad línea a línea | **No está en SOFT** — sigue viniendo del Excel consolidado (cuenta, débito, crédito) de otro origen |
| Facturación nueva | Por empresa: resolución, certificado y consecutivo **por cada cliente** que emita |

---

## Qué falta en SOFT (pedir si existe en otro lado)

1. Excel de **consolidado contable** con columnas: Empresa, Tercero, Fecha, Cuenta, Débito, Crédito.
2. **Resoluciones y prefijos** por cada una de las 32 empresas que vayan a **emitir** factura.
3. Lista de cuáles empresas son solo **importación/reporte** vs cuáles necesitan **emisión** FE desde Expertak.

---

## Relación con otras carpetas

| Carpeta | Rol |
|---------|-----|
| `Desktop\SOFT` | **Datos reales** de operación (clientes, volumen, tipos doc) |
| `Desktop\facturacion` | Documentación DIAN + código habilitación |
| `Desktop\expertak` | Aplicación |

---

*Generado a partir del análisis de los tres archivos .xlsx en SOFT (2025).*
