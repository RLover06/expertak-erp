import express, { Request, Response } from 'express';
import cors from 'cors';
import multer from 'multer';
import path from 'path';
import fs from 'fs';
import xlsx from 'xlsx';
import dotenv from 'dotenv';
import mysql from 'mysql2/promise';

dotenv.config();

const app = express();
const PORT = Number(process.env.PORT || 8000);
const UPLOAD_DIR = process.env.UPLOAD_DIR || 'uploads';
const MAX_FILE_SIZE = Number(process.env.MAX_FILE_SIZE || 50 * 1024 * 1024);
const BATCH_SIZE = Number(process.env.BATCH_SIZE || 500);

const DB_HOST = process.env.DB_HOST || 'localhost';
const DB_PORT = Number(process.env.DB_PORT || 3306);
const DB_USER = process.env.DB_USER || 'root';
const DB_PASSWORD = process.env.DB_PASSWORD || '';
const DB_NAME = process.env.DB_NAME || 'expertak';

const EXPECTED_COLUMNS = [
  'tipo_documento',
  'cufe_cude',
  'folio',
  'prefijo',
  'divisa',
  'forma_pago',
  'medio_pago',
  'fecha_emision',
  'fecha_recepcion',
  'nit_emisor',
  'nombre_emisor',
  'nit_receptor',
  'nombre_receptor',
  'iva',
  'ica',
  'ic',
  'inc',
  'timbre',
  'inc_bolsas',
  'in_carbono',
  'in_combustibles',
  'ic_datos',
  'icl',
  'inpp',
  'ibua',
  'icui',
  'rete_iva',
  'rete_renta',
  'rete_ica',
  'total',
  'estado',
  'grupo',
];

const DECIMAL_FIELDS = new Set([
  'iva',
  'ica',
  'ic',
  'inc',
  'timbre',
  'inc_bolsas',
  'in_carbono',
  'in_combustibles',
  'ic_datos',
  'icl',
  'inpp',
  'ibua',
  'icui',
  'rete_iva',
  'rete_renta',
  'rete_ica',
  'total',
]);

const INT_FIELDS = new Set(['nit_emisor', 'nit_receptor']);

const pool = mysql.createPool({
  host: DB_HOST,
  port: DB_PORT,
  user: DB_USER,
  password: DB_PASSWORD,
  database: DB_NAME,
  waitForConnections: true,
  connectionLimit: 10,
  queueLimit: 0,
});

app.use(express.json());
app.use(
  cors({
    origin: ['http://localhost:5173'],
    credentials: true,
    methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  })
);

if (!fs.existsSync(UPLOAD_DIR)) {
  fs.mkdirSync(UPLOAD_DIR, { recursive: true });
}

const storage = multer.diskStorage({
  destination: (_req, _file, cb) => cb(null, UPLOAD_DIR),
  filename: (_req, file, cb) => {
    const safeName = file.originalname.replace(/[^a-zA-Z0-9.\-_]/g, '_');
    cb(null, `${Date.now()}-${safeName}`);
  },
});

const upload = multer({
  storage,
  limits: { fileSize: MAX_FILE_SIZE },
});

type PreviewResponse = {
  headers: string[];
  rows: Record<string, unknown>[];
};

type RowError = {
  row_number: number;
  errors: string[];
};

function normalizeHeader(value: unknown): string {
  return String(value ?? '').trim();
}

function excelSerialToDate(value: number): Date | null {
  if (!Number.isFinite(value)) {
    return null;
  }
  const parsed = xlsx.SSF.parse_date_code(value);
  if (!parsed) {
    return null;
  }
  return new Date(Date.UTC(parsed.y, parsed.m - 1, parsed.d, parsed.H, parsed.M, parsed.S));
}

function parseDate(value: unknown): string | null {
  if (!value && value !== 0) {
    return null;
  }
  if (value instanceof Date) {
    return value.toISOString().slice(0, 10);
  }
  if (typeof value === 'number') {
    const dt = excelSerialToDate(value);
    return dt ? dt.toISOString().slice(0, 10) : null;
  }
  if (typeof value === 'string') {
    const trimmed = value.trim();
    if (!trimmed) return null;
    const match =
      trimmed.match(/^(\d{4})-(\d{2})-(\d{2})$/) ||
      trimmed.match(/^(\d{2})\/(\d{2})\/(\d{4})$/) ||
      trimmed.match(/^(\d{2})-(\d{2})-(\d{4})$/) ||
      trimmed.match(/^(\d{4})\/(\d{2})\/(\d{2})$/);
    if (match) {
      let year: number;
      let month: number;
      let day: number;
      if (match[1].length === 4) {
        year = Number(match[1]);
        month = Number(match[2]);
        day = Number(match[3]);
      } else {
        day = Number(match[1]);
        month = Number(match[2]);
        year = Number(match[3]);
      }
      if (year && month && day) {
        return `${String(year).padStart(4, '0')}-${String(month).padStart(2, '0')}-${String(day).padStart(
          2,
          '0'
        )}`;
      }
    }
  }
  return null;
}

function parseDateTime(value: unknown): string | null {
  if (!value && value !== 0) {
    return null;
  }
  if (value instanceof Date) {
    return value.toISOString().replace('T', ' ').slice(0, 19);
  }
  if (typeof value === 'number') {
    const dt = excelSerialToDate(value);
    return dt ? dt.toISOString().replace('T', ' ').slice(0, 19) : null;
  }
  if (typeof value === 'string') {
    const trimmed = value.trim();
    if (!trimmed) return null;
    const match = trimmed.match(
      /^(\d{4})-(\d{2})-(\d{2})(?:\s+(\d{2}):(\d{2})(?::(\d{2}))?)?$/
    );
    if (match) {
      const year = Number(match[1]);
      const month = Number(match[2]);
      const day = Number(match[3]);
      const hour = Number(match[4] || 0);
      const min = Number(match[5] || 0);
      const sec = Number(match[6] || 0);
      if (year && month && day) {
        return `${String(year).padStart(4, '0')}-${String(month).padStart(2, '0')}-${String(day).padStart(
          2,
          '0'
        )} ${String(hour).padStart(2, '0')}:${String(min).padStart(2, '0')}:${String(sec).padStart(2, '0')}`;
      }
    }
  }
  return null;
}

function parseDecimal(value: unknown): string {
  if (value === null || value === undefined || value === '') {
    return '0.00';
  }
  if (typeof value === 'number' && Number.isFinite(value)) {
    return value.toFixed(2);
  }
  if (typeof value === 'string') {
    const cleaned = value.replace(/[$,\s]/g, '');
    const parsed = Number(cleaned);
    return Number.isFinite(parsed) ? parsed.toFixed(2) : '0.00';
  }
  return '0.00';
}

function parseIntField(value: unknown): number | null {
  if (value === null || value === undefined || value === '') {
    return null;
  }
  if (typeof value === 'number' && Number.isFinite(value)) {
    return Math.trunc(value);
  }
  if (typeof value === 'string') {
    const cleaned = value.replace(/[.,\s]/g, '');
    const parsed = Number(cleaned);
    return Number.isFinite(parsed) ? Math.trunc(parsed) : null;
  }
  return null;
}

function normalizeRow(row: Record<string, unknown>): Record<string, unknown> {
  const normalized: Record<string, unknown> = {};

  for (const key of EXPECTED_COLUMNS) {
    const value = row[key];
    if (key === 'fecha_emision') {
      normalized[key] = parseDate(value);
    } else if (key === 'fecha_recepcion') {
      normalized[key] = parseDateTime(value);
    } else if (DECIMAL_FIELDS.has(key)) {
      normalized[key] = parseDecimal(value);
    } else if (INT_FIELDS.has(key)) {
      normalized[key] = parseIntField(value);
    } else {
      normalized[key] = value === null || value === undefined ? '' : String(value).trim();
    }
  }

  return normalized;
}

function isRowEmpty(row: Record<string, unknown>): boolean {
  return Object.values(row).every((value) => value === null || value === undefined || String(value).trim() === '');
}

function validateHeaders(headers: string[]): string[] {
  const normalized = headers.map((h) => String(h).trim().toLowerCase()).filter((h) => h);
  if (normalized.length !== EXPECTED_COLUMNS.length) {
    return [
      `Column count mismatch. Expected ${EXPECTED_COLUMNS.length}, found ${normalized.length}`,
    ];
  }
  const expectedLower = EXPECTED_COLUMNS.map((c) => c.toLowerCase());
  for (let i = 0; i < expectedLower.length; i += 1) {
    if (normalized[i] !== expectedLower[i]) {
      return [
        `Column order or names mismatch. Expected: ${EXPECTED_COLUMNS.join(', ')}`,
      ];
    }
  }
  return [];
}

function validateRow(row: Record<string, unknown>, rowNumber: number): string[] {
  const errors: string[] = [];
  const requiredFields = ['tipo_documento', 'cufe_cude', 'total'];

  for (const field of requiredFields) {
    const value = row[field];
    if (value === null || value === undefined || (typeof value === 'string' && !value.trim())) {
      errors.push(`Row ${rowNumber}: Required field '${field}' is empty`);
    }
  }

  const fechaEmision = row.fecha_emision;
  if (fechaEmision && !parseDate(fechaEmision)) {
    errors.push(`Row ${rowNumber}: Invalid date format for 'fecha_emision': ${fechaEmision}`);
  }

  const fechaRecepcion = row.fecha_recepcion;
  if (fechaRecepcion && !parseDateTime(fechaRecepcion)) {
    errors.push(`Row ${rowNumber}: Invalid datetime format for 'fecha_recepcion': ${fechaRecepcion}`);
  }

  for (const field of DECIMAL_FIELDS) {
    const value = row[field];
    if (value !== null && value !== undefined && value !== '') {
      const parsed = Number(String(value).replace(/,/g, ''));
      if (!Number.isFinite(parsed)) {
        errors.push(`Row ${rowNumber}: Invalid numeric value for '${field}': ${value}`);
      }
    }
  }

  for (const field of INT_FIELDS) {
    const value = row[field];
    if (value !== null && value !== undefined && value !== '') {
      const parsed = Number(String(value));
      if (!Number.isFinite(parsed)) {
        errors.push(`Row ${rowNumber}: Invalid integer value for '${field}': ${value}`);
      }
    }
  }

  return errors;
}

function normalizePreviewCell(value: unknown): string | number | null {
  if (value instanceof Date) {
    return value.toISOString();
  }
  if (typeof value === 'number' && Number.isFinite(value)) {
    return value;
  }
  if (value === null || value === undefined) {
    return null;
  }
  return String(value);
}

function readExcelFile(filePath: string): { headers: string[]; rows: unknown[][] } {
  const workbook = xlsx.readFile(filePath, { cellDates: true });
  const sheetName = workbook.SheetNames[0];
  if (!sheetName) {
    throw new Error('El archivo no contiene hojas');
  }
  const sheet = workbook.Sheets[sheetName];
  const rowsArray = xlsx.utils.sheet_to_json(sheet, {
    header: 1,
    defval: null,
    raw: true,
  }) as unknown[][];
  if (!rowsArray.length) {
    return { headers: [], rows: [] };
  }
  const headers = rowsArray[0].map((header) => normalizeHeader(header));
  const rows = rowsArray.slice(1);
  return { headers, rows };
}

async function insertBatch(
  batch: { rowNumber: number; data: Record<string, unknown> }[],
  archivoOrigen: string
): Promise<{ inserted: number; duplicates: number; errors: RowError[] }> {
  const connection = await pool.getConnection();
  const errors: RowError[] = [];
  let inserted = 0;
  let duplicates = 0;

  const columns = [...EXPECTED_COLUMNS, 'archivo_origen'];
  const placeholders = columns.map(() => '?').join(', ');
  const sql = `INSERT IGNORE INTO documentos_dian (${columns.join(', ')}) VALUES (${placeholders})`;

  try {
    await connection.beginTransaction();
    for (const item of batch) {
      try {
        const normalized = normalizeRow(item.data);
        const values = columns.map((col) =>
          col === 'archivo_origen' ? archivoOrigen : (normalized[col] as unknown)
        );
        const [result] = await connection.execute(sql, values);
        const affected = (result as mysql.ResultSetHeader).affectedRows || 0;
        if (affected === 0) {
          duplicates += 1;
        } else {
          inserted += 1;
        }
      } catch (error) {
        errors.push({
          row_number: item.rowNumber,
          errors: [error instanceof Error ? error.message : 'Unknown error'],
        });
      }
    }
    await connection.commit();
  } catch (error) {
    await connection.rollback();
    errors.push({
      row_number: 0,
      errors: [error instanceof Error ? error.message : 'Transaction failed'],
    });
  } finally {
    connection.release();
  }

  return { inserted, duplicates, errors };
}

app.post('/api/v1/import/preview', upload.single('file'), async (req: Request, res: Response) => {
  if (!req.file) {
    return res.status(400).json({ message: 'Archivo requerido' });
  }

  const filePath = req.file.path;
  const extension = path.extname(req.file.originalname).toLowerCase();

  if (extension !== '.xlsx') {
    fs.unlink(filePath, () => {});
    return res.status(400).json({ message: 'Solo se permiten archivos .xlsx' });
  }

  try {
    const { headers, rows } = readExcelFile(filePath);
    const response: PreviewResponse = {
      headers,
      rows: rows.map((row) => {
        const record: Record<string, unknown> = {};
        headers.forEach((header, index) => {
          record[header] = normalizePreviewCell(row[index]);
        });
        return record;
      }),
    };
    return res.json(response);
  } catch (error) {
    return res.status(500).json({
      message: error instanceof Error ? error.message : 'Error al procesar el archivo',
    });
  } finally {
    fs.unlink(filePath, () => {});
  }
});

app.post('/api/v1/import', upload.single('file'), async (req: Request, res: Response) => {
  const startTime = Date.now();

  if (!req.file) {
    return res.status(400).json({ message: 'Archivo requerido' });
  }

  const filePath = req.file.path;
  const extension = path.extname(req.file.originalname).toLowerCase();

  if (extension !== '.xlsx') {
    fs.unlink(filePath, () => {});
    return res.status(400).json({ message: 'Solo se permiten archivos .xlsx' });
  }

  try {
    const { headers, rows } = readExcelFile(filePath);
    const headerErrors = validateHeaders(headers);
    if (headerErrors.length) {
      return res.status(400).json({ message: `File validation failed: ${headerErrors.join(', ')}` });
    }

    const errors: RowError[] = [];
    let totalRows = 0;
    let inserted = 0;
    let duplicates = 0;

    const batch: { rowNumber: number; data: Record<string, unknown> }[] = [];

    for (let i = 0; i < rows.length; i += 1) {
      const rowNumber = i + 2;
      const rowArray = rows[i];
      const rowData: Record<string, unknown> = {};
      headers.forEach((header, index) => {
        rowData[header] = rowArray[index];
      });

      totalRows += 1;
      if (isRowEmpty(rowData)) {
        continue;
      }

      const rowErrors = validateRow(rowData, rowNumber);
      if (rowErrors.length) {
        errors.push({ row_number: rowNumber, errors: rowErrors });
        continue;
      }

      batch.push({ rowNumber, data: rowData });
      if (batch.length >= BATCH_SIZE) {
        const batchStats = await insertBatch(batch, req.file.originalname);
        inserted += batchStats.inserted;
        duplicates += batchStats.duplicates;
        errors.push(...batchStats.errors);
        batch.length = 0;
      }
    }

    if (batch.length) {
      const batchStats = await insertBatch(batch, req.file.originalname);
      inserted += batchStats.inserted;
      duplicates += batchStats.duplicates;
      errors.push(...batchStats.errors);
    }

    const processingTimeSeconds = (Date.now() - startTime) / 1000;

    return res.json({
      success: true,
      message: 'Import completed successfully',
      file_name: req.file.originalname,
      file_size: req.file.size,
      total_rows: totalRows,
      inserted,
      duplicates,
      rejected: errors.length,
      errors,
      processing_time_seconds: Number(processingTimeSeconds.toFixed(2)),
    });
  } catch (error) {
    return res.status(500).json({
      message: error instanceof Error ? error.message : 'Error al procesar el archivo',
    });
  } finally {
    fs.unlink(filePath, () => {});
  }
});

app.get('/api/v1/documentos', async (req: Request, res: Response) => {
  const skip = Number(req.query.skip || 0);
  const limit = Number(req.query.limit || 50);
  const cufe_cude = req.query.cufe_cude ? String(req.query.cufe_cude) : null;
  const nit_emisor = req.query.nit_emisor ? Number(req.query.nit_emisor) : null;
  const nit_receptor = req.query.nit_receptor ? Number(req.query.nit_receptor) : null;
  const estado = req.query.estado ? String(req.query.estado) : null;

  const where: string[] = [];
  const values: Array<string | number> = [];

  if (cufe_cude) {
    where.push('cufe_cude = ?');
    values.push(cufe_cude);
  }
  if (Number.isFinite(nit_emisor)) {
    where.push('nit_emisor = ?');
    values.push(nit_emisor as number);
  }
  if (Number.isFinite(nit_receptor)) {
    where.push('nit_receptor = ?');
    values.push(nit_receptor as number);
  }
  if (estado) {
    where.push('estado = ?');
    values.push(estado);
  }

  const whereSql = where.length ? `WHERE ${where.join(' AND ')}` : '';

  try {
    const [countRows] = await pool.query(
      `SELECT COUNT(*) as total FROM documentos_dian ${whereSql}`,
      values
    );
    const total = (countRows as Array<{ total: number }>)[0]?.total || 0;

    const [items] = await pool.query(
      `SELECT * FROM documentos_dian ${whereSql} ORDER BY id DESC LIMIT ? OFFSET ?`,
      [...values, limit, skip]
    );

    return res.json({
      items,
      total,
      skip,
      limit,
    });
  } catch (error) {
    return res.status(500).json({
      message: error instanceof Error ? error.message : 'Error al cargar documentos',
    });
  }
});

app.get('/api/v1/documentos/resumen', async (req: Request, res: Response) => {
  const empresa = req.query.empresa ? String(req.query.empresa) : null;
  const grupo = req.query.grupo ? String(req.query.grupo) : null;
  const tipo_documento = req.query.tipo_documento ? String(req.query.tipo_documento) : null;
  const fecha_desde = req.query.fecha_desde ? String(req.query.fecha_desde) : null;
  const fecha_hasta = req.query.fecha_hasta ? String(req.query.fecha_hasta) : null;

  const where: string[] = [];
  const values: Array<string> = [];

  if (empresa) {
    where.push('nombre_emisor = ?');
    values.push(empresa);
  }
  if (grupo) {
    where.push('grupo = ?');
    values.push(grupo);
  }
  if (tipo_documento) {
    where.push('tipo_documento = ?');
    values.push(tipo_documento);
  }
  if (fecha_desde) {
    where.push('fecha_emision >= ?');
    values.push(fecha_desde);
  }
  if (fecha_hasta) {
    where.push('fecha_emision <= ?');
    values.push(fecha_hasta);
  }

  const whereSql = where.length ? `WHERE ${where.join(' AND ')}` : '';
  try {
    const [rows] = await pool.query(
      `SELECT
        nombre_emisor AS empresa,
        grupo AS grupo,
        tipo_documento AS tipo_documento,
        SUM(iva) AS iva,
        SUM(ica) AS ica,
        SUM(ic) AS ic,
        SUM(inc) AS inc,
        SUM(timbre) AS timbre,
        SUM(inc_bolsas) AS inc_bolsas,
        SUM(in_carbono) AS in_carbono,
        SUM(in_combustibles) AS in_combustibles,
        SUM(ic_datos) AS ic_datos,
        SUM(icl) AS icl,
        SUM(inpp) AS inpp,
        SUM(ibua) AS ibua,
        SUM(icui) AS icui,
        SUM(rete_iva) AS rete_iva,
        SUM(rete_renta) AS rete_renta,
        SUM(rete_ica) AS rete_ica,
        SUM(total) AS total
      FROM documentos_dian
      ${whereSql}
      GROUP BY nombre_emisor, grupo, tipo_documento
      ORDER BY nombre_emisor ASC, grupo ASC, tipo_documento ASC`
      ,
      values
    );

    const items = (rows as Array<Record<string, unknown>>).map((row) => {
      const toNumber = (value: unknown) => {
        const parsed = Number(value ?? 0);
        return Number.isFinite(parsed) ? parsed : 0;
      };

      const iva = toNumber(row.iva);
      const ica = toNumber(row.ica);
      const ic = toNumber(row.ic);
      const inc = toNumber(row.inc);
      const timbre = toNumber(row.timbre);
      const inc_bolsas = toNumber(row.inc_bolsas);
      const in_carbono = toNumber(row.in_carbono);
      const in_combustibles = toNumber(row.in_combustibles);
      const ic_datos = toNumber(row.ic_datos);
      const icl = toNumber(row.icl);
      const inpp = toNumber(row.inpp);
      const ibua = toNumber(row.ibua);
      const icui = toNumber(row.icui);
      const rete_iva = toNumber(row.rete_iva);
      const rete_renta = toNumber(row.rete_renta);
      const rete_ica = toNumber(row.rete_ica);
      const total = toNumber(row.total);

      const total_otros =
        ica +
        ic +
        timbre +
        inc +
        inc_bolsas +
        in_carbono +
        in_combustibles +
        ic_datos +
        icl +
        inpp +
        ibua +
        icui;
      const total_renta = rete_iva + rete_renta + rete_ica;
      const subtotal = total - total_renta - total_otros - iva;

      return {
        empresa: row.empresa ?? null,
        tipo_documento: row.tipo_documento ?? null,
        grupo: row.grupo ?? null,
        subtotal: subtotal.toFixed(2),
        iva: iva.toFixed(2),
        otros: total_otros.toFixed(2),
        retenciones: total_renta.toFixed(2),
        total: total.toFixed(2),
      };
    });

    return res.json({ items });
  } catch (error) {
    return res.status(500).json({
      message: error instanceof Error ? error.message : 'Error al cargar resumen',
    });
  }
});

app.get('/api/v1/health', async (_req: Request, res: Response) => {
  try {
    await pool.query('SELECT 1');
    return res.json({ status: 'ok', database: 'connected', version: '1.0.0' });
  } catch (error) {
    return res.status(500).json({ status: 'error', database: 'unavailable' });
  }
});

app.listen(PORT, () => {
  // eslint-disable-next-line no-console
  console.log(`API running on http://localhost:${PORT}`);
});
