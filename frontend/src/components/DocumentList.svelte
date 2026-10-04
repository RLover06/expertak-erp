<script>
  import { onMount } from 'svelte';
  import { getDocumentos } from '../services/api';

  let documentos = [];
  let total = 0;
  let skip = 0;
  let limit = 20;
  let loading = false;
  let loadError = null;

  let filters = {
    cufe_cude: '',
    nit_emisor: '',
    nit_receptor: '',
    estado: ''
  };

  const canPrev = () => skip > 0;
  const canNext = () => skip + limit < total;

  async function loadDocumentos() {
    loading = true;
    loadError = null;

    try {
      // FastAPI: GET /api/v1/documentos
      const response = await getDocumentos({
        skip,
        limit,
        cufe_cude: filters.cufe_cude || undefined,
        nit_emisor: filters.nit_emisor ? Number(filters.nit_emisor) : undefined,
        nit_receptor: filters.nit_receptor ? Number(filters.nit_receptor) : undefined,
        estado: filters.estado || undefined
      });
      documentos = response.items || [];
      total = response.total || 0;
    } catch (err) {
      loadError = err?.message || 'Error al cargar documentos';
    } finally {
      loading = false;
    }
  }

  function applyFilters() {
    skip = 0;
    loadDocumentos();
  }

  function clearFilters() {
    filters = { cufe_cude: '', nit_emisor: '', nit_receptor: '', estado: '' };
    applyFilters();
  }

  function nextPage() {
    if (!canNext()) return;
    skip += limit;
    loadDocumentos();
  }

  function prevPage() {
    if (!canPrev()) return;
    skip = Math.max(0, skip - limit);
    loadDocumentos();
  }

  onMount(() => {
    loadDocumentos();
  });
</script>

<section class="documentos-section">
  <header class="section-header">
    <h2>Documentos registrados</h2>
    <button class="btn btn-secondary" on:click={loadDocumentos} disabled={loading}>
      {#if loading}Cargando...{:else}Actualizar{/if}
    </button>
  </header>

  <div class="filters">
    <input
      type="text"
      placeholder="CUFE/CUDE"
      bind:value={filters.cufe_cude}
    />
    <input
      type="text"
      placeholder="NIT emisor"
      bind:value={filters.nit_emisor}
    />
    <input
      type="text"
      placeholder="NIT receptor"
      bind:value={filters.nit_receptor}
    />
    <input
      type="text"
      placeholder="Estado"
      bind:value={filters.estado}
    />
    <div class="filter-actions">
      <button class="btn btn-primary" on:click={applyFilters} disabled={loading}>
        Buscar
      </button>
      <button class="btn btn-ghost" on:click={clearFilters} disabled={loading}>
        Limpiar
      </button>
    </div>
  </div>

  {#if loadError}
    <div class="error-message">{loadError}</div>
  {/if}

  <div class="table-wrapper">
    <table>
      <thead>
        <tr>
          <th>ID</th>
          <th>CUFE/CUDE</th>
          <th>Tipo</th>
          <th>Emisor</th>
          <th>Receptor</th>
          <th>Total</th>
          <th>Estado</th>
        </tr>
      </thead>
      <tbody>
        {#if !loading && documentos.length === 0}
          <tr>
            <td colspan="7" class="empty-row">No hay documentos para mostrar.</td>
          </tr>
        {:else}
          {#each documentos as doc}
            <tr>
              <td>{doc.id}</td>
              <td>{doc.cufe_cude}</td>
              <td>{doc.tipo_documento}</td>
              <td>{doc.nit_emisor || '-'}</td>
              <td>{doc.nit_receptor || '-'}</td>
              <td>{doc.total}</td>
              <td>{doc.estado || '-'}</td>
            </tr>
          {/each}
        {/if}
      </tbody>
    </table>
  </div>

  <footer class="pagination">
    <span>Mostrando {skip + 1}-{Math.min(skip + limit, total)} de {total}</span>
    <div class="pagination-actions">
      <button class="btn btn-ghost" on:click={prevPage} disabled={!canPrev() || loading}>
        Anterior
      </button>
      <button class="btn btn-ghost" on:click={nextPage} disabled={!canNext() || loading}>
        Siguiente
      </button>
    </div>
  </footer>
</section>

<style>
  .documentos-section {
    margin-top: 2rem;
    padding-top: 2rem;
    border-top: 1px solid #e5e7eb;
  }

  .section-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 1.5rem;
    gap: 1rem;
  }

  .filters {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: 0.75rem;
    margin-bottom: 1rem;
  }

  .filters input {
    padding: 0.6rem 0.75rem;
    border: 1px solid #e5e7eb;
    border-radius: 0.5rem;
    font-size: 0.95rem;
  }

  .filter-actions {
    display: flex;
    gap: 0.5rem;
    align-items: center;
  }

  .error-message {
    padding: 0.75rem 1rem;
    background: #fee2e2;
    color: #991b1b;
    border: 1px solid #ef4444;
    border-radius: 0.5rem;
    margin-bottom: 1rem;
  }

  .table-wrapper {
    overflow-x: auto;
    border: 1px solid #e5e7eb;
    border-radius: 0.5rem;
  }

  table {
    width: 100%;
    border-collapse: collapse;
    background: #fff;
  }

  th,
  td {
    padding: 0.75rem;
    text-align: left;
    border-bottom: 1px solid #e5e7eb;
    font-size: 0.9rem;
  }

  th {
    background: #f9fafb;
    font-weight: 600;
  }

  .empty-row {
    text-align: center;
    color: #6b7280;
    padding: 1.5rem;
  }

  .pagination {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-top: 1rem;
    gap: 1rem;
    color: #6b7280;
    font-size: 0.9rem;
  }

  .pagination-actions {
    display: flex;
    gap: 0.5rem;
  }

  .btn {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 0.9rem;
    font-size: 0.9rem;
    font-weight: 600;
    border: none;
    border-radius: 0.5rem;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .btn-primary {
    background: #2563eb;
    color: white;
  }

  .btn-secondary {
    background: #111827;
    color: white;
  }

  .btn-ghost {
    background: #f3f4f6;
    color: #111827;
  }

  .btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
</style>
