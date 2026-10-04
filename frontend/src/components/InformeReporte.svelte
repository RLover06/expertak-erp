<script>
  import { onMount } from 'svelte';
  import { getInformeReporte } from '../services/api';

  let loading = false;
  let errorMessage = null;
  let rows = [];

  let empresa = '';
  let grupo = '';
  let tipoDocumento = '';
  let fechaDesde = '';
  let fechaHasta = '';

  onMount(async () => {
    await loadReporte();
    const handler = () => loadReporte();
    window.addEventListener('resumen-imported', handler);
    return () => window.removeEventListener('resumen-imported', handler);
  });

  async function loadReporte() {
    try {
      loading = true;
      errorMessage = null;
      const response = await getInformeReporte({
        empresa: empresa || undefined,
        grupo: grupo || undefined,
        tipo_documento: tipoDocumento || undefined,
        fecha_desde: fechaDesde || undefined,
        fecha_hasta: fechaHasta || undefined,
      });
      rows = Array.isArray(response?.rows) ? response.rows : [];
    } catch (err) {
      errorMessage = err?.message || 'Error al cargar informe';
      rows = [];
    } finally {
      loading = false;
    }
  }

  function isTotalRow(row) {
    return row.Empresa && row.Empresa.startsWith('Total Acumulado');
  }
</script>

<section class="informe-section">
  <div class="header">
    <h2>Resumen</h2>
    <button class="btn btn-secondary" on:click={loadReporte} disabled={loading}>
      {#if loading}
        <span class="spinner"></span>
        <span>Actualizando...</span>
      {:else}
        <span>Actualizar</span>
      {/if}
    </button>
  </div>

  {#if errorMessage}
    <div class="error-message">{errorMessage}</div>
  {/if}

  <div class="filters-card">
    <div class="filters-grid">
      <label>
        Empresa
        <input type="text" placeholder="Empresa" bind:value={empresa} />
      </label>
      <label>
        Tipo De Documento
        <input type="text" placeholder="Tipo De Documento" bind:value={tipoDocumento} />
      </label>
      <label>
        Grupo
        <input type="text" placeholder="Grupo" bind:value={grupo} />
      </label>
      <label>
        Fecha desde
        <input type="date" bind:value={fechaDesde} />
      </label>
      <label>
        Fecha hasta
        <input type="date" bind:value={fechaHasta} />
      </label>
    </div>
    <div class="filters-actions">
      <button class="btn btn-secondary" on:click={loadReporte} disabled={loading}>
        {#if loading}
          <span class="spinner"></span>
          <span>Aplicando...</span>
        {:else}
          <span>Aplicar filtros</span>
        {/if}
      </button>
      <button
        class="btn btn-ghost"
        on:click={() => {
          empresa = '';
          grupo = '';
          tipoDocumento = '';
          fechaDesde = '';
          fechaHasta = '';
          loadReporte();
        }}
        disabled={loading}
      >
        Limpiar
      </button>
    </div>
  </div>

  <div class="table-wrapper">
    <table>
      <thead>
        <tr>
          <th>Empresa</th>
          <th>Tipo De Documento</th>
          <th>Grupo</th>
          <th>Subtotal</th>
          <th>IVA</th>
          <th>Total_otros</th>
          <th>Total_renta</th>
          <th>Total</th>
        </tr>
      </thead>
      <tbody>
        {#if loading}
          <tr>
            <td colspan="8" class="loading-cell">Cargando datos...</td>
          </tr>
        {:else if rows.length === 0}
          <tr>
            <td colspan="8" class="empty-cell">No hay datos disponibles.</td>
          </tr>
        {:else}
          {#each rows as row}
            <tr class:total-row={isTotalRow(row)}>
              <td>{row.Empresa}</td>
              <td>{row.Tipo_de_documento}</td>
              <td>{row.Grupo}</td>
              <td class="num">{row.Subtotal}</td>
              <td class="num">{row.IVA}</td>
              <td class="num">{row.Total_otros}</td>
              <td class="num">{row.Total_renta}</td>
              <td class="num">{row.Total}</td>
            </tr>
          {/each}
        {/if}
      </tbody>
    </table>
  </div>
</section>

<style>
  .informe-section {
    margin-top: 2.5rem;
  }

  .header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    margin-bottom: 1rem;
  }

  .filters-card {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 0.75rem;
    padding: 1rem;
    margin-bottom: 1rem;
  }

  .filters-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 1rem;
  }

  label {
    display: flex;
    flex-direction: column;
    font-size: 0.9rem;
    color: #374151;
    gap: 0.35rem;
  }

  input[type='text'],
  input[type='date'] {
    padding: 0.5rem 0.6rem;
    border-radius: 0.5rem;
    border: 1px solid #d1d5db;
    font-size: 0.9rem;
  }

  .filters-actions {
    display: flex;
    gap: 0.5rem;
    margin-top: 1rem;
    justify-content: flex-end;
  }

  .btn-ghost {
    background: #f3f4f6;
    color: #111827;
  }

  h2 {
    font-size: 1.4rem;
    margin: 0;
  }

  .error-message {
    padding: 1rem;
    background: #fee2e2;
    color: #991b1b;
    border: 1px solid #ef4444;
    border-radius: 0.5rem;
    margin-bottom: 1rem;
  }

  .btn {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.6rem 1rem;
    font-size: 0.9rem;
    font-weight: 600;
    border-radius: 0.5rem;
    cursor: pointer;
    border: none;
  }

  .btn-secondary {
    background: #111827;
    color: white;
  }

  .btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .spinner {
    width: 16px;
    height: 16px;
    border: 2px solid rgba(255, 255, 255, 0.3);
    border-top-color: white;
    border-radius: 50%;
    animation: spin 0.6s linear infinite;
  }

  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }

  .table-wrapper {
    overflow-x: auto;
    border: 1px solid #e5e7eb;
    border-radius: 0.5rem;
    background: #fff;
  }

  table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.8rem;
  }

  th,
  td {
    padding: 0.5rem 0.65rem;
    border-bottom: 1px solid #e5e7eb;
    text-align: left;
  }

  td.num {
    text-align: right;
    font-variant-numeric: tabular-nums;
  }

  th {
    background: #f9fafb;
    font-weight: 600;
  }

  tr.total-row {
    background: #eff6ff;
    font-weight: 600;
  }

  tr.total-row td {
    border-top: 2px solid #2563eb;
  }

  .loading-cell,
  .empty-cell {
    text-align: center;
    padding: 1rem;
    color: #6b7280;
  }
</style>
