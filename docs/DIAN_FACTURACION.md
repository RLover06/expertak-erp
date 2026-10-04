# Facturación electrónica DIAN — Inventario y plan Expertak

Este documento resume los materiales que ya tienes, el repositorio de referencia aprobado en habilitación, y cómo integrarlos con **Expertak + Supabase** sin reinventar el proceso.

---

## 1. Materiales — carpeta única

**Toda la documentación oficial, la caja de herramientas DIAN y el código de referencia están aquí:**

```text
C:\path\to\facturacion
```

Índice detallado: [`REFERENCIA_FACTURACION.md`](REFERENCIA_FACTURACION.md)

### Documentación oficial DIAN

| Archivo | Uso |
|---------|-----|
| `Anexo-Tecnico-Factura-Electronica-de-Venta-vr-1-9.pdf` | Estructura UBL 2.1, campos obligatorios, reglas de validación |
| `Guia-Herramienta-para-el-Consumo-de-Web-Services.pdf` | Endpoints SOAP, flujo envío/validación |
| `Caja-de-herramientas-FE-V19-V2026.zip` | XSD, ejemplos XML, sets de prueba habilitación |
| `Nuevo-Diseno-Sistema-de-Facturacion-Electronica.pdf` | Arquitectura general del sistema DIAN |
| `Numeracion2022-Habilitacion-F.pdf` | Proceso de habilitación de numeración |
| `Numeracion2022-Inhabilitacion-F.pdf` | Inhabilitación |
| `Numeracion2022-PreguntasFrecuentes-F.pdf` | FAQ numeración |
| `Solicitud-autorizacion-de-numeracion-facturacion.pdf` | Trámite resolución |
| `Resolución 000202 de 31-03-2025.pdf` | Normativa reciente |
| `Preguntas-y-respuestas-Proveedores-Tecnologicos-FE.pdf` | Rol PT vs software propio |
| `Presentacion-Recepcion-de-Facturas-Electronicas.pdf` | Recepción / eventos |

### Material operativo

| Archivo | Uso |
|---------|-----|
| `Para probar en desarrollo.docx` | Credenciales/URLs ambiente habilitación (revisar con quien aprobó pruebas) |
| `Listado-Correos-de-recepcion-documentos-e-instrumentos-electronicos.zip` | Correos recepción FE |

### Repositorio de referencia (ya descargado)

| Ruta | Origen |
|------|--------|
| `facturacion-electronica-colombia-main\facturacion-electronica-colombia-main\` | [Crispancho93/facturacion-electronica-colombia](https://github.com/Crispancho93/facturacion-electronica-colombia) |

**Stack del repo:** Python + FastAPI (igual que Expertak), `lxml`, firma XAdES, SOAP a DIAN, ambiente de **habilitación** documentado en README.

---

## 2. Qué hace el repositorio de referencia (no empezar de cero)

```
facturacion-electronica-colombia/
├── domain/xml_models/     # UBL factura + nota crédito
├── application/use_cases/
│   ├── invoice/           # create_invoice_case, create_note_case
│   ├── sign_docs/         # XmlSignerV3, plantillas XAdES
│   └── soap/              # soap_invoice (producción/habilitación envío)
│                          # soap_test (Set de pruebas / TestID)
├── shared/                # certificado .pfx, plantillas SOAP/XML
└── interfaces/api/        # POST /api/invoice/create_invoice, send_test
```

### Flujo ya implementado

1. Recibe `InvoiceDto` (JSON).
2. Arma XML UBL según anexo técnico.
3. Calcula **CUFE** (clave técnica + datos factura).
4. Firma XML (`XmlSignerV3`).
5. Comprime ZIP.
6. Envía por **SOAP** firmado (WS-Security).
7. **Habilitación:** `send_test()` → `SoapRequestTest` con `TestID` del set DIAN.
8. **Envío normal:** `send()` → `SoapRequest`.

### Configuración que usa (.env)

- `PATH_BASE` — carpeta con certificados y XML de resolución
- `SIGN_NAME` — archivo `.pfx`
- `SIGN_PASSWORD` — contraseña del certificado
- `POLITICA_NAME` — política de firma (opcional según versión)

Certificados en: `{PATH_BASE}/certificados/`

---

## 3. Proceso DIAN que debes superar (habilitación)

Resumen alineado con tus PDFs y el repo:

| Etapa | Qué valida DIAN | En el repo |
|-------|-----------------|------------|
| 1. Registro software propio | Datos del facturador | Fuera del código (portal DIAN) |
| 2. Certificado digital | Firma válida | `shared/certificate.py` |
| 3. Resolución / numeración | Prefijo, rango, vigencia | `InvoiceDto.Control` |
| 4. Sets de prueba | XML por escenario | `POST /api/invoice/send_test` |
| 5. Envío facturas prueba | Respuesta válida / CUFE | `CreateInvoiceCase.send_test()` |
| 6. Aprobación habilitación | Paso a producción | Portal DIAN |

Los **TestID** de la caja de herramientas v1.9 deben coincidir con cada escenario (IVA, exportación, contingencia, etc.).

---

## 4. Cómo encaja con Expertak (arquitectura propuesta)

```text
┌─────────────────────────────────────────────────────────────┐
│  Frontend Svelte (formulario factura simple)                │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│  Expertak FastAPI                                             │
│  ├── /api/v1/facturas          (CRUD borrador)               │
│  ├── /api/v1/facturas/{id}/emitir  → módulo DIAN            │
│  └── /api/v1/consolidado       (contabilidad al aprobar)     │
└───────────────┬─────────────────────────────┬─────────────────┘
                │                             │
     ┌──────────▼──────────┐       ┌──────────▼──────────┐
     │  Módulo DIAN        │       │  Supabase           │
     │  (basado en repo    │       │  facturas_emitidas  │
     │   de referencia)    │       │  fe_respuestas      │
     └──────────┬──────────┘       │  plantillas_contab  │
                │                  └─────────────────────┘
     ┌──────────▼──────────┐
     │  Web Services DIAN  │
     │  (habilitación /    │
     │   producción)       │
     └─────────────────────┘
```

### Tablas Supabase sugeridas (fase FE)

- `fe_config` — NIT, ambiente, rutas, IDs habilitación
- `fe_resoluciones` — prefijo, desde, hasta, vigencia, clave técnica
- `facturas_emitidas` — estado, CUFE, XML/ZIP path, respuesta DIAN
- `factura_lineas` — detalle
- `fe_log_envios` — auditoría SOAP

Al estado **APROBADO** → disparar movimientos en `consolidado_movimientos` (plantilla contable).

---

## 5. Estrategias de integración del código de referencia

| Opción | Pros | Contras |
|--------|------|---------|
| **A. Microservicio** | Expertak llama API del repo en `:8001` | Dos servicios, GPL aislado |
| **B. Módulo `backend/app/dian/`** | Un solo deploy | Repo es **GPLv2** — si distribuyes Expertak, debes cumplir GPL |
| **C. Reimplementar inspirado** | Licencia propia | Más tiempo, riesgo de errores en firma/SOAP |

**Recomendación práctica:** empezar con **A (microservicio)** para pasar habilitación rápido; luego migrar piezas estables a Expertak si defines licencia.

---

## 6. Licencia del repositorio de referencia

El proyecto de Crispancho93 está bajo **GPLv2**. Si copias código dentro de Expertak y distribuyes el producto, las obligaciones GPL aplican. Para uso interno privado el impacto es menor, pero conviene definirlo con asesoría legal antes de comercializar.

---

## 7. Qué necesitamos de ti para el siguiente paso de código

1. Contenido de `Para probar en desarrollo.docx` (URLs habilitación, NIT prueba — **sin contraseñas en chat**).
2. Confirmar si ya tienes **Set de pruebas aprobado** o cuáles faltan.
3. Certificado `.pfx` en ruta segura (solo en servidor, no en Git).
4. Resolución de numeración (prefijo, rango, `TechnicalKey`).
5. Decisión: **microservicio** vs **módulo integrado** en Expertak.

---

## 8. Plan de trabajo sugerido

| Fase | Entregable | Duración orientativa |
|------|------------|----------------------|
| **0** | Validar repo referencia en habilitación (mismo .env que quien aprobó) | 1–2 días |
| **1** | Tablas Supabase `fe_*` + config | 2–3 días |
| **2** | API Expertak: borrador factura + emitir (delegando a módulo DIAN) | 1 semana |
| **3** | Sets de prueba DIAN (`send_test`) hasta aprobación | según DIAN |
| **4** | Contabilización automática en consolidado | 2–3 días |
| **5** | Producción + sincronización `documentos_dian` | 1 semana |

---

## 9. Referencias rápidas

- Repo: https://github.com/Crispancho93/facturacion-electronica-colombia
- Video README del autor: enlace en README del repo
- Anexo técnico local: `Anexo-Tecnico-Factura-Electronica-de-Venta-vr-1-9.pdf`
- Expertak Supabase: `SUPABASE.md`

---

*Documento generado a partir del inventario en Desktop/facturacion y análisis del repositorio facturacion-electronica-colombia.*
