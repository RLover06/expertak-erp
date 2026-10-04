<script>
  import { onMount } from 'svelte';
  import {
    getEmpresasFE,
    getEmpresaFE,
    getFacturasFE,
    crearBorradorFE,
    enviarBorradorFE,
    corregirFacturaFE,
  } from '../services/api';

  // ── Estado de empresas / credenciales ────────────────────────────────
  let empresas = [];
  let empresasReadyMap = {}; // nit -> listo_para_emitir
  let empresaNit = '';
  let empresaDetalle = null; // incluye .credenciales
  let loadingEmpresas = false;
  let loadingDetalle = false;

  // ── Formulario ────────────────────────────────────────────────────────
  let adquirente = {
    nit: '',
    nombre: '',
    email: '',
    telefono: '',
    direccion: '',
    municipio: '',
    departamento: '',
    tipo_documento: '31',
    municipio_code: '',
    departamento_code: '',
    tax_level_code: 'R-99-PN',
  };
  let items = [nuevoItem()];
  let formaPago = '1'; // 1=contado, 2=crédito
  let medioPago = '10'; // 10=efectivo
  let fechaVencimiento = '';
  let notas = '';
  let modo = 'habilitacion';

  // ── Resultado / mensajes ──────────────────────────────────────────────
  let saving = false;
  let sending = false;
  let resultado = null; // respuesta de borrador o envío
  let errorMsg = null;
  let erroresDian = [];

  // ── Lista de facturas recientes ───────────────────────────────────────
  let facturas = [];
  let loadingFacturas = false;
  let rowBusyId = null;

  function nuevoItem() {
    return {
      descripcion: '',
      cantidad: 1,
      precio_unitario: 0,
      iva_porcentaje: 19,
      descuento: 0,
      codigo_producto: '',
      unidad_medida: 'EA',
    };
  }

  function agregarItem() {
    items = [...items, nuevoItem()];
  }

  function quitarItem(idx) {
    items = items.filter((_, i) => i !== idx);
    if (items.length === 0) items = [nuevoItem()];
  }

  // ── Totales en vivo (referenciales; el backend recalcula en firme) ─────
  function n(v) {
    const x = parseFloat(v);
    return Number.isFinite(x) ? x : 0;
  }
  $: lineas = items.map((it) => {
    const base = n(it.cantidad) * n(it.precio_unitario) - n(it.descuento);
    const baseR = Math.round(base * 100) / 100;
    const iva = Math.round((baseR * n(it.iva_porcentaje)) / 100 * 100) / 100;
    return { base: baseR, iva };
  });
  $: subtotal = lineas.reduce((s, l) => s + l.base, 0);
  $: totalIva = lineas.reduce((s, l) => s + l.iva, 0);
  $: total = subtotal + totalIva;

  $: empresaReady = !!empresaDetalle?.credenciales?.listo_para_emitir;
  $: faltantes = empresaDetalle?.credenciales?.faltantes || [];

  $: formValido =
    empresaNit &&
    adquirente.nit.trim() &&
    adquirente.nombre.trim() &&
    items.some((it) => it.descripcion.trim() && n(it.cantidad) > 0);

  function money(v) {
    const x = typeof v === 'string' ? parseFloat(v) : v;
    if (!Number.isFinite(x)) return '—';
    return x.toLocaleString('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 2 });
  }

  function buildPayload() {
    return {
      empresa_nit: empresaNit,
      adquirente: {
        nit: adquirente.nit.trim(),
        nombre: adquirente.nombre.trim(),
        email: adquirente.email.trim() || null,
        telefono: adquirente.telefono.trim() || null,
        direccion: adquirente.direccion.trim() || null,
        municipio: adquirente.municipio.trim() || null,
        departamento: adquirente.departamento.trim() || null,
        tipo_documento: adquirente.tipo_documento || '31',
        municipio_code: adquirente.municipio_code.trim() || null,
        departamento_code: adquirente.departamento_code.trim() || null,
        tax_level_code: adquirente.tax_level_code || 'R-99-PN',
      },
      items: items
        .filter((it) => it.descripcion.trim())
        .map((it) => ({
          descripcion: it.descripcion.trim(),
          cantidad: n(it.cantidad),
          precio_unitario: n(it.precio_unitario),
          iva_porcentaje: n(it.iva_porcentaje),
          descuento: n(it.descuento),
          codigo_producto: it.codigo_producto.trim() || null,
          unidad_medida: it.unidad_medida || 'EA',
        })),
      forma_pago: formaPago,
      medio_pago: medioPago,
      fecha_vencimiento: fechaVencimiento || null,
      notas: notas.trim() || null,
      modo,
    };
  }

  async function cargarEmpresas() {
    loadingEmpresas = true;
    errorMsg = null;
    try {
      empresas = await getEmpresasFE();
      empresasReadyMap = Object.fromEntries(empresas.map((e) => [e.nit, e.listo_para_emitir]));
      if (!empresaNit && empresas.length) {
        empresaNit = empresas[0].nit;
        await cargarDetalleEmpresa();
      }
    } catch (e) {
      errorMsg = e.message;
    } finally {
      loadingEmpresas = false;
    }
  }

  async function cargarDetalleEmpresa() {
    empresaDetalle = null;
    if (!empresaNit) return;
    loadingDetalle = true;
    try {
      empresaDetalle = await getEmpresaFE(empresaNit);
    } catch (e) {
      errorMsg = e.message;
    } finally {
      loadingDetalle = false;
    }
  }

  async function cargarFacturas() {
    loadingFacturas = true;
    try {
      facturas = await getFacturasFE(50);
    } catch (e) {
      errorMsg = e.message;
    } finally {
      loadingFacturas = false;
    }
  }

  function resetMensajes() {
    errorMsg = null;
    erroresDian = [];
    resultado = null;
  }

  async function guardarBorrador() {
    if (!formValido || saving) return;
    resetMensajes();
    saving = true;
    try {
      resultado = await crearBorradorFE(buildPayload());
      await cargarFacturas();
    } catch (e) {
      errorMsg = e.message;
    } finally {
      saving = false;
    }
  }

  // Enviar = crear borrador con los datos actuales + transmitir ese borrador.
  async function guardarYEnviar() {
    if (!formValido || sending || !empresaReady) return;
    if (modo === 'produccion' && !confirm('Vas a emitir en PRODUCCIÓN (factura con validez fiscal). ¿Continuar?')) {
      return;
    }
    resetMensajes();
    sending = true;
    try {
      const borrador = await crearBorradorFE(buildPayload());
      resultado = await enviarBorradorFE(borrador.factura_id, modo);
      erroresDian = resultado?.errores || [];
      await cargarFacturas();
    } catch (e) {
      errorMsg = e.message;
      erroresDian = Array.isArray(e.detail?.errores) ? e.detail.errores : [];
    } finally {
      sending = false;
    }
  }

  async function enviarFila(f) {
    if (!empresasReadyMap[f.empresa_nit]) return;
    if (f.ambiente === 'produccion' && !confirm('Enviar en PRODUCCIÓN. ¿Continuar?')) return;
    rowBusyId = f.id;
    resetMensajes();
    try {
      resultado = await enviarBorradorFE(f.id, f.ambiente || 'habilitacion');
      erroresDian = resultado?.errores || [];
      await cargarFacturas();
    } catch (e) {
      errorMsg = e.message;
      erroresDian = Array.isArray(e.detail?.errores) ? e.detail.errores : [];
    } finally {
      rowBusyId = null;
    }
  }

  async function corregirFila(f) {
    rowBusyId = f.id;
    resetMensajes();
    try {
      const nueva = await corregirFacturaFE(f.id);
      await cargarFacturas();
      resultado = {
        estado: 'BORRADOR',
        factura_id: nueva.id,
        message: `Se generó el borrador #${nueva.id} a partir de la rechazada #${f.id}. La original sigue RECHAZADA.`,
      };
    } catch (e) {
      errorMsg = e.message;
    } finally {
      rowBusyId = null;
    }
  }

  function estadoClase(estado) {
    return 'badge badge-' + (estado || '').toLowerCase();
  }

  onMount(async () => {
    await cargarEmpresas();
    await cargarFacturas();
  });
</script>

<div class="fe-form">
  <header class="fe-header">
    <h2>Facturación electrónica</h2>
    <p class="fe-sub">
      Crea y revisa borradores aunque la empresa todavía no tenga credenciales DIAN. El envío
      real se habilita cuando el certificado y las credenciales estén cargados.
    </p>
  </header>

  {#if errorMsg}
    <div class="alert alert-error">
      <strong>Error:</strong> {errorMsg}
      {#if erroresDian.length}
        <ul>
          {#each erroresDian as err}<li>{err}</li>{/each}
        </ul>
      {/if}
    </div>
  {/if}

  {#if resultado}
    <div class="alert alert-success">
      <div class="result-line">
        <span class={estadoClase(resultado.estado)}>{resultado.estado}</span>
        <strong>{resultado.message}</strong>
      </div>
      {#if resultado.factura_numero}
        <div class="result-meta">
          Nº: <code>{resultado.factura_numero}</code>
          {#if resultado.total} · Total: {money(resultado.total)}{/if}
          {#if resultado.cufe} · CUFE: <code class="cufe">{resultado.cufe}</code>{/if}
        </div>
      {/if}
    </div>
  {/if}

  <!-- ── Empresa emisora + credenciales ─────────────────────────────── -->
  <section class="card">
    <h3>Empresa emisora</h3>
    <div class="grid grid-2">
      <label>
        Empresa
        <select bind:value={empresaNit} on:change={cargarDetalleEmpresa} disabled={loadingEmpresas}>
          {#if !empresas.length}
            <option value="">— Sin empresas en fe_empresas_config —</option>
          {/if}
          {#each empresas as e}
            <option value={e.nit}>{e.razon_social || e.nit} ({e.nit}){e.listo_para_emitir ? '' : ' ⚠'}</option>
          {/each}
        </select>
      </label>
      <label>
        Ambiente
        <select bind:value={modo}>
          <option value="habilitacion">Habilitación (pruebas)</option>
          <option value="produccion">Producción</option>
        </select>
      </label>
    </div>

    {#if loadingDetalle}
      <p class="muted">Cargando credenciales…</p>
    {:else if empresaDetalle}
      {#if empresaReady}
        <div class="banner banner-ok">
          ✓ Empresa lista para emitir. Prefijo <code>{empresaDetalle.prefijo}</code>, resolución
          <code>{empresaDetalle.resolucion_numero}</code>.
        </div>
      {:else}
        <div class="banner banner-warn">
          <strong>⚠ Esta empresa aún no puede emitir a la DIAN.</strong>
          Puedes crear y revisar borradores sin problema; el envío real se habilitará cuando
          cargues en <code>fe_empresas_config</code>:
          <ul>
            {#each faltantes as f}<li>{f}</li>{/each}
          </ul>
        </div>
      {/if}
    {/if}
  </section>

  <!-- ── Adquirente ─────────────────────────────────────────────────── -->
  <section class="card">
    <h3>Adquirente (cliente)</h3>
    <div class="grid grid-3">
      <label>NIT / Documento *<input type="text" bind:value={adquirente.nit} placeholder="900123456" /></label>
      <label class="col-span-2">Nombre / Razón social *<input type="text" bind:value={adquirente.nombre} /></label>
      <label>Tipo documento
        <select bind:value={adquirente.tipo_documento}>
          <option value="31">31 - NIT</option>
          <option value="13">13 - Cédula</option>
          <option value="22">22 - Cédula extranjería</option>
          <option value="41">41 - Pasaporte</option>
        </select>
      </label>
      <label>Email<input type="email" bind:value={adquirente.email} /></label>
      <label>Teléfono<input type="text" bind:value={adquirente.telefono} /></label>
      <label class="col-span-3">Dirección<input type="text" bind:value={adquirente.direccion} /></label>
      <label>Ciudad / Municipio<input type="text" bind:value={adquirente.municipio} /></label>
      <label>Cód. municipio (DANE)<input type="text" bind:value={adquirente.municipio_code} placeholder="11001" /></label>
      <label>Cód. depto.<input type="text" bind:value={adquirente.departamento_code} placeholder="11" /></label>
    </div>
  </section>

  <!-- ── Ítems ──────────────────────────────────────────────────────── -->
  <section class="card">
    <div class="card-head">
      <h3>Ítems</h3>
      <button type="button" class="btn btn-light" on:click={agregarItem}>+ Agregar ítem</button>
    </div>
    <div class="items-table">
      <div class="items-row items-head">
        <span>Descripción</span>
        <span>Cantidad</span>
        <span>Precio unit.</span>
        <span>Desc.</span>
        <span>IVA %</span>
        <span>Subtotal</span>
        <span></span>
      </div>
      {#each items as it, idx}
        <div class="items-row">
          <input type="text" bind:value={it.descripcion} placeholder="Descripción" />
          <input type="number" min="0" step="any" bind:value={it.cantidad} />
          <input type="number" min="0" step="any" bind:value={it.precio_unitario} />
          <input type="number" min="0" step="any" bind:value={it.descuento} />
          <input type="number" min="0" step="any" bind:value={it.iva_porcentaje} />
          <span class="cell-sub">{money(lineas[idx]?.base)}</span>
          <button type="button" class="btn-icon" title="Quitar" on:click={() => quitarItem(idx)}>✕</button>
        </div>
      {/each}
    </div>

    <div class="grid grid-3 pago-row">
      <label>Forma de pago
        <select bind:value={formaPago}>
          <option value="1">1 - Contado</option>
          <option value="2">2 - Crédito</option>
        </select>
      </label>
      <label>Medio de pago
        <select bind:value={medioPago}>
          <option value="10">10 - Efectivo</option>
          <option value="42">42 - Transferencia</option>
          <option value="48">48 - Tarjeta crédito</option>
          <option value="49">49 - Tarjeta débito</option>
        </select>
      </label>
      <label>Vencimiento<input type="date" bind:value={fechaVencimiento} /></label>
      <label class="col-span-3">Notas<input type="text" bind:value={notas} /></label>
    </div>

    <div class="totals">
      <div><span>Subtotal</span><strong>{money(subtotal)}</strong></div>
      <div><span>IVA</span><strong>{money(totalIva)}</strong></div>
      <div class="grand"><span>Total</span><strong>{money(total)}</strong></div>
      <p class="muted small">Totales referenciales; el backend los recalcula con redondeo normativo (§8).</p>
    </div>
  </section>

  <!-- ── Acciones ───────────────────────────────────────────────────── -->
  <section class="actions">
    <button type="button" class="btn btn-primary" disabled={!formValido || saving} on:click={guardarBorrador}>
      {saving ? 'Guardando…' : 'Guardar borrador'}
    </button>

    <div class="send-wrap">
      <button
        type="button"
        class="btn btn-send"
        disabled={!formValido || sending || !empresaReady}
        title={empresaReady ? 'Transmitir a la DIAN' : 'Faltan credenciales DIAN para esta empresa'}
        on:click={guardarYEnviar}
      >
        {sending ? 'Enviando…' : `Enviar a DIAN (${modo})`}
      </button>
      {#if empresaDetalle && !empresaReady}
        <span class="send-hint">Deshabilitado: la empresa no tiene credenciales/certificado cargados.</span>
      {/if}
    </div>
  </section>

  <!-- ── Facturas / borradores recientes ────────────────────────────── -->
  <section class="card">
    <div class="card-head">
      <h3>Facturas y borradores recientes</h3>
      <button type="button" class="btn btn-light" on:click={cargarFacturas} disabled={loadingFacturas}>
        {loadingFacturas ? 'Actualizando…' : 'Actualizar'}
      </button>
    </div>
    {#if !facturas.length}
      <p class="muted">Aún no hay facturas ni borradores.</p>
    {:else}
      <table class="fe-table">
        <thead>
          <tr><th>#</th><th>Estado</th><th>Empresa</th><th>Adquirente</th><th>Nº</th><th>Total</th><th>Acciones</th></tr>
        </thead>
        <tbody>
          {#each facturas as f}
            <tr>
              <td>{f.id}</td>
              <td><span class={estadoClase(f.estado)}>{f.estado}</span></td>
              <td class="mono">{f.empresa_nit}</td>
              <td>{f.adquirente_nombre || f.adquirente_nit || '—'}</td>
              <td class="mono">{f.factura_numero || '—'}</td>
              <td>{money(f.total)}</td>
              <td class="row-actions">
                {#if f.estado === 'BORRADOR'}
                  <button
                    type="button"
                    class="btn btn-xs btn-send"
                    disabled={rowBusyId === f.id || !empresasReadyMap[f.empresa_nit]}
                    title={empresasReadyMap[f.empresa_nit] ? 'Enviar a la DIAN' : 'Empresa sin credenciales DIAN'}
                    on:click={() => enviarFila(f)}
                  >
                    {rowBusyId === f.id ? '…' : 'Enviar'}
                  </button>
                {:else if f.estado === 'RECHAZADA'}
                  <button
                    type="button"
                    class="btn btn-xs btn-light"
                    disabled={rowBusyId === f.id}
                    on:click={() => corregirFila(f)}
                  >
                    {rowBusyId === f.id ? '…' : 'Corregir'}
                  </button>
                {:else}
                  <span class="muted small">—</span>
                {/if}
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    {/if}
  </section>
</div>

<style>
  .fe-form { display: flex; flex-direction: column; gap: 1.25rem; }
  .fe-header h2 { margin: 0 0 0.25rem; font-size: 1.6rem; color: #111827; }
  .fe-sub { margin: 0; color: #6b7280; font-size: 0.95rem; }

  .card {
    background: #fff;
    border: 1px solid #e5e7eb;
    border-radius: 0.75rem;
    padding: 1.25rem 1.5rem;
  }
  .card h3 { margin: 0 0 1rem; font-size: 1.1rem; color: #111827; }
  .card-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 1rem; }
  .card-head h3 { margin: 0; }

  .grid { display: grid; gap: 0.85rem 1rem; }
  .grid-2 { grid-template-columns: repeat(2, 1fr); }
  .grid-3 { grid-template-columns: repeat(3, 1fr); }
  .col-span-2 { grid-column: span 2; }
  .col-span-3 { grid-column: 1 / -1; }

  label { display: flex; flex-direction: column; gap: 0.3rem; font-size: 0.82rem; font-weight: 600; color: #374151; }
  input, select {
    padding: 0.5rem 0.6rem;
    border: 1px solid #d1d5db;
    border-radius: 0.45rem;
    font-size: 0.9rem;
    font-weight: 400;
    color: #111827;
    background: #fff;
  }
  input:focus, select:focus { outline: 2px solid #93c5fd; border-color: #3b82f6; }

  .banner { margin-top: 1rem; padding: 0.85rem 1rem; border-radius: 0.5rem; font-size: 0.9rem; }
  .banner ul { margin: 0.4rem 0 0; padding-left: 1.1rem; }
  .banner-ok { background: #ecfdf5; color: #065f46; border: 1px solid #a7f3d0; }
  .banner-warn { background: #fffbeb; color: #92400e; border: 1px solid #fcd34d; }

  .items-table { display: flex; flex-direction: column; gap: 0.4rem; }
  .items-row {
    display: grid;
    grid-template-columns: 2.4fr 0.8fr 1fr 0.8fr 0.7fr 1fr 32px;
    gap: 0.5rem;
    align-items: center;
  }
  .items-head { font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.03em; color: #6b7280; font-weight: 700; }
  .items-head span { padding-left: 0.2rem; }
  .cell-sub { font-size: 0.85rem; text-align: right; color: #374151; }
  .btn-icon { border: none; background: #f3f4f6; color: #6b7280; border-radius: 0.4rem; cursor: pointer; height: 32px; }
  .btn-icon:hover { background: #fee2e2; color: #b91c1c; }
  .pago-row { margin-top: 1.25rem; }

  .totals { margin-top: 1.25rem; display: flex; flex-direction: column; align-items: flex-end; gap: 0.25rem; }
  .totals > div { display: flex; gap: 1rem; min-width: 240px; justify-content: space-between; }
  .totals span { color: #6b7280; }
  .totals .grand { font-size: 1.15rem; border-top: 1px solid #e5e7eb; padding-top: 0.4rem; margin-top: 0.2rem; }
  .totals .grand strong { color: #111827; }

  .actions { display: flex; align-items: center; gap: 1rem; flex-wrap: wrap; }
  .send-wrap { display: flex; flex-direction: column; gap: 0.2rem; }
  .send-hint { font-size: 0.75rem; color: #92400e; }

  .btn { padding: 0.6rem 1.2rem; border-radius: 0.5rem; border: none; font-size: 0.9rem; font-weight: 600; cursor: pointer; }
  .btn:disabled { opacity: 0.5; cursor: not-allowed; }
  .btn-primary { background: #2563eb; color: #fff; }
  .btn-primary:not(:disabled):hover { background: #1d4ed8; }
  .btn-send { background: #059669; color: #fff; }
  .btn-send:not(:disabled):hover { background: #047857; }
  .btn-light { background: #f3f4f6; color: #374151; }
  .btn-light:not(:disabled):hover { background: #e5e7eb; }
  .btn-xs { padding: 0.3rem 0.7rem; font-size: 0.78rem; }

  .alert { padding: 0.85rem 1rem; border-radius: 0.5rem; font-size: 0.9rem; }
  .alert ul { margin: 0.4rem 0 0; padding-left: 1.1rem; }
  .alert-error { background: #fef2f2; color: #991b1b; border: 1px solid #fecaca; }
  .alert-success { background: #f0fdf4; color: #14532d; border: 1px solid #bbf7d0; }
  .result-line { display: flex; align-items: center; gap: 0.6rem; }
  .result-meta { margin-top: 0.4rem; font-size: 0.85rem; }
  code { background: rgba(0,0,0,0.06); padding: 0.05rem 0.3rem; border-radius: 0.25rem; }
  code.cufe { word-break: break-all; font-size: 0.75rem; }

  .fe-table { width: 100%; border-collapse: collapse; font-size: 0.87rem; }
  .fe-table th, .fe-table td { padding: 0.5rem 0.6rem; text-align: left; border-bottom: 1px solid #f0f0f0; }
  .fe-table th { font-size: 0.72rem; text-transform: uppercase; color: #6b7280; letter-spacing: 0.03em; }
  .mono, .row-actions { white-space: nowrap; }
  .mono { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 0.8rem; }

  .badge { display: inline-block; padding: 0.15rem 0.55rem; border-radius: 999px; font-size: 0.72rem; font-weight: 700; }
  .badge-borrador { background: #e5e7eb; color: #374151; }
  .badge-pendiente { background: #dbeafe; color: #1e40af; }
  .badge-enviada { background: #e0e7ff; color: #3730a3; }
  .badge-validada { background: #d1fae5; color: #065f46; }
  .badge-rechazada { background: #fee2e2; color: #991b1b; }
  .badge-error { background: #ffedd5; color: #9a3412; }
  .badge-offline { background: #fef3c7; color: #92400e; }

  .muted { color: #6b7280; }
  .small { font-size: 0.78rem; }

  @media (max-width: 820px) {
    .grid-2, .grid-3 { grid-template-columns: 1fr; }
    .col-span-2, .col-span-3 { grid-column: auto; }
    .items-row { grid-template-columns: 1fr 1fr; }
    .items-head { display: none; }
  }
</style>
