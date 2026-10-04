# Emisión de facturas electrónicas — Expertak

Prioridad: **generar XML conforme DIAN → firmar → enviar a validación** (habilitación primero, producción después).

## Arquitectura

```text
Expertak API (:8000)                    Motor DIAN de referencia
/api/v1/fe/emitir          ──────►    facturacion-electronica-colombia (:8001)
                                       o inline (mismo proceso)
                                              │
                                              ▼
                                    vpfe-hab.dian.gov.co (habilitación)
                                    vpfe.dian.gov.co (producción)
```

El motor de referencia ya implementa UBL 2.1, CUFE, firma XAdES y SOAP DIAN.

**Ruta local:** `C:\path\to\facturacion\facturacion-electronica-colombia-main\facturacion-electronica-colombia-main`

---

## Paso 1 — Configurar motor de referencia

1. Copie `.env` con `PATH_BASE`, `SIGN_NAME`, `SIGN_PASSWORD` (certificado `.pfx`).
2. En `PATH_BASE` debe existir estructura de resolución/XML según el proyecto de referencia.

```powershell
cd "C:\path\to\facturacion\facturacion-electronica-colombia-main\facturacion-electronica-colombia-main"
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
uvicorn app:app --reload --port 8001
```

Verifique: http://localhost:8001/docs

---

## Paso 2 — Configurar Expertak

En `backend/.env`:

```env
DIAN_REFERENCE_APP=C:\path\to\facturacion\facturacion-electronica-colombia-main\facturacion-electronica-colombia-main
DIAN_SERVICE_URL=http://localhost:8001
DIAN_ENGINE=auto
```

```powershell
cd C:\path\to\expertak\backend
uvicorn app.main:app --reload --port 8000
```

---

## Paso 3 — Verificar estado

```http
GET http://localhost:8000/api/v1/fe/dian-status
```

`ready: true` cuando el servicio :8001 responde o el `.env` del motor existe.

---

## Paso 4 — Emitir factura (habilitación)

1. Copie y complete [`fe_invoice_ejemplo.json`](fe_invoice_ejemplo.json) con datos reales.
2. `ProfileExecutionID`: `"2"` = habilitación, `"1"` = producción.
3. `TestID`: ID del set de la caja de herramientas DIAN.

```http
POST http://localhost:8000/api/v1/fe/emitir
Content-Type: application/json

{
  "modo": "habilitacion",
  "invoice": { ... contenido de fe_invoice_ejemplo.json ... }
}
```

Para **producción** (solo después de aprobar habilitación):

```json
{ "modo": "produccion", "invoice": { ... } }
```

---

## Endpoints Expertak

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/v1/fe/dian-status` | Estado del motor DIAN |
| POST | `/api/v1/fe/emitir` | Generar, firmar y enviar |
| GET | `/api/v1/fe/emisiones` | Log local de intentos |

Documentación interactiva: http://localhost:8000/docs

---

## Flujo habilitación → producción

| Fase | modo | ProfileExecutionID | Endpoint referencia |
|------|------|--------------------|---------------------|
| Sets de prueba DIAN | `habilitacion` | 2 | `send_test` |
| Producción | `produccion` | 1 | `send` |

---

## Errores frecuentes

| Síntoma | Causa probable |
|---------|----------------|
| `ready: false` | Servicio :8001 apagado o sin `.env`/certificado |
| Rechazo DIAN en XML | Campos anexo técnico (CIIU, tributos, consecutivo) |
| Consecutivo inválido | Número fuera de rango de resolución |
| Firma inválida | Certificado vencido o contraseña incorrecta |

---

## Siguiente desarrollo

- Formulario Svelte (factura simple → arma JSON)
- Persistencia en Supabase (`fe_emisiones`)
- Contabilización automática al aprobar
- Nota crédito
