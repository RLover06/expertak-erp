# Checklist previo a habilitación DIAN — Expertak

Guía de verificación para completar **antes de volver a Cursor**. Todo lo de aquí es trámite externo o infraestructura: no requiere tocar código.

Cuando todos los ítems bloqueantes estén en **OK**, el endpoint `GET /api/v1/fe/dian-status` debe responder `ready: true` y podremos retomar el desarrollo (sets V19, QR, PDF de representación gráfica, INC/ICA/retenciones).

> **Cambio importante de alcance (set de pruebas):** el set de habilitación exige **exactamente 4 documentos** — 2 facturas electrónicas + 1 nota débito + 1 nota crédito. Por eso **Nota Crédito y Nota Débito dejan de ser post-MVP**: son requisito obligatorio para pasar habilitación y su implementación (ya diseñada en `ubl_credit_note.py` y `ubl_debit_note.py` del motor) debe **adelantarse antes** de completar el set, no después. Ver Fase 5.

## Convenciones

- **Responsable:**
  - `Yo` → gestión personal / trámites ante DIAN / datos de la empresa.
  - `Infra` → servidor, certificados en disco, levantar servicios, variables de entorno.
  - `DIAN` → acciones que dependen del portal o de la aprobación de la entidad (tiempos externos).
- **Estado inicial:** todos en `Pendiente`. Marque `OK` al completar, o `Bloqueado` si depende de un tercero.

---

## Fase 1 — Registro como facturador (portal DIAN)

> **Ruta oficial confirmada (ABECÉ del facturador).** El registro y el modo de operación se hacen desde el portal principal de la DIAN, **no** entrando directo a `catalogo-vpfe-hab.dian.gov.co` (ese es un paso posterior). El flujo tiene dos sesiones separadas con un **cierre de sesión obligatorio** entre medias.

**Paso a paso:**

1. Entrar a `www.dian.gov.co` → sección **"Factura Electrónica"** → opción **"Habilitación"**.
2. Llega un **correo con un token de acceso** a la dirección registrada en el **RUT**. El token es **válido por tiempo limitado (~60 minutos)** → hay que actuar rápido.
3. Dentro del sistema: **"Registro y habilitación"** → **"Documentos Electrónicos"** → **"Factura Electrónica"** → registrar al facturador.
4. **Cerrar sesión obligatoriamente** después de registrarse. No se puede configurar el modo de operación en la misma sesión.
5. Volver a entrar y elegir el **modo de operación: "Software propio"**. Al hacerlo, la DIAN **genera automáticamente el Software ID y el PIN**.
6. El estado pasa de **"En proceso"** a **"Habilitado"** únicamente cuando se **completan y aprueban los 4 documentos del set de pruebas** (ver Fase 5).

| # | Ítem | Responsable | Estado |
|---|------|-------------|--------|
| 1.1 | Confirmar que el **RUT del emisor** tenga activa la responsabilidad de facturación electrónica y el **correo del RUT** esté vigente y accesible | Yo | Pendiente |
| 1.2 | Entrar a `www.dian.gov.co` → **"Factura Electrónica"** → **"Habilitación"** (no entrar directo al catálogo) | Yo | Pendiente |
| 1.3 | Recibir el **token de acceso** en el correo del RUT y usarlo **dentro de los ~60 min** de validez | Yo / DIAN | Pendiente |
| 1.4 | Registrar al facturador: **"Registro y habilitación" → "Documentos Electrónicos" → "Factura Electrónica"** | Yo | Pendiente |
| 1.5 | **Cerrar sesión** obligatoriamente tras el registro | Yo | Pendiente |
| 1.6 | Volver a ingresar y elegir **modo de operación = "Software propio"** | Yo | Pendiente |
| 1.7 | Anotar el **Software ID** generado automáticamente por DIAN | Yo | Pendiente |
| 1.8 | Anotar el **PIN del software** generado automáticamente por DIAN | Yo | Pendiente |
| 1.9 | Confirmar el **NIT del emisor** y su **dígito de verificación (DV)** | Yo | Pendiente |
| 1.10 | (Seguimiento) Verificar que el estado quede en **"En proceso"** hasta aprobar el set de pruebas (Fase 5) | Yo / DIAN | Pendiente |

---

## Fase 2 — Certificado digital

> **Aclaración (desarrollo propio):** el certificado que usaremos es **de pago**, adquirido con una entidad **acreditada por ONAC** (Certicámara, GSE, ANDES SCD, etc.). El **certificado gratuito de la DIAN NO aplica a nuestro caso**: es exclusivo para quienes usan la **"Solución Gratuita DIAN"**, y nosotros hacemos **desarrollo propio (software propio)**. No se considera como opción.

| # | Ítem | Responsable | Estado |
|---|------|-------------|--------|
| 2.1 | Adquirir / renovar el **certificado digital `.pfx` de pago** con entidad acreditada ONAC (Certicámara, GSE, ANDES SCD, etc.) | Yo | Pendiente |
| 2.2 | Verificar que el certificado esté **vigente** (no vencido) y a nombre del emisor correcto | Yo | Pendiente |
| 2.3 | Resguardar la **contraseña del `.pfx`** en lugar seguro (gestor de secretos, NO en chat ni en Git) | Yo | Pendiente |
| 2.4 | Copiar el `.pfx` al servidor en `…\facturacion\fe_data\certificados\` (ruta privada, fuera del repositorio) | Infra | Pendiente |
| 2.5 | (Opcional según versión) Colocar el archivo de **política de firma** en la misma carpeta `certificados/` | Infra | Pendiente |

---

## Fase 3 — Resolución de numeración (factura electrónica)

> Numeración **normal** para emitir factura electrónica en operación habitual. Es **distinta** de la numeración de contingencia (Fase 4).

| # | Ítem | Responsable | Estado |
|---|------|-------------|--------|
| 3.1 | Solicitar / confirmar la **resolución de numeración de facturación electrónica** ante DIAN | Yo / DIAN | Pendiente |
| 3.2 | Anotar el **número de resolución** (`InvoiceAuthorization`) | Yo | Pendiente |
| 3.3 | Anotar **prefijo**, **rango desde–hasta** (`Prefix`, `From`, `To`) | Yo | Pendiente |
| 3.4 | Anotar **fechas de vigencia** inicio y fin (`StartDate`, `EndDate`) | Yo | Pendiente |
| 3.5 | Anotar la **clave técnica** de la resolución (`TechnicalKey`) | Yo | Pendiente |

---

## Fase 4 — Numeración de contingencia (talonario / papel, portal MUISCA)

> **Trámite nuevo y separado.** No es la numeración de factura electrónica (Fase 3). Es un rango de **factura de talonario o de papel** que se usa **exclusivamente** para emitir durante una **contingencia Tipo 03** (ver Suplemento C). **Hay que solicitarlo con anticipación**: no se puede improvisar cuando ya ocurrió la falla.

**Paso a paso (MUISCA):**

1. Iniciar sesión en `www.dian.gov.co` como **"Usuario registrado"**.
2. Ir a **"Numeración de Facturación"** → **"Solicitar Numeración de Facturación"** → **"Autorizar rango"**.
3. Elegir tipo de facturación **"Factura de talonario o de papel"** (NO "Factura Electrónica").
4. Definir **prefijo y rango** (ej. 1 a 500).
5. **Firmar el formulario 1302** → pasa de **Borrador** a **Definitivo**.
6. **Firmar una segunda vez** → se genera el **formulario 1876 (Autorización de Numeración de Facturación)**, el documento final con la **vigencia** y los **rangos autorizados**.

| # | Ítem | Responsable | Estado |
|---|------|-------------|--------|
| 4.1 | Iniciar sesión en MUISCA como **"Usuario registrado"** | Yo | Pendiente |
| 4.2 | **"Numeración de Facturación" → "Solicitar Numeración de Facturación" → "Autorizar rango"** | Yo | Pendiente |
| 4.3 | Elegir tipo **"Factura de talonario o de papel"** y definir **prefijo + rango** (ej. 1–500) | Yo | Pendiente |
| 4.4 | Firmar el **formulario 1302** (Borrador → Definitivo) | Yo | Pendiente |
| 4.5 | Firmar por **segunda vez** para generar el **formulario 1876** | Yo / DIAN | Pendiente |
| 4.6 | Anotar de la **1876**: prefijo, rango autorizado y **vigencia** (para usar en contingencia Tipo 03) | Yo | Pendiente |

---

## Fase 5 — Set de habilitación (Caja V19) — **4 documentos obligatorios**

> El set de pruebas exige **exactamente 4 documentos**: **2 facturas electrónicas + 1 nota débito + 1 nota crédito**. Esto adelanta el alcance: **Nota Crédito y Nota Débito ya no son post-MVP**, son **requisito para pasar habilitación**. Su implementación (diseño en `ubl_credit_note.py` y `ubl_debit_note.py` del motor) debe **completarse y aprobarse antes** de cerrar el set de pruebas.

| # | Ítem | Responsable | Estado |
|---|------|-------------|--------|
| 5.1 | Identificar en el portal el **set de pruebas asignado** (Caja de herramientas FE V19 / V2026) | Yo / DIAN | Pendiente |
| 5.2 | Anotar el/los **TestID** del set/escenario a enviar (`TestID`) | Yo | Pendiente |
| 5.3 | Confirmar la composición exacta del set: **2 facturas + 1 nota débito + 1 nota crédito** | Yo | Pendiente |
| 5.4 | Adelantar la implementación de **Nota Crédito** (`ubl_credit_note.py`) — *se desarrolla en Cursor* | Yo / Infra | Pendiente |
| 5.5 | Adelantar la implementación de **Nota Débito** (`ubl_debit_note.py`) — *se desarrolla en Cursor* | Yo / Infra | Pendiente |
| 5.6 | Emitir y **aprobar los 4 documentos** del set para que el estado pase a **"Habilitado"** (ver Fase 1.10) | Yo / DIAN | Pendiente |

> Nota: la implementación y aprobación de cada escenario se hace en la fase de desarrollo en Cursor. Para **arrancar** esa fase solo se necesita **tener el set asignado y el/los TestID**; para **cerrar** habilitación se necesitan los 4 documentos aprobados.

---

## Fase 6 — Motor de referencia DIAN (`:8001`)

| # | Ítem | Responsable | Estado |
|---|------|-------------|--------|
| 6.1 | Confirmar que existe la carpeta del motor en `DIAN_REFERENCE_APP` con `app.py` | Infra | Pendiente |
| 6.2 | Crear entorno virtual e instalar dependencias (`python -m venv venv` → `pip install -r requirements.txt`) | Infra | Pendiente |
| 6.3 | Configurar el **`.env` del motor**: `PATH_BASE`, `SIGN_NAME` (nombre del `.pfx`), `SIGN_PASSWORD`, y `POLITICA_NAME` si aplica | Infra | Pendiente |
| 6.4 | Verificar que `PATH_BASE` apunte a `…\facturacion\fe_data` y contenga la subcarpeta `certificados/` | Infra | Pendiente |
| 6.5 | Levantar el motor: `uvicorn app:app --reload --port 8001` | Infra | Pendiente |
| 6.6 | Comprobar que responde la documentación interactiva: `http://localhost:8001/docs` | Infra | Pendiente |

---

## Fase 7 — Configuración de Expertak

| # | Ítem | Responsable | Estado |
|---|------|-------------|--------|
| 7.1 | En `backend/.env`: `DIAN_REFERENCE_APP` con la ruta del motor | Infra | Pendiente |
| 7.2 | En `backend/.env`: `DIAN_SERVICE_URL=http://localhost:8001` | Infra | Pendiente |
| 7.3 | En `backend/.env`: `DIAN_ENGINE=auto` (o `http` para forzar microservicio) | Infra | Pendiente |
| 7.4 | (Recomendado) Configurar `DATABASE_URL` de Supabase para persistir emisiones | Infra | Pendiente |
| 7.5 | Levantar Expertak: `uvicorn app.main:app --reload --port 8000` | Infra | Pendiente |

---

## Fase 8 — Datos del piloto (`docs/fe_piloto.json`)

Reemplazar todos los campos `REEMPLAZAR_*` con los datos reales obtenidos en las fases anteriores. **Sin secretos en Git** (la contraseña del `.pfx` solo va en el `.env` del motor).

| # | Ítem | Responsable | Estado |
|---|------|-------------|--------|
| 8.1 | `ProviderID` y `CompanyID` → NIT del emisor (Fase 1.9) | Yo | Pendiente |
| 8.2 | `VerificationDigit` → DV del NIT (Fase 1.9) | Yo | Pendiente |
| 8.3 | `SoftwareID` y `Pin` → datos del software propio (Fase 1.7 / 1.8) | Yo | Pendiente |
| 8.4 | `InvoiceAuthorization`, `Prefix`, `From`, `To`, `StartDate`, `EndDate`, `TechnicalKey` → resolución (Fase 3) | Yo | Pendiente |
| 8.5 | `TestID` → set de habilitación (Fase 5.2) | Yo | Pendiente |
| 8.6 | `ProfileExecutionID = "2"` (habilitación) durante todas las pruebas | Yo | Pendiente |
| 8.7 | `PartyName`, `Address.AddressLine` y demás datos del emisor | Yo | Pendiente |

---

## Fase 9 — Verificación final (preflight)

| # | Ítem | Responsable | Estado |
|---|------|-------------|--------|
| 9.1 | Ejecutar el preflight: `python backend/scripts/fe_preflight.py` | Infra | Pendiente |
| 9.2 | Consultar estado por API: `GET http://localhost:8000/api/v1/fe/dian-status` → `ready: true` | Infra | Pendiente |
| 9.3 | Confirmar que la lista de `blockers` esté **vacía** | Infra | Pendiente |
| 9.4 | (Opcional) Emisión de prueba: `python backend/scripts/emitir_prueba.py` y revisar respuesta DIAN | Yo / Infra | Pendiente |

---

## Resumen de bloqueantes mínimos para volver a Cursor

Para retomar el desarrollo basta con tener en **OK** lo siguiente:

- [ ] Registro como facturador completo, en **modo "Software propio"**, con Software ID + PIN generados (Fase 1).
- [ ] Certificado `.pfx` **de pago (ONAC)** vigente, copiado al servidor y con contraseña en el `.env` del motor (Fase 2).
- [ ] Resolución de numeración electrónica con clave técnica (Fase 3).
- [ ] TestID del set de habilitación asignado (Fase 5).
- [ ] Motor `:8001` levantado y respondiendo `/docs` (Fase 6).
- [ ] `backend/.env` apuntando al motor (Fase 7).
- [ ] `docs/fe_piloto.json` completo (Fase 8).
- [ ] `dian-status` → `ready: true` (Fase 9).

> **Numeración de contingencia (Fase 4):** no es bloqueante para *arrancar* habilitación, pero **sí es requisito antes de operar en producción**, porque sin ella no se puede declarar una contingencia **Tipo 03** (ver Suplemento C). Conviene tramitarla en paralelo.

---

## Suplemento C — Procedimiento operativo de contingencias

Dos tipos de contingencia, con procedimientos distintos:

### Tipo 04 — Falla de la DIAN

1. **Verificar la caída** con **4 intentos, uno cada 20 segundos**, antes de declarar la contingencia por cuenta propia.
2. **Guardar evidencia** del error del servidor (captura / respuesta).
3. **Expedir sin validación** previa de la DIAN.
4. **Reintentar a los 30 minutos** el envío para validación.
5. **Transmitir dentro de las 48 horas** marcando los documentos como **Tipo 04**.

### Tipo 03 — Falla propia o del proveedor tecnológico

1. **Requiere la numeración de contingencia ya solicitada** (Fase 4, formulario 1876). **No se puede improvisar** cuando ya ocurrió la falla.
2. **Facturar en papel** usando ese rango de talonario autorizado.
3. **Transcribir esas facturas en el sistema dentro de las 48 horas** siguientes, marcándolas como **Tipo 03**.

---

## Qué haremos al volver a Cursor (fuera de este checklist)

- **Implementar Nota Crédito y Nota Débito** (`ubl_credit_note.py` / `ubl_debit_note.py`) — **ahora obligatorias** para completar el set de pruebas (ya **no** son post-MVP).
- Aprobar los **sets de habilitación de la Caja V19** (escenario por escenario, incluidos los 4 documentos del set).
- Implementar el **código QR** y el **PDF de representación gráfica**.
- Ampliar la **cobertura tributaria**: INC, ICA y retenciones.

---

*Documento de control de trámites externos. Generado al cierre de la fase de desarrollo del MVP. Actualice la columna **Estado** a medida que avance.*
