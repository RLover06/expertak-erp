# Carpeta de referencia — Facturación electrónica

**Ruta única de materiales (oficial DIAN + implementación de prueba):**

```text
C:\path\to\facturacion
```

Expertak **no duplica** estos archivos en el repo Git; se usa esta carpeta como biblioteca local durante el desarrollo.

---

## Contenido de la carpeta

### Documentación DIAN (PDF)

| Archivo | Descripción |
|---------|-------------|
| `Anexo-Tecnico-Factura-Electronica-de-Venta-vr-1-9.pdf` | Anexo técnico UBL 1.9 (~11 MB) |
| `Guia-Herramienta-para-el-Consumo-de-Web-Services.pdf` | Consumo Web Services SOAP |
| `Nuevo-Diseno-Sistema-de-Facturacion-Electronica.pdf` | Diseño del sistema FE |
| `Numeracion2022-Habilitacion-F.pdf` | Habilitación numeración |
| `Numeracion2022-Inhabilitacion-F.pdf` | Inhabilitación |
| `Numeracion2022-PreguntasFrecuentes-F.pdf` | FAQ numeración |
| `Solicitud-autorizacion-de-numeracion-facturacion.pdf` | Solicitud resolución |
| `Resolución 000202 de 31-03-2025.pdf` | Resolución 2025 |
| `Preguntas-y-respuestas-Proveedores-Tecnologicos-FE.pdf` | PT vs software propio |
| `Presentacion-Recepcion-de-Facturas-Electronicas.pdf` | Recepción FE |

### Paquetes ZIP

| Archivo | Descripción |
|---------|-------------|
| `Caja-de-herramientas-FE-V19-V2026.zip` | XSD, XML ejemplo, sets habilitación DIAN |
| `Listado-Correos-de-recepcion-documentos-e-instrumentos-electronicos.zip` | Listado correos recepción |
| `facturacion-electronica-colombia-main.zip` | Backup del repo GitHub |

### Operación y negocio

| Archivo | Descripción |
|---------|-------------|
| `Para probar en desarrollo.docx` | Notas ambiente habilitación / pruebas |
| `EXPARTAK.pptx`, `IEXPARTAK.pptx` | Presentaciones proyecto |
| `*.png` | Capturas / diagramas |

### Código de referencia (software propio FE)

Carpeta descomprimida del repo [facturacion-electronica-colombia](https://github.com/Crispancho93/facturacion-electronica-colombia):

```text
C:\path\to\facturacion\facturacion-electronica-colombia-main\facturacion-electronica-colombia-main\
```

**Ejecutar API de referencia (puerto distinto a Expertak):**

```powershell
cd "C:\path\to\facturacion\facturacion-electronica-colombia-main\facturacion-electronica-colombia-main"
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
# Configurar .env (PATH_BASE, certificado .pfx, etc.)
uvicorn app:app --reload --port 8001
```

Documentación API: http://localhost:8001/docs

---

## Relación con Expertak

| Componente | Ubicación |
|------------|-----------|
| App principal (importación, consolidado, UI) | `C:\path\to\expertak` |
| **Datos reales multi-empresa** | `C:\path\to\SOFT` → ver [`SOFT_NEGOCIO.md`](SOFT_NEGOCIO.md) |
| Docs + plan FE | `expertak\docs\DIAN_FACTURACION.md` |
| Base de datos | Supabase (ver `expertak\SUPABASE.md`) |
| DIAN oficial + código habilitación | `Desktop\facturacion` (esta carpeta) |

---

## Seguridad

- **No** subir a Git: `.pfx`, contraseñas, `.env` del repo de referencia.
- Mantener certificados solo en `PATH_BASE/certificados/` del proyecto de referencia o en variable de entorno del servidor.

---

## Siguiente paso

Ver plan de integración: [`DIAN_FACTURACION.md`](DIAN_FACTURACION.md)
