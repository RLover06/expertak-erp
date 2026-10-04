<script>
  import { onMount } from 'svelte';
  import { getPivotOptions, getPivotData } from '../services/api';

  let optionsLoading = false;
  let pivotLoading = false;
  let errorMessage = null;
  let options = { empresas: [], terceros: [], cuentas: [], periodos: [] };
  let pivotData = { items: [], group_by: [] };

  let empresaId = '';
  let terceroId = '';
  let cuenta = '';
  let periodo = '';
  let fechaDesde = '';
  let fechaHasta = '';

  const groupBy = 'empresa,tercero,cuenta,periodo';

  onMount(async () => {
    await loadOptions();
    await loadPivot();
  });

  async function loadOptions() {
    try {
      optionsLoading = true;
      errorMessage = null;
      options = await getPivotOptions();
    } catch (err) {
      errorMessage = err?.message || 'Error al cargar filtros';
    } finally {
      optionsLoading = false;
    }
  }

  async function loadPivot() {
    try {
      pivotLoading = true;
      errorMessage = null;
      pivotData = await getPivotData({
        empresa_id: empresaId || undefined,
        tercero_id: terceroId || undefined,
        cuenta: cuenta || undefined,
        periodo: periodo || undefined,
        fecha_desde: fechaDesde || undefined,
        fecha_hasta: fechaHasta || undefined,
        group_by: groupBy,
      });
    } catch (err) {
      errorMessage = err?.message || 'Error al cargar tabla dinamica';
    } finally {
      pivotLoading = false;
    }
  }

  function resetFilters() {
    empresaId = '';
    terceroId = '';
    cuenta = '';
    periodo = '';
    fechaDesde = '';
    fechaHasta = '';
    loadPivot();
  }
</script>

<section class="pivot-section">
  <h2>Tabla dinamica web</h2>

  {#if errorMessage}
    <div class="error-message">
      {errorMessage}
    </div>
  {/if}

  <div class="filters-card">
    <div class="filters-header">
      <h3>Filtros</h3>
      <div class="filters-actions">
        <button class="btn btn-secondary" on:click={loadPivot} disabled={pivotLoading || optionsLoading}>
          {#if pivotLoading}
            <span class="spinner"></span>
            <span>Actualizando...</span>
          {:else}
            <span>Aplicar filtros</span>
          {/if}
        </button>
        <button class="btn btn-ghost" on:click={resetFilters} disabled={pivotLoading}>
          Limpiar
        </button>
      </div>
    </div>

    <div class="filters-grid">
      <label>
        Empresa
        <select bind:value={empresaId} disabled={optionsLoading}>
          <option value="">Todas</option>
          {#each options.empresas as empresa}
            <option value={empresa.id}>{empresa.nombre}</option>
          {/each}
        </select>
      </label>

      <label>
        Tercero
        <select bind:value={terceroId} disabled={optionsLoading}>
          <option value="">Todos</option>
          {#each options.terceros as tercero}
            <option value={tercero.id}>{tercero.nombre}</option>
          {/each}
        </select>
      </label>

      <label>
        Cuenta contable
        <select bind:value={cuenta} disabled={optionsLoading}>
          <option value="">Todas</option>
          {#each options.cuentas as item}
            <option value={item}>{item}</option>
          {/each}
        </select>
      </label>

      <label>
        Periodo
        <select bind:value={periodo} disabled={optionsLoading}>
          <option value="">Todos</option>
          {#each options.periodos as item}
            <option value={item}>{item}</option>
          {/each}
        </select>
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
  </div>

  <div class="pivot-card">
    <div class="pivot-header">
      <h3>Resumen</h3>
      <span class="badge">{pivotData.items.length} filas</span>
    </div>

    <div class="table-wrapper">
      <table>
        <thead>
          <tr>
            <th>Empresa</th>
            <th>Tercero</th>
            <th>Cuenta</th>
            <th>Periodo</th>
            <th>Debito</th>
            <th>Credito</th>
            <th>Movimientos</th>
          </tr>
        </thead>
        <tbody>
          {#if pivotLoading}
            <tr>
              <td colspan="7" class="loading-cell">Cargando datos...</td>
            </tr>
          {:else if pivotData.items.length === 0}
            <tr>
              <td colspan="7" class="empty-cell">No hay datos para los filtros seleccionados.</td>
            </tr>
          {:else}
            {#each pivotData.items as item}
              <tr>
                <td>{item.empresa}</td>
                <td>{item.tercero}</td>
                <td>{item.cuenta}</td>
                <td>{item.periodo ?? '-'}</td>
                <td>{item.debito}</td>
                <td>{item.credito}</td>
                <td>{item.movimientos}</td>
              </tr>
            {/each}
          {/if}
        </tbody>
      </table>
    </div>
  </div>
</section>

<style>
  .pivot-section {
    margin-top: 2.5rem;
  }

  h2 {
    font-size: 1.5rem;
    margin-bottom: 1.5rem;
    color: #111827;
  }

  h3 {
    font-size: 1.125rem;
    margin: 0;
    color: #111827;
  }

  .error-message {
    padding: 1rem;
    background: #fee2e2;
    color: #991b1b;
    border: 1px solid #ef4444;
    border-radius: 0.5rem;
    margin-bottom: 1rem;
  }

  .filters-card,
  .pivot-card {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 0.75rem;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
  }

  .filters-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 1rem;
    gap: 1rem;
    flex-wrap: wrap;
  }

  .filters-actions {
    display: flex;
    gap: 0.5rem;
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

  select,
  input[type="date"] {
    padding: 0.5rem 0.6rem;
    border-radius: 0.5rem;
    border: 1px solid #d1d5db;
    font-size: 0.9rem;
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
    color: #fff;
  }

  .btn-ghost {
    background: #f3f4f6;
    color: #111827;
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
    to { transform: rotate(360deg); }
  }

  .pivot-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 1rem;
  }

  .badge {
    background: #e0e7ff;
    color: #1e3a8a;
    padding: 0.2rem 0.6rem;
    border-radius: 999px;
    font-size: 0.8rem;
    font-weight: 600;
  }

  .table-wrapper {
    overflow-x: auto;
    border: 1px solid #e5e7eb;
    border-radius: 0.5rem;
  }

  table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.85rem;
  }

  th,
  td {
    padding: 0.6rem 0.75rem;
    border-bottom: 1px solid #e5e7eb;
    text-align: left;
  }

  th {
    background: #f9fafb;
    font-weight: 600;
  }

  .loading-cell,
  .empty-cell {
    text-align: center;
    padding: 1rem;
    color: #6b7280;
  }
</style>
