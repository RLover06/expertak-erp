import axios from 'axios';
import { demoAdapter } from './demo.js';

// FastAPI backend only: http://localhost:8000/api/v1
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
});

// Demo pública (GitHub Pages): sin backend, responde con datos ficticios en el navegador.
export const DEMO = import.meta.env.VITE_DEMO === 'true';
if (DEMO) api.defaults.adapter = demoAdapter;

export async function validateFile(file) {
  const formData = new FormData();
  formData.append('file', file);

  try {
    const response = await api.post('/import/validate', formData);
    return response.data;
  } catch (error) {
    if (error.response) {
      const responseMessage =
        error.response.data?.message ||
        error.response.data?.detail ||
        (typeof error.response.data === 'string' ? error.response.data : null) ||
        (error.response.status ? `Error al validar archivo (HTTP ${error.response.status})` : null) ||
        'Error al validar archivo';
      throw new Error(responseMessage);
    }
    throw new Error(error?.message || 'Error de conexión al servidor');
  }
}

export async function importFile(file) {
  const formData = new FormData();
  formData.append('file', file);

  try {
    const response = await api.post('/import', formData, {
      timeout: 300000, // 5 minutes timeout for large files
    });
    return response.data;
  } catch (error) {
    if (error.response) {
      const responseMessage =
        error.response.data?.message ||
        error.response.data?.detail ||
        (typeof error.response.data === 'string' ? error.response.data : null) ||
        (error.response.status ? `Error al importar archivo (HTTP ${error.response.status})` : null) ||
        'Error al importar archivo';
      throw new Error(responseMessage);
    }
    if (error.code === 'ECONNABORTED') {
      throw new Error('Tiempo de espera agotado. El archivo es muy grande.');
    }
    throw new Error(error?.message || 'Error de conexión al servidor');
  }
}

export async function importRows(rows, fileName) {
  try {
    const response = await api.post('/import', {
      rows,
      file_name: fileName || null,
    });
    return response.data;
  } catch (error) {
    if (error.response) {
      const responseMessage =
        error.response.data?.message ||
        error.response.data?.detail ||
        (typeof error.response.data === 'string' ? error.response.data : null) ||
        (error.response.status ? `Error al importar archivo (HTTP ${error.response.status})` : null) ||
        'Error al importar archivo';
      throw new Error(responseMessage);
    }
    if (error.code === 'ECONNABORTED') {
      throw new Error('Tiempo de espera agotado. El archivo es muy grande.');
    }
    throw new Error(error?.message || 'Error de conexión al servidor');
  }
}

export async function previewExcelFile(file) {
  const formData = new FormData();
  formData.append('file', file);

  try {
    const response = await api.post('/import/preview', formData, {
      timeout: 300000,
    });
    const payload = response.data || {};
    const headers = Array.isArray(payload.headers) ? payload.headers : [];
    const rows = Array.isArray(payload.rows) ? payload.rows : [];

    // Normalize to rows as objects keyed by header for table rendering.
    const normalizedRows = rows.map((row) => {
      if (row && typeof row === 'object' && !Array.isArray(row)) {
        return row;
      }
      const record = {};
      headers.forEach((header, index) => {
        record[header] = Array.isArray(row) ? row[index] ?? '' : '';
      });
      return record;
    });

    return { headers, rows: normalizedRows };
  } catch (error) {
    if (error.response) {
      const responseMessage =
        error.response.data?.message ||
        error.response.data?.detail ||
        (typeof error.response.data === 'string' ? error.response.data : null) ||
        (error.response.status ? `Error al previsualizar archivo (HTTP ${error.response.status})` : null) ||
        'Error al previsualizar archivo';
      throw new Error(responseMessage);
    }
    if (error.code === 'ECONNABORTED') {
      throw new Error('Tiempo de espera agotado. El archivo es muy grande.');
    }
    throw new Error(error?.message || 'Error de conexión al servidor');
  }
}

export async function getDocumentos({ skip = 0, limit = 20, cufe_cude, nit_emisor, nit_receptor, estado } = {}) {
  try {
    const response = await api.get('/documentos', {
      params: { skip, limit, cufe_cude, nit_emisor, nit_receptor, estado },
    });
    return response.data;
  } catch (error) {
    if (error.response) {
      const responseMessage =
        error.response.data?.message ||
        error.response.data?.detail ||
        (typeof error.response.data === 'string' ? error.response.data : null) ||
        (error.response.status ? `Error al cargar documentos (HTTP ${error.response.status})` : null) ||
        'Error al cargar documentos';
      throw new Error(responseMessage);
    }
    throw new Error(error?.message || 'Error de conexión al servidor');
  }
}

export async function getDocumentosResumen({
  empresa,
  grupo,
  tipo_documento,
  fecha_desde,
  fecha_hasta,
} = {}) {
  try {
    const response = await api.get('/documentos/resumen', {
      params: { empresa, grupo, tipo_documento, fecha_desde, fecha_hasta },
    });
    return response.data;
  } catch (error) {
    if (error.response) {
      const responseMessage =
        error.response.data?.message ||
        error.response.data?.detail ||
        (typeof error.response.data === 'string' ? error.response.data : null) ||
        (error.response.status ? `Error al cargar resumen (HTTP ${error.response.status})` : null) ||
        'Error al cargar resumen';
      throw new Error(responseMessage);
    }
    throw new Error(error?.message || 'Error de conexión al servidor');
  }
}

export async function importResumenRows(rows, fileName, headers = null) {
  try {
    const headersToSend = headers || (rows?.length > 0 ? Object.keys(rows[0]) : null);
    const response = await api.post('/resumen/import', {
      rows,
      file_name: fileName || null,
      headers: headersToSend,
    });
    return response.data;
  } catch (error) {
    if (error.response) {
      const responseMessage =
        error.response.data?.message ||
        error.response.data?.detail ||
        (typeof error.response.data === 'string' ? error.response.data : null) ||
        (error.response.status ? `Error al importar resumen (HTTP ${error.response.status})` : null) ||
        'Error al importar resumen';
      throw new Error(responseMessage);
    }
    throw new Error(error?.message || 'Error de conexión al servidor');
  }
}

export async function importConsolidadoRows(rows, fileName, headers = null) {
  try {
    const headersToSend = headers || (rows?.length > 0 ? Object.keys(rows[0]) : null);
    const response = await api.post('/consolidado/import', {
      rows,
      file_name: fileName || null,
      headers: headersToSend,
    });
    return response.data;
  } catch (error) {
    if (error.response) {
      const responseMessage =
        error.response.data?.message ||
        error.response.data?.detail ||
        (typeof error.response.data === 'string' ? error.response.data : null) ||
        (error.response.status ? `Error al importar consolidado (HTTP ${error.response.status})` : null) ||
        'Error al importar consolidado';
      throw new Error(responseMessage);
    }
    throw new Error(error?.message || 'Error de conexión al servidor');
  }
}

export async function getInformeReporte({
  empresa,
  grupo,
  tipo_documento,
  fecha_desde,
  fecha_hasta,
} = {}) {
  try {
    const response = await api.get('/consolidado/reporte-fe', {
      params: { empresa, grupo, tipo_documento, fecha_desde, fecha_hasta },
    });
    return response.data;
  } catch (error) {
    if (error.response) {
      const responseMessage =
        error.response.data?.message ||
        error.response.data?.detail ||
        (typeof error.response.data === 'string' ? error.response.data : null) ||
        (error.response.status ? `Error al cargar informe (HTTP ${error.response.status})` : null) ||
        'Error al cargar informe';
      throw new Error(responseMessage);
    }
    throw new Error(error?.message || 'Error de conexión al servidor');
  }
}

export async function getPivotOptions() {
  try {
    const response = await api.get('/consolidado/options');
    return response.data;
  } catch (error) {
    if (error.response) {
      const responseMessage =
        error.response.data?.message ||
        error.response.data?.detail ||
        (typeof error.response.data === 'string' ? error.response.data : null) ||
        (error.response.status ? `Error al cargar filtros (HTTP ${error.response.status})` : null) ||
        'Error al cargar filtros';
      throw new Error(responseMessage);
    }
    throw new Error(error?.message || 'Error de conexión al servidor');
  }
}

export async function getPivotData({
  empresa_id,
  tercero_id,
  fecha_desde,
  fecha_hasta,
  cuenta,
  periodo,
  group_by,
} = {}) {
  try {
    const response = await api.get('/consolidado/pivot', {
      params: { empresa_id, tercero_id, fecha_desde, fecha_hasta, cuenta, periodo, group_by },
    });
    return response.data;
  } catch (error) {
    if (error.response) {
      const responseMessage =
        error.response.data?.message ||
        error.response.data?.detail ||
        (typeof error.response.data === 'string' ? error.response.data : null) ||
        (error.response.status ? `Error al cargar pivot (HTTP ${error.response.status})` : null) ||
        'Error al cargar pivot';
      throw new Error(responseMessage);
    }
    throw new Error(error?.message || 'Error de conexión al servidor');
  }
}

// ─────────────────────────────────────────────────────────────────────────
// Facturación electrónica (FE)
// ─────────────────────────────────────────────────────────────────────────

function feError(error, fallback) {
  if (error.response) {
    const data = error.response.data;
    const detail = data?.detail;
    // FastAPI puede devolver detail como objeto (p. ej. errores DIAN) o string.
    const msg =
      (typeof detail === 'string' ? detail : null) ||
      (detail && typeof detail === 'object' ? detail.message : null) ||
      data?.message ||
      (typeof data === 'string' ? data : null) ||
      (error.response.status ? `${fallback} (HTTP ${error.response.status})` : null) ||
      fallback;
    const err = new Error(msg);
    err.detail = detail;
    err.status = error.response.status;
    return err;
  }
  return new Error(error?.message || 'Error de conexión al servidor');
}

export async function getEmpresasFE() {
  try {
    const response = await api.get('/fe/empresas');
    return response.data;
  } catch (error) {
    throw feError(error, 'Error al cargar empresas');
  }
}

export async function getEmpresaFE(nit) {
  try {
    const response = await api.get(`/fe/empresas/${encodeURIComponent(nit)}`);
    return response.data;
  } catch (error) {
    throw feError(error, 'Error al cargar la empresa');
  }
}

export async function getFacturasFE(limit = 50) {
  try {
    const response = await api.get('/fe/facturas', { params: { limit } });
    return response.data;
  } catch (error) {
    throw feError(error, 'Error al cargar facturas');
  }
}

export async function getFacturaFE(id) {
  try {
    const response = await api.get(`/fe/facturas/${id}`);
    return response.data;
  } catch (error) {
    throw feError(error, 'Error al cargar la factura');
  }
}

/** Crea un BORRADOR (no transmite). Funciona sin credenciales DIAN. */
export async function crearBorradorFE(payload) {
  try {
    const response = await api.post('/fe/emitir-simple', { ...payload, enviar: false });
    return response.data;
  } catch (error) {
    throw feError(error, 'Error al crear el borrador');
  }
}

/** Transmite a la DIAN un borrador existente (BORRADOR → PENDIENTE → ...). */
export async function enviarBorradorFE(id, modo = 'habilitacion') {
  try {
    const response = await api.post(`/fe/facturas/${id}/enviar`, null, {
      params: { modo },
      timeout: 120000,
    });
    return response.data;
  } catch (error) {
    throw feError(error, 'Error al enviar la factura');
  }
}

/** Genera un BORRADOR nuevo a partir de una RECHAZADA (la original sigue RECHAZADA). */
export async function corregirFacturaFE(id) {
  try {
    const response = await api.post(`/fe/facturas/${id}/corregir`);
    return response.data;
  } catch (error) {
    throw feError(error, 'Error al corregir la factura');
  }
}

export default api;
