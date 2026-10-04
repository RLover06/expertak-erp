// Modo demo: responde las llamadas de la API en el navegador con datos ficticios,
// sin backend ni base de datos. Se activa al compilar con VITE_DEMO=true.
// Nada de lo que se hace en la demo sale del navegador ni se guarda.

const EMPRESAS = [
  'COMERCIALIZADORA PILOTO UNO S.A.S.',
  'SERVICIOS PILOTO DOS LTDA',
  'DISTRIBUCIONES PILOTO TRES S.A.S.',
  'IPS DEMO SALUD S.A.S.',
  'FERRETERIA EJEMPLO S.A.S.',
];
const TIPOS = ['Factura electrónica', 'Nota crédito electrónica', 'Documento soporte'];
const PROVEEDORES = ['PROVEEDOR ALFA S.A.S.', 'SUMINISTROS BETA LTDA', 'LOGISTICA GAMMA S.A.S.', 'TECNOLOGIA DELTA S.A.S.'];

// Generador pseudoaleatorio con semilla: la demo muestra siempre los mismos datos.
function rng(seed) {
  let s = seed;
  return () => ((s = (s * 1664525 + 1013904223) % 4294967296) / 4294967296);
}

function seedDocumentos() {
  const r = rng(42);
  const docs = [];
  let folio = 1000;
  EMPRESAS.forEach((empresa, ei) => {
    const n = 18 + ei * 5;
    for (let i = 0; i < n; i++) {
      const tipo = r() < 0.78 ? TIPOS[0] : r() < 0.6 ? TIPOS[1] : TIPOS[2];
      const grupo = r() < 0.55 ? 'Emitido' : 'Recibido';
      const base = Math.round((300000 + r() * 9500000) / 100) * 100;
      const iva = Math.round(base * (r() < 0.8 ? 0.19 : 0.05));
      const ica = grupo === 'Recibido' ? Math.round(base * 0.00966) : 0;
      const reteRenta = grupo === 'Recibido' ? Math.round(base * 0.025) : 0;
      const signo = tipo === TIPOS[1] ? -1 : 1;
      const mes = 1 + Math.floor(r() * 9);
      const dia = 1 + Math.floor(r() * 27);
      docs.push({
        tipo_documento: tipo,
        cufe_cude: `demo-${ei}-${i}-${Math.floor(r() * 1e9).toString(16)}`,
        folio: String(folio++),
        prefijo: grupo === 'Emitido' ? `FE${ei + 1}` : 'FV',
        fecha_emision: `2026-${String(mes).padStart(2, '0')}-${String(dia).padStart(2, '0')}`,
        nombre_emisor: grupo === 'Emitido' ? empresa : PROVEEDORES[Math.floor(r() * PROVEEDORES.length)],
        empresa,
        grupo,
        iva: signo * iva,
        ica: signo * ica,
        rete_renta: signo * reteRenta,
        total: signo * (base + iva + ica + reteRenta),
        estado: 'Aprobado',
      });
    }
  });
  return docs;
}

const db = {
  documentos: seedDocumentos(),
  empresasFE: [
    { nit: '901111111', razon_social: EMPRESAS[0], prefijo: 'SETP', ambiente: 'habilitacion', listo: true, rango_desde: 990000000, rango_hasta: 995000000, numero_actual: 990000006 },
    { nit: '901222222', razon_social: EMPRESAS[1], prefijo: 'SETP', ambiente: 'habilitacion', listo: true, rango_desde: 990000000, rango_hasta: 995000000, numero_actual: 990000002 },
    { nit: '901333333', razon_social: EMPRESAS[2], prefijo: 'SETP', ambiente: 'habilitacion', listo: false, rango_desde: 990000000, rango_hasta: 995000000, numero_actual: 989999999 },
  ],
  facturas: [],
  nextId: 1,
};

const IMPUESTOS_OTROS = ['ica', 'ic', 'inc', 'timbre', 'inc_bolsas', 'in_carbono', 'in_combustibles', 'ic_datos', 'icl', 'inpp', 'ibua', 'icui'];
const RETENCIONES = ['rete_iva', 'rete_renta', 'rete_ica'];

// ── Utilidades ───────────────────────────────────────────────────────────
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

function num(v) {
  if (v === null || v === undefined || v === '') return 0;
  if (typeof v === 'number') return v;
  let s = String(v).trim().replace(/[$\s]/g, '');
  if (/,\d{1,2}$/.test(s)) s = s.replace(/\./g, '').replace(',', '.'); // 1.234,56
  else s = s.replace(/,/g, '');
  const x = parseFloat(s);
  return Number.isFinite(x) ? x : 0;
}

function co(v) {
  return Number(v).toLocaleString('es-CO', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function normHeader(h) {
  return String(h ?? '').normalize('NFKD').replace(/[̀-ͯ]/g, '').replace(/\//g, ' ').replace(/\s+/g, ' ').trim().toLowerCase();
}

const HEADER_MAP = {
  'tipo de documento': 'tipo_documento', 'tipo documento': 'tipo_documento',
  'cufe cude': 'cufe_cude', cufe: 'cufe_cude', cude: 'cufe_cude',
  folio: 'folio', prefijo: 'prefijo',
  'fecha emision': 'fecha_emision', 'nit emisor': 'nit_emisor', 'nombre emisor': 'nombre_emisor',
  'razon social': 'nombre_emisor', 'nit receptor': 'nit_receptor', 'nombre receptor': 'nombre_receptor',
  iva: 'iva', ica: 'ica', ic: 'ic', inc: 'inc', timbre: 'timbre',
  'rete iva': 'rete_iva', 'rete renta': 'rete_renta', 'rete ica': 'rete_ica',
  total: 'total', estado: 'estado', grupo: 'grupo', empresa: 'empresa',
};

const CONSOLIDADO_REQUERIDOS = ['empresa', 'tercero', 'fecha', 'cuenta'];

function contains(value, filter) {
  return !filter || String(value || '').toLowerCase().includes(String(filter).toLowerCase());
}

async function sha384(text) {
  const data = new TextEncoder().encode(text);
  const hash = await crypto.subtle.digest('SHA-384', data);
  return [...new Uint8Array(hash)].map((b) => b.toString(16).padStart(2, '0')).join('');
}

// ── Endpoints ────────────────────────────────────────────────────────────
async function previewExcel(file) {
  const XLSX = await import('xlsx');
  const wb = XLSX.read(await file.arrayBuffer(), { type: 'array', cellDates: true });
  const sheet = wb.Sheets[wb.SheetNames[0]];
  const rows = XLSX.utils.sheet_to_json(sheet, { defval: null, raw: false });
  const headers = rows.length ? Object.keys(rows[0]) : [];
  return { headers, rows: rows.slice(0, 5000) };
}

function importDocumentos(rows, fileName) {
  let inserted = 0;
  let duplicates = 0;
  const errors = [];
  const existentes = new Set(db.documentos.map((d) => d.cufe_cude));
  rows.forEach((raw, i) => {
    const d = {};
    for (const [k, v] of Object.entries(raw)) {
      const key = HEADER_MAP[normHeader(k)] || normHeader(k).replace(/ /g, '_');
      d[key] = v;
    }
    const faltan = ['tipo_documento', 'cufe_cude', 'total'].filter((f) => d[f] === null || d[f] === undefined || d[f] === '');
    if (faltan.length) {
      errors.push({ row_number: i + 2, errors: faltan.map((f) => `Campo requerido vacío: ${f}`) });
      return;
    }
    if (existentes.has(String(d.cufe_cude))) { duplicates++; return; }
    existentes.add(String(d.cufe_cude));
    db.documentos.push(d);
    inserted++;
  });
  return {
    success: true,
    message: 'Importación completada correctamente (demo: los datos solo viven en este navegador)',
    file_name: fileName, file_size: null,
    total_rows: rows.length, inserted, duplicates, rejected: errors.length, errors: errors.slice(0, 50),
    processing_time_seconds: 0.4,
  };
}

function importConsolidado(rows, fileName) {
  const errors = [];
  rows.forEach((raw, i) => {
    const keys = Object.keys(raw).map(normHeader);
    const faltan = CONSOLIDADO_REQUERIDOS.filter((f) => !keys.includes(f) || raw[Object.keys(raw)[keys.indexOf(f)]] == null);
    if (faltan.length) errors.push({ row_number: i + 2, errors: faltan.map((f) => `Campo requerido vacío: ${f}`) });
  });
  return {
    success: true,
    message: 'Consolidado importado correctamente (demo)',
    file_name: fileName,
    total_rows: rows.length, inserted: rows.length - errors.length, rejected: errors.length, errors: errors.slice(0, 50),
    processing_time_seconds: 0.3,
  };
}

function reporte({ empresa, grupo, tipo_documento, fecha_desde, fecha_hasta } = {}) {
  const grupos = new Map();
  for (const d of db.documentos) {
    const emp = d.empresa || d.nombre_emisor || '';
    if (!contains(emp, empresa) || !contains(d.grupo, grupo) || !contains(d.tipo_documento, tipo_documento)) continue;
    const f = String(d.fecha_emision || '').slice(0, 10);
    if (fecha_desde && f && f < fecha_desde) continue;
    if (fecha_hasta && f && f > fecha_hasta) continue;
    const key = [emp, d.grupo || '', d.tipo_documento || ''].join('|');
    const g = grupos.get(key) || { emp, grp: d.grupo || '', tip: d.tipo_documento || '', iva: 0, otros: 0, renta: 0, total: 0 };
    g.iva += num(d.iva);
    g.otros += IMPUESTOS_OTROS.reduce((s, k) => s + num(d[k]), 0);
    g.renta += RETENCIONES.reduce((s, k) => s + num(d[k]), 0);
    g.total += num(d.total);
    grupos.set(key, g);
  }
  const ordenados = [...grupos.values()].sort((a, b) => (a.emp + a.grp + a.tip).localeCompare(b.emp + b.grp + b.tip));
  const suma = { sub: 0, iva: 0, otros: 0, renta: 0, total: 0 };
  const rows = ordenados.map((g) => {
    const sub = g.total - g.renta - g.otros - g.iva;
    suma.sub += sub; suma.iva += g.iva; suma.otros += g.otros; suma.renta += g.renta; suma.total += g.total;
    return {
      Empresa: g.emp, Tipo_de_documento: g.tip, Grupo: g.grp,
      Subtotal: co(sub), IVA: co(g.iva), Total_otros: co(g.otros), Total_renta: co(g.renta), Total: co(g.total),
    };
  });
  rows.push({
    Empresa: `Total Acumulado (${rows.length}) - Suma`, Tipo_de_documento: '', Grupo: '',
    Subtotal: co(suma.sub), IVA: co(suma.iva), Total_otros: co(suma.otros), Total_renta: co(suma.renta), Total: co(suma.total),
  });
  return { rows };
}

function credenciales(e) {
  const faltantes = e.listo ? [] : ['clave_tecnica', 'software_pin', 'certificado (.p12)'];
  return {
    listo_para_emitir: e.listo, faltantes,
    tiene_clave_tecnica: e.listo, tiene_software_id: true, tiene_software_pin: e.listo,
    tiene_certificado: e.listo, tiene_resolucion: true, tiene_rango: true,
  };
}

function empresaDetalle(nit) {
  const e = db.empresasFE.find((x) => x.nit === nit);
  if (!e) throw httpError(404, 'Empresa no encontrada');
  return {
    nit: e.nit, razon_social: e.razon_social, prefijo: e.prefijo,
    rango_desde: e.rango_desde, rango_hasta: e.rango_hasta, numero_actual: e.numero_actual,
    resolucion_numero: '18760000001', resolucion_fecha_desde: '2026-01-01', resolucion_fecha_hasta: '2027-12-31',
    ambiente: e.ambiente, tipo_documento: '31', tax_level_code: 'O-13',
    direccion: 'Calle 1 # 2-3', departamento: 'Córdoba', departamento_code: '23', municipio_code: '23001', ciudad: 'Montería',
    credenciales: credenciales(e),
  };
}

function calcular(items) {
  let subtotal = 0;
  let iva = 0;
  for (const it of items) {
    const base = Math.round((num(it.cantidad) * num(it.precio_unitario) - num(it.descuento)) * 100) / 100;
    subtotal += base;
    iva += Math.round(base * num(it.iva_porcentaje)) / 100;
  }
  return { subtotal: subtotal.toFixed(2), iva: iva.toFixed(2), total: (subtotal + iva).toFixed(2) };
}

function resumenFactura(f) {
  const { items, logs, prefijo, numero, ...resto } = f;
  return resto;
}

function crearBorrador(payload) {
  if (!db.empresasFE.some((e) => e.nit === payload.empresa_nit)) throw httpError(400, 'Empresa no configurada');
  if (!payload.items?.length) throw httpError(400, 'La factura debe tener al menos un ítem');
  const t = calcular(payload.items);
  const f = {
    id: db.nextId++, empresa_nit: payload.empresa_nit, cufe: null, factura_numero: null, estado: 'BORRADOR',
    adquirente_nit: payload.adquirente?.nit, adquirente_nombre: payload.adquirente?.nombre,
    ...t, ambiente: payload.modo || 'habilitacion', created_at: new Date().toISOString(),
    items: payload.items, logs: [{ estado: 'BORRADOR', at: new Date().toISOString() }],
  };
  db.facturas.unshift(f);
  return {
    success: true, estado: 'BORRADOR', factura_id: String(f.id), ...t, enviado: false, modo: f.ambiente,
    message: `Borrador #${f.id} guardado. Aún no se ha enviado a la DIAN.`, errores: [],
  };
}

async function enviar(id, modo) {
  const f = db.facturas.find((x) => String(x.id) === String(id));
  if (!f) throw httpError(404, 'Factura no encontrada');
  const e = db.empresasFE.find((x) => x.nit === f.empresa_nit);
  if (!e.listo) {
    throw httpError(400, { message: 'La empresa no tiene credenciales DIAN completas', errores: credenciales(e).faltantes.map((x) => `Falta ${x}`) });
  }
  await sleep(900);
  e.numero_actual += 1;
  const numero = `${e.prefijo}${e.numero_actual}`;
  const ahora = new Date();
  const fecha = ahora.toISOString().slice(0, 10);
  const hora = ahora.toTimeString().slice(0, 8) + '-05:00';
  // Misma fórmula del CUFE (§11.2), con una clave técnica ficticia de demostración.
  const cufe = await sha384(
    numero + fecha + hora + f.subtotal + '01' + f.iva + '04' + '0.00' + '03' + '0.00' + f.total +
      e.nit + (f.adquirente_nit || '') + 'clave-tecnica-demo' + (modo === 'produccion' ? '1' : '2'),
  );
  Object.assign(f, { estado: 'VALIDADA', cufe, factura_numero: numero, ambiente: modo || f.ambiente });
  f.logs.push({ estado: 'VALIDADA', at: ahora.toISOString() });
  return {
    success: true, estado: 'VALIDADA', cufe, factura_id: String(f.id), factura_numero: numero,
    subtotal: f.subtotal, iva: f.iva, total: f.total, enviado: true, modo: f.ambiente,
    message: 'Factura validada (simulación: en la demo no se envía nada a la DIAN).', errores: [],
  };
}

function corregir(id) {
  const f = db.facturas.find((x) => String(x.id) === String(id));
  if (!f) throw httpError(404, 'Factura no encontrada');
  const nueva = { ...f, id: db.nextId++, estado: 'BORRADOR', cufe: null, factura_numero: null, created_at: new Date().toISOString(), logs: [] };
  db.facturas.unshift(nueva);
  return resumenFactura(nueva);
}

// ── Adaptador de axios ───────────────────────────────────────────────────
function httpError(status, detail) {
  const err = new Error(typeof detail === 'string' ? detail : detail.message);
  err.response = { status, data: { detail } };
  return err;
}

async function route(method, path, params, data) {
  if (method === 'post' && path === '/import/preview') return previewExcel(data.get('file'));
  if (method === 'post' && path === '/import') return importDocumentos(data.rows || [], data.file_name);
  if (method === 'post' && (path === '/consolidado/import' || path === '/resumen/import')) return importConsolidado(data.rows || [], data.file_name);
  if (method === 'get' && (path === '/consolidado/reporte-fe' || path === '/documentos/resumen')) return reporte(params);
  if (method === 'get' && path === '/documentos') {
    const items = db.documentos.slice(params.skip || 0, (params.skip || 0) + (params.limit || 20));
    return { items, total: db.documentos.length, skip: params.skip || 0, limit: params.limit || 20 };
  }
  if (method === 'get' && path === '/fe/empresas') {
    return db.empresasFE.map((e) => ({ nit: e.nit, razon_social: e.razon_social, prefijo: e.prefijo, ambiente: e.ambiente, listo_para_emitir: e.listo }));
  }
  let m;
  if (method === 'get' && (m = path.match(/^\/fe\/empresas\/(.+)$/))) return empresaDetalle(decodeURIComponent(m[1]));
  if (method === 'get' && path === '/fe/facturas') return db.facturas.slice(0, params.limit || 50).map(resumenFactura);
  if (method === 'get' && (m = path.match(/^\/fe\/facturas\/(\d+)$/))) {
    const f = db.facturas.find((x) => String(x.id) === m[1]);
    if (!f) throw httpError(404, 'Factura no encontrada');
    return f;
  }
  if (method === 'post' && path === '/fe/emitir-simple') return crearBorrador(data);
  if (method === 'post' && (m = path.match(/^\/fe\/facturas\/(\d+)\/enviar$/))) return enviar(m[1], params.modo);
  if (method === 'post' && (m = path.match(/^\/fe\/facturas\/(\d+)\/corregir$/))) return corregir(m[1]);
  if (path === '/health') return { status: 'ok', mode: 'demo' };
  throw httpError(404, `Ruta no disponible en la demo: ${path}`);
}

export async function demoAdapter(config) {
  const path = (config.url || '').replace(/^https?:\/\/[^/]+/, '').replace(/^\/api\/v1/, '');
  let data = config.data;
  if (typeof data === 'string') {
    try { data = JSON.parse(data); } catch { /* FormData u otro */ }
  }
  await sleep(250);
  const body = await route((config.method || 'get').toLowerCase(), path, config.params || {}, data);
  return { data: body, status: 200, statusText: 'OK', headers: {}, config, request: {} };
}

// Facturas de ejemplo para que el historial no arranque vacío.
(function seedFacturas() {
  const ejemplos = [
    { estado: 'VALIDADA', empresa_nit: '901111111', numero: 'SETP990000005', nit: '900123456', nombre: 'CLIENTE PRUEBA SAS', sub: 1250000 },
    { estado: 'RECHAZADA', empresa_nit: '901111111', numero: 'SETP990000006', nit: '800000001', nombre: 'COMERCIAL DEMO LTDA', sub: 480000 },
    { estado: 'BORRADOR', empresa_nit: '901222222', numero: null, nit: '900765432', nombre: 'SERVICIOS DE PRUEBA SAS', sub: 2100000 },
  ];
  for (const e of ejemplos) {
    const iva = Math.round(e.sub * 0.19);
    db.facturas.unshift({
      id: db.nextId++, empresa_nit: e.empresa_nit, estado: e.estado, factura_numero: e.numero,
      cufe: e.estado === 'BORRADOR' ? null : Array.from({ length: 96 }, (_, i) => '0123456789abcdef'[(i * 7 + db.nextId * 13) % 16]).join(''),
      adquirente_nit: e.nit, adquirente_nombre: e.nombre,
      subtotal: e.sub.toFixed(2), iva: iva.toFixed(2), total: (e.sub + iva).toFixed(2),
      ambiente: 'habilitacion', created_at: '2026-09-28T10:00:00-05:00',
      items: [{ descripcion: 'Servicio de asesoría contable', cantidad: 1, precio_unitario: e.sub, iva_porcentaje: 19, descuento: 0 }],
      logs: [],
    });
  }
})();
