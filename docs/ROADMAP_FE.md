# Hoja de ruta — Facturación electrónica Expertak

Orden lógico de ejecución para implementar emisión DIAN, habilitación, producción y contabilidad, reutilizando el motor de referencia y los datos reales en `Desktop\SOFT` y `Desktop\facturacion`.

**Estado actual (base ya hecha):** importación DIAN, consolidado/resumen, Supabase preparado, API `/api/v1/fe/emitir`, documentación en `docs/`.

---

## Fase 0 — Preparación y decisiones (no saltar)

### 0.1 Definir alcance del MVP y modelo de negocio

**Objetivo:** Acotar qué se entrega en la primera versión funcional sin dispersar esfuerzo en 32 empresas o todos los tipos de documento DIAN.

**Revisar / desarrollar:**
- Confirmar si Expertak es **multi-empresa contable** (32 clientes en SOFT) o piloto con 1–3 emisores.
- Lista de empresas que **solo importan/reportan** vs las que **emitirán** FE.
- Documentos MVP: factura venta (+ nota crédito en fase 2).
- Decisión legal de integración del repo GPLv2 (microservicio vs módulo embebido).

**Riesgos / errores comunes:**
- Intentar habilitar y producción para todas las empresas a la vez.
- Mezclar recepción (compras) con emisión (ventas) en el mismo flujo sin separar `Grupo` Emitido/Recibido.

**Dependencias:** Ninguna técnica; bloquea priorización de fases 4–8.

**Prompt recomendado:**
```text
Contexto: Expertak es [multi-empresa contable / ERP de un solo NIT]. 
Datos reales en SOFT (32 empresas, 32k documentos DIAN 2025).
Objetivo MVP: [solo emisión factura venta / emisión + nota crédito / solo habilitación].

Dame:
1) Alcance MVP en 5 bullets medibles.
2) Lista de empresas piloto (máx. 3) con justificación.
3) Qué queda explícitamente fuera del MVP.
```

---

### 0.2 Inventariar credenciales y habilitación DIAN por empresa emisora

**Objetivo:** Tener por cada emisor los insumos obligatorios antes de programar.

**Revisar / desarrollar:**
- Checklist por empresa: NIT, razón social, resolución (prefijo, desde, hasta, vigencia), **clave técnica**, Software ID, Pin, certificado `.pfx`.
- Estado en portal DIAN: habilitación en curso / aprobada / producción.
- Sets de prueba aprobados y pendientes (caja herramientas V19).
- Archivo local: `Desktop\facturacion\Para probar en desarrollo.docx` (sin pegar secretos en Git).

**Riesgos / errores comunes:**
- Usar resolución vencida o consecutivo fuera de rango.
- Certificado de persona equivocada o expirado.
- `ProfileExecutionID` incorrecto (2=habilitación, 1=producción).

**Dependencias:** Fase 0.1 (empresas piloto).

**Prompt recomendado:**
```text
Empresa piloto: [razón social], NIT [xxx].
Tengo: resolución [sí/no], certificado .pfx [sí/no], habilitación DIAN [estado].
Según Anexo Técnico 1.9 y Numeracion2022-Habilitacion-F.pdf, 
lista los campos ControlDto que debo completar y qué validar en portal DIAN antes del primer envío.
No incluyas contraseñas; usa placeholders.
```

---

## Fase 1 — Infraestructura y entornos

### 1.1 Supabase operativo para Expertak

**Objetivo:** Persistir documentos, emisiones y configuración; dejar de depender solo de memoria.

**Revisar / desarrollar:**
- Proyecto Supabase creado; `DATABASE_URL` en `backend/.env`.
- Ejecutar `sql/supabase_schema.sql` + `sql/supabase_fe_schema.sql`.
- `python scripts/init_supabase_tables.py` y verificar `/api/v1/health` → `mode: supabase`.
- Política: `.env` y `.pfx` fuera de Git.

**Riesgos / errores comunes:**
- URL pooler incorrecta (usar Session mode 5432 para SQLAlchemy).
- Olvidar `sslmode` en conexión Supabase.
- Commitear credenciales.

**Dependencias:** Ninguna para desarrollo local; bloquea persistencia de emisiones (fase 4).

**Prompt recomendado:**
```text
Proyecto Expertak FastAPI + Supabase. 
DATABASE_URL ya configurada en backend/.env.
Verifica que init_database cree: documentos_dian, consolidado_movimientos, resumen_filas, fe_emisiones.
Indica comandos y cómo validar en Table Editor de Supabase.
```

---

### 1.2 Motor DIAN de referencia funcionando en local

**Objetivo:** Validar generación XML, firma y SOAP **antes** de depender de Expertak.

**Revisar / desarrollar:**
- Ruta: `Desktop\facturacion\...\facturacion-electronica-colombia-main`.
- `.env`: `PATH_BASE`, `SIGN_NAME`, `SIGN_PASSWORD`, estructura de carpetas del autor.
- `uvicorn app:app --port 8001` → `/docs`.
- Prueba directa: `POST /api/invoice/send_test` con payload válido del repo o Swagger.

**Riesgos / errores comunes:**
- `PATH_BASE` sin XML de resolución/autorización que espera el motor.
- Java/JAR si alguna ruta de firma lo requiere (revisar `xml_signer_jar.py`).
- Firewall bloqueando `vpfe-hab.dian.gov.co`.

**Dependencias:** 0.2 (certificado y control).

**Prompt recomendado:**
```text
Motor: facturacion-electronica-colombia en puerto 8001.
Error al enviar: [pegar mensaje DIAN o traceback sin secretos].
Archivos: soap_invoice.py, create_invoice_case.py.
Diagnostica: certificado, TestID, consecutivo, o error SOAP; propón fix concreto.
```

---

### 1.3 Expertak conectado al motor DIAN

**Objetivo:** Confirmar cadena Expertak → motor → DIAN.

**Revisar / desarrollar:**
- `backend/.env`: `DIAN_REFERENCE_APP`, `DIAN_SERVICE_URL`, `DIAN_ENGINE=auto`.
- Expertak `:8000` → `GET /api/v1/fe/dian-status` → `ready: true`.
- `POST /api/v1/fe/emitir` modo `habilitacion` con `docs/fe_invoice_ejemplo.json` completado.
- Revisar `GET /api/v1/fe/emisiones` para auditoría.

**Riesgos / errores comunes:**
- Solo levantar Expertak sin el servicio 8001 (auto falla si no hay inline configurado).
- Payload JSON incompleto vs `InvoiceDto` (campos anexo técnico).

**Dependencias:** 1.1 (opcional), 1.2 (obligatorio).

**Prompt recomendado:**
```text
Expertak /api/v1/fe/emitir devuelve 502: [detalle JSON].
DIAN_SERVICE_URL=http://localhost:8001, dian-status: [pegar].
Revisa backend/app/dian/emitter.py y alinea el payload con domain/dtos/invoice_dto.py del motor.
```

---

## Fase 2 — Habilitación DIAN (software propio)

### 2.1 Completar sets de prueba (caja de herramientas V19)

**Objetivo:** Aprobar todos los escenarios exigidos por DIAN en ambiente de habilitación.

**Revisar / desarrollar:**
- Descomprimir `Caja-de-herramientas-FE-V19-V2026.zip`.
- Por cada set: XML ejemplo, `TestID`, reglas específicas (IVA, exportación, contingencia, etc.).
- Enviar vía `modo: habilitacion` / `send_test` con `Control.TestID` correcto.
- Registrar en hoja: set ID, fecha, resultado, mensaje DIAN.

**Riesgos / errores comunes:**
- Enviar factura estándar cuando el set exige otro tipo de operación.
- Reutilizar el mismo consecutivo entre intentos.
- Ignorar `Application response` en datos importados vs emisión propia.

**Dependencias:** 1.2, 1.3, 0.2.

**Prompt recomendado:**
```text
Set DIAN TestID: [xxx]. Descripción del escenario: [copiar de caja herramientas].
Payload actual: [JSON resumido].
Respuesta DIAN: [XML/texto error].
Qué campos del InvoiceDto/UBL debo ajustar según Anexo Técnico 1.9 para este set?
```

---

### 2.2 Corregir rechazos normativos iterativamente

**Objetivo:** Llegar a respuestas válidas de DIAN para todos los sets pendientes.

**Revisar / desarrollar:**
- Parser de respuesta (`extract_errors_invoice` en motor).
- Ajustes en: tributos, `IndustryClassificationCode`, medios de pago, identificación adquiriente, CUFE.
- Documentar cada fix en `docs/DIAN_FACTURACION.md` o changelog interno.

**Riesgos / errores comunes:**
- Parchear solo el mensaje visible sin revisar XSD de la caja de herramientas.
- Cambiar anexo/campos sin versionar qué versión DIAN aplica (v1.9).

**Dependencias:** 2.1.

**Prompt recomendado:**
```text
DIAN rechazó con: [código/mensaje]. 
Fragmento XML enviado (sin firma): [pegar sección relevante].
Compara con XSD/ejemplo del set en caja herramientas V19 y lista cambios mínimos en el JSON InvoiceDto.
```

---

### 2.3 Cierre de habilitación en portal DIAN

**Objetivo:** Obtener aprobación formal del software en ambiente de habilitación.

**Revisar / desarrollar:**
- Portal DIAN: confirmación de sets completos.
- Resolución 165/2023 y Numeracion2022 según procedimiento vigente.
- Congelar versión del motor (commit/tag) que pasó pruebas.

**Riesgos / errores comunes:**
- Pasar a producción sin cierre formal en portal.
- Modificar código de firma/SOAP después de aprobar sin re-habilitar.

**Dependencias:** 2.1, 2.2.

**Prompt recomendado:**
```text
Lista de sets DIAN completados: [tabla]. 
¿Qué pasos manuales faltan en portal DIAN según Numeracion2022-Habilitacion-F.pdf 
para declarar software propio habilitado? Checklist accionable.
```

---

## Fase 3 — Producto Expertak: emisión estructurada

### 3.1 Modelo de datos FE en Supabase

**Objetivo:** Guardar borradores, emisiones, respuestas DIAN y configuración por empresa.

**Revisar / desarrollar:**
- Tablas: `fe_empresas_config`, `fe_resoluciones`, `facturas_emitidas`, `factura_lineas`, `fe_emisiones` (ampliar JSONB + CUFE).
- SQLAlchemy models + repositorio; migrar log en memoria de `fe_facturas.py`.
- Estados: `borrador` → `enviada` → `aprobada` / `rechazada`.

**Riesgos / errores comunes:**
- Duplicar `documentos_dian` sin vínculo a factura emitida propia.
- No guardar respuesta XML cruda para auditoría.

**Dependencias:** 1.1.

**Prompt recomendado:**
```text
Diseña schema PostgreSQL/Supabase para facturación multi-empresa: 
config por NIT, resolución, factura borrador, líneas, emisión DIAN con CUFE y respuesta XML.
Integra con tablas existentes documentos_dian y consolidado_movimientos. SQL + modelos SQLAlchemy.
```

---

### 3.2 API Expertak: borrador → emitir → consultar

**Objetivo:** Flujo REST claro sin exigir JSON DIAN crudo al usuario final.

**Revisar / desarrollar:**
- `POST /api/v1/fe/facturas` — crear borrador (cliente, líneas, totales calculados).
- `POST /api/v1/fe/facturas/{id}/emitir?modo=habilitacion|produccion` — mapeo a `InvoiceDto`.
- `GET /api/v1/fe/facturas/{id}` — estado, CUFE, enlace QR.
- Servicio `mapper.py`: borrador simple → `InvoiceDto` usando config empresa.

**Riesgos / errores comunes:**
- Calcular IVA en frontend y en backend con redondeos distintos.
- No validar consecutivo contra resolución antes de enviar.

**Dependencias:** 1.3, 3.1, 0.2.

**Prompt recomendado:**
```text
En Expertak FastAPI, implementa mapper de FacturaBorrador (Pydantic simple) a InvoiceDto del motor DIAN.
Incluye cálculo IVA 19%, validación consecutivo en rango de resolución, y tests con payload de fe_invoice_ejemplo.json.
```

---

### 3.3 UI Svelte: factura simple

**Objetivo:** Pantalla usable para crear y emitir sin Postman.

**Revisar / desarrollar:**
- Formulario: empresa activa, cliente, líneas, totales.
- Botones: Guardar borrador, Enviar a DIAN (habilitación/producción).
- Mostrar resultado DIAN y CUFE.
- Integrar en Panel o nueva pestaña “Facturación”.

**Riesgos / errores comunes:**
- No seleccionar empresa en contexto multi-tenant.
- UX que permite producción sin confirmación explícita.

**Dependencias:** 3.2.

**Prompt recomendado:**
```text
Componente Svelte FacturaForm.svelte: empresa selector, cliente, tabla líneas, IVA, 
llama POST /api/v1/fe/facturas y /emitir. Estilo coherente con ConsolidadoUpload.svelte en Expertak.
```

---

## Fase 4 — Multi-empresa y datos reales (SOFT)

### 4.1 Catálogo de empresas desde datos SOFT

**Objetivo:** Alinear sistema con las 32 empresas reales y NIT en `Identificacion`.

**Revisar / desarrollar:**
- Import inicial desde `01pro.xlsx` columnas `Empresa` + `Identificacion`.
- Tabla `empresas` / `fe_empresas_config` poblada.
- Filtros en UI por empresa (como informes actuales).

**Riesgos / errores comunes:**
- Duplicar empresas por variaciones de razón social.
- Mezclar NIT emisor del documento con NIT “cliente contable”.

**Dependencias:** 1.1, 3.1.

**Prompt recomendado:**
```text
Script Python: leer Desktop/SOFT/01pro.xlsx, extraer pares únicos Empresa+Identificacion (NIT),
insertar en Supabase empresas. Normalizar nombres. Manejar 32472 filas por lotes.
```

---

### 4.2 Sincronizar emisiones propias con `documentos_dian`

**Objetivo:** Una sola vista de documentos emitidos (importados DIAN + generados en Expertak).

**Revisar / desarrollar:**
- Tras emisión aprobada: insertar fila en `documentos_dian` con CUFE, totales, `Grupo=Emitido`.
- Evitar duplicado por `cufe_cude` unique.
- Informe/resumen incluye facturas propias.

**Riesgos / errores comunes:**
- Doble registro si también importan el mismo CUFE desde Excel DIAN.

**Dependencias:** 3.2, import existente.

**Prompt recomendado:**
```text
Tras emisión DIAN exitosa en Expertak, persiste en documentos_dian y resumen_filas 
con mismos campos que import Excel. Función en supabase_store evitando duplicado CUFE.
```

---

## Fase 5 — Producción

### 5.1 Cambio controlado a ambiente producción

**Objetivo:** Emitir facturas legales con validez fiscal.

**Revisar / desarrollar:**
- `ProfileExecutionID=1`, URL producción en `soap_invoice.py` (verificar si motor usa hab vs prod por config).
- Resolución de producción y consecutivos reales.
- Prueba de una factura real de bajo riesgo.

**Riesgos / errores comunes:**
- Enviar a producción con certificado de prueba.
- Saltar habilitación incompleta.

**Dependencias:** 2.3, 3.2.

**Prompt recomendado:**
```text
Motor DIAN reference: ¿cómo conmutar habilitación vs producción (URL SOAP, ProfileExecutionID)?
Propón variables de entorno FE_AMBIENTE=hab|prod y cambios mínimos en Expertak + motor.
```

---

### 5.2 Operación continua (consecutivos, contingencia)

**Objetivo:** Operación diaria sin romper numeración ni DIAN.

**Revisar / desarrollar:**
- Incremento atómico de consecutivo por prefijo en BD.
- Alertas: resolución por vencer, certificado por vencer.
- Plan contingencia (Anexo / tipos contingencia) — fase posterior si aplica.

**Riesgos / errores comunes:**
- Dos usuarios obtienen el mismo folio.
- No inhabilitar resolución agotada.

**Dependencias:** 5.1, 3.1.

**Prompt recomendado:**
```text
Implementa fe_consecutivos con lock transaccional en PostgreSQL/Supabase: 
prefijo, último usado, rango resolución. API get_next_folio(empresa_id, prefijo).
```

---

## Fase 6 — Contabilidad automática

### 6.1 Plantillas contables por tipo de documento

**Objetivo:** Al aprobar factura emitida, generar movimientos consolidado automáticamente.

**Revisar / desarrollar:**
- Tabla `fe_plantillas_contables` (cuenta débito/crédito por concepto: cliente, ingreso, IVA).
- Hook post-aprobación → `consolidado_movimientos`.
- Validar cuadre débito = crédito.

**Riesgos / errores comunes:**
- Plantilla única para todas las empresas con PUC distinto.
- Contabilizar antes de aprobación DIAN.

**Dependencias:** 3.2, consolidado existente; Excel PUC si existe fuera de SOFT.

**Prompt recomendado:**
```text
Al cambiar factura_emitida a estado aprobada, genera 3 líneas consolidado_movimientos 
(130505 cliente, 4135 ingreso, 2408 IVA) usando plantilla por empresa_id. 
Código en supabase_store + test cuadre.
```

---

### 6.2 Reportes unificados FE + contabilidad

**Objetivo:** Informes coherentes con `consolidado_20251` y operación real.

**Revisar / desarrollar:**
- Cruzar `documentos_dian` emitido con movimientos por `documento_origen`.
- Informe “facturado vs contabilizado”.

**Riesgos / errores comunes:**
- Totales Excel pivot vs BD por redondeo.

**Dependencias:** 6.1, 4.2.

**Prompt recomendado:**
```text
Endpoint GET /api/v1/informes/fe-contabilidad?empresa=&periodo= 
cruza documentos_dian Grupo=Emitido con consolidado por documento_origen. 
Respuesta tipo InformeReporte existente.
```

---

## Fase 7 — Ampliaciones (post-MVP)

### 7.1 Nota crédito electrónica

**Objetivo:** Referenciar factura y cumplir anexo para notas.

**Revisar / desarrollar:** `CreateNoteCase`, `CreditNoteDto`, UI y API en Expertak.  
**Dependencias:** 5.1, 3.2.  
**Prompt:** `Implementa POST /api/v1/fe/notas-credito delegando a create_credit_note del motor DIAN.`

---

### 7.2 Panel compras (documentos recibidos)

**Objetivo:** Activar flujos del panel compras con datos Recibido.

**Revisar / desarrollar:** Wire `PanelCompras.svelte` a API; eventos RADIAN si aplica.  
**Dependencias:** 4.1.  
**Prompt:** `Conecta PanelCompras.svelte a GET documentos filtrados Grupo=Recibido por empresa activa.`

---

### 7.3 Nómina y documentos equivalentes

**Objetivo:** Solo si el negocio lo exige (801 nóminas en 01pro).

**Dependencias:** MVP estable.  
**Prompt:** `Evalúa esfuerzo nómina electrónica vs factura venta según volumen en SOFT/01pro.xlsx.`

---

## Fase 8 — Calidad, despliegue y mantenimiento

### 8.1 Pruebas automatizadas y CI

**Objetivo:** Evitar regresiones en import y emisión.

**Revisar / desarrollar:** pytest con mocks SOAP; fixture `subir prueba.xlsx`; no llamar DIAN real en CI.  
**Dependencias:** 3.2.  
**Prompt:** `pytest para build_insert_payload y mapper FE con datos de docs/fe_invoice_ejemplo.json.`

---

### 8.2 Despliegue (Expertak + secretos)

**Objetivo:** Producción segura.

**Revisar / desarrollar:** Hosting backend/frontend; Supabase prod; certificado en HSM o vault; motor DIAN en mismo VPC o microservicio.  
**Dependencias:** 5.1.  
**Prompt:** `Docker compose Expertak + variables DIAN sin .pfx en imagen; montar volumen certificados.`

---

### 8.3 Monitoreo y soporte

**Objetivo:** Detectar fallos de DIAN y certificados.

**Revisar / desarrollar:** Log `fe_emisiones`; alertas certificado 30 días; dashboard estado DIAN.  
**Dependencias:** 3.1, 5.1.

---

## Resumen visual de dependencias

```text
0.1 Alcance → 0.2 Credenciales
                ↓
1.2 Motor DIAN → 1.3 Expertak+DIAN → 2.x Habilitación
                ↓
1.1 Supabase → 3.1 Datos FE → 3.2 API → 3.3 UI
                ↓
4.x Multi-empresa (SOFT) → 5.x Producción → 6.x Contabilidad
                ↓
7.x Ampliaciones    8.x Calidad/Deploy
```

---

## Orden recomendado “esta semana” (si hay un solo desarrollador)

1. 0.1 → 0.2  
2. 1.2 → 1.3  
3. 2.1 → 2.2 (iterar hasta sets OK)  
4. 1.1 + 3.1  
5. 3.2 → 3.3  
6. 2.3 → 5.1  
7. 6.1 → 4.2  

---

*Documento vivo: actualizar al cerrar cada fase. Referencias: `DIAN_FACTURACION.md`, `SOFT_NEGOCIO.md`, `EMISION_FE.md`, `SUPABASE.md`.*
