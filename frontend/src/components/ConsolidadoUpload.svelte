<script>
  import { previewExcelFile, importRows, importConsolidadoRows } from '../services/api';

  let importType = 'documentos'; // 'documentos' = Resumen calculado | 'consolidado'
  let selectedFile = null;
  let fileInfo = null;
  let dragOver = false;
  let successMessage = null;
  let errorMessage = null;
  let previewLoading = false;
  let importLoading = false;
  let previewData = null;
  let importResult = null;

  $: canPreview = selectedFile && !previewLoading;
  $: canImport = selectedFile && previewData?.rows?.length > 0 && !importLoading;
  $: previewHeaders = previewData?.headers || [];
  $: previewRows = previewData?.rows ? previewData.rows.slice(0, 50) : [];

  function handleFileSelect(event) {
    const file = event.target.files?.[0];
    if (file) {
      processFile(file);
    }
  }

  function handleDrop(event) {
    event.preventDefault();
    dragOver = false;

    const file = event.dataTransfer?.files?.[0];
    if (file && file.name.endsWith('.xlsx')) {
      processFile(file);
    }
  }

  function handleDragOver(event) {
    event.preventDefault();
    dragOver = true;
  }

  function handleDragLeave() {
    dragOver = false;
  }

  async function processFile(file) {
    if (!file.name.endsWith('.xlsx')) {
      errorMessage = 'Solo se permiten archivos .xlsx';
      successMessage = null;
      return;
    }

    selectedFile = file;
    fileInfo = {
      name: file.name,
      size: formatFileSize(file.size),
    };
    previewData = null;
    importResult = null;
    errorMessage = null;
    successMessage = null;
  }

  async function handlePreview() {
    if (!selectedFile) {
      return;
    }

    try {
      previewLoading = true;
      errorMessage = null;

      const preview = await previewExcelFile(selectedFile);
      previewData = preview;
      importResult = null;
      successMessage = `Archivo previsualizado. Filas: ${preview.rows?.length ?? 0}`;
    } catch (err) {
      const message = err?.message || 'Error al previsualizar';
      errorMessage = message.startsWith('Error al previsualizar')
        ? message
        : `Error al previsualizar: ${message}`;
      successMessage = null;
    } finally {
      previewLoading = false;
    }
  }

  async function handleImport() {
    if (!selectedFile) {
      return;
    }

    try {
      importLoading = true;
      errorMessage = null;

      if (!previewData || !Array.isArray(previewData.rows) || previewData.rows.length === 0) {
        errorMessage = 'Debe previsualizar el archivo antes de importar.';
        importLoading = false;
        return;
      }

      const result = importType === 'consolidado'
        ? await importConsolidadoRows(previewData.rows, selectedFile?.name, previewData.headers)
        : await importRows(previewData.rows, selectedFile?.name);
      importResult = result;
      successMessage = 'Importacion completada correctamente.';
      if (importType === 'documentos' && result?.inserted > 0) {
        window.dispatchEvent(new CustomEvent('resumen-imported'));
      }
    } catch (err) {
      const message = err?.message || 'Error al importar';
      errorMessage = message.startsWith('Error al importar')
        ? message
        : `Error al importar: ${message}`;
      successMessage = null;
    } finally {
      importLoading = false;
    }
  }

  function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
  }

  function resetForm() {
    selectedFile = null;
    fileInfo = null;
    previewData = null;
    importResult = null;
    errorMessage = null;
    successMessage = null;
    previewLoading = false;
    importLoading = false;
  }
</script>

<section class="consolidado-section">
  <h2>Carga de Datos</h2>
  <!-- Selector Documentos FE / Consolidado oculto de momento -->
  <!-- <div class="import-type-selector">
    <label>
      <input type="radio" bind:group={importType} value="documentos" />
      <strong>Documentos FE</strong> (Tipo de documento, Nombre Emisor, Grupo, IVA, Total, etc.) → Se calcula el Resumen automáticamente
    </label>
    <label>
      <input type="radio" bind:group={importType} value="consolidado" />
      <strong>Consolidado</strong> (Empresa, Tercero, Fecha, Cuenta, Débito, Crédito)
    </label>
  </div> -->

  {#if errorMessage}
    <div class="error-message">
      {errorMessage}
    </div>
  {/if}

  {#if successMessage}
    <div class="success-message">
      {successMessage}
    </div>
  {/if}

  <div
    class="drop-zone"
    class:drag-over={dragOver}
    role="button"
    tabindex="0"
    aria-label="Zona de carga de archivo Excel consolidado"
    on:drop={handleDrop}
    on:dragover={handleDragOver}
    on:dragleave={handleDragLeave}
  >
    <input
      type="file"
      id="consolidado-file-input"
      accept=".xlsx"
      on:change={handleFileSelect}
      style="display: none;"
    />

    {#if !selectedFile}
      <label for="consolidado-file-input" class="drop-label">
        <span class="icon">📂</span>
        <span>Haga clic o arrastre un Excel (.xlsx)</span>
      </label>
    {:else}
      <div class="file-selected">
        <div class="file-icon">📄</div>
        <div class="file-details">
          <div class="file-name">{fileInfo.name}</div>
          <div class="file-size">{fileInfo.size}</div>
        </div>
        <button class="btn-remove" on:click={resetForm}>✕</button>
      </div>
    {/if}
  </div>

  <div class="actions">
    <button class="btn btn-secondary" disabled={!canPreview} on:click={handlePreview}>
      {#if previewLoading}
        <span class="spinner"></span>
        <span>Previsualizando...</span>
      {:else}
        <span>Previsualizar</span>
      {/if}
    </button>

    <button class="btn btn-primary" disabled={!canImport} on:click={handleImport}>
      {#if importLoading}
        <span class="spinner"></span>
        <span>Importando...</span>
      {:else}
        <span>Importar</span>
      {/if}
    </button>
  </div>

  {#if importResult}
    <div class="result-summary">
      <h3>Resultado de importacion</h3>
      <div class="summary-grid">
        <div>
          <span class="label">Total filas</span>
          <span class="value">{importResult.total_rows}</span>
        </div>
        <div>
          <span class="label">Insertadas</span>
          <span class="value">{importResult.inserted}</span>
        </div>
        <div>
          <span class="label">Rechazadas</span>
          <span class="value">{importResult.rejected}</span>
        </div>
        <div>
          <span class="label">Tiempo (s)</span>
          <span class="value">{importResult.processing_time_seconds}</span>
        </div>
      </div>
      {#if importResult.errors?.length > 0}
        <div class="errors-detail">
          <h4>Errores de validacion (corregir celdas indicadas)</h4>
          <ul>
            {#each importResult.errors as err}
              <li>
                <strong>Fila {err.row_number}:</strong>
                {#each err.errors as msg}
                  <span class="error-msg">{msg}</span>
                {/each}
              </li>
            {/each}
          </ul>
        </div>
      {/if}
    </div>
  {/if}

  {#if previewData}
    <div class="preview-section">
      <h3>Previsualizacion (primeras 50 filas)</h3>
      <div class="table-wrapper">
        <table>
          <thead>
            <tr>
              {#each previewHeaders as header}
                <th>{header}</th>
              {/each}
            </tr>
          </thead>
          <tbody>
            {#each previewRows as row}
              <tr>
                {#each previewHeaders as header}
                  <td>{row[header] ?? ''}</td>
                {/each}
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
      <p class="preview-note">Mostrando {previewRows.length} de {previewData.rows.length} filas.</p>
    </div>
  {/if}
</section>

<style>
  .consolidado-section {
    margin-bottom: 2.5rem;
  }

  .import-type-selector {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    margin-bottom: 1rem;
    padding: 1rem;
    background: #f9fafb;
    border-radius: 0.5rem;
    border: 1px solid #e5e7eb;
  }

  .import-type-selector label {
    display: flex;
    align-items: flex-start;
    gap: 0.5rem;
    cursor: pointer;
    font-size: 0.9rem;
  }

  h2 {
    font-size: 1.5rem;
    margin-bottom: 1.5rem;
    color: #111827;
  }

  h3 {
    font-size: 1.125rem;
    margin: 1.5rem 0 1rem;
  }

  .error-message {
    padding: 1rem;
    background: #fee2e2;
    color: #991b1b;
    border: 1px solid #ef4444;
    border-radius: 0.5rem;
    margin-bottom: 1rem;
  }

  .success-message {
    padding: 1rem;
    background: #dcfce7;
    color: #166534;
    border: 1px solid #86efac;
    border-radius: 0.5rem;
    margin-bottom: 1rem;
  }

  .drop-zone {
    border: 2px dashed #e5e7eb;
    border-radius: 0.5rem;
    padding: 2.5rem;
    text-align: center;
    background: #f9fafb;
    transition: all 0.3s ease;
    margin-bottom: 1.5rem;
  }

  .drop-zone.drag-over {
    border-color: #2563eb;
    background: #eff6ff;
  }

  .drop-label {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.75rem;
    cursor: pointer;
    color: #6b7280;
  }

  .icon {
    font-size: 2rem;
  }

  .file-selected {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 1rem;
    background: #f0f7ff;
    border-radius: 0.5rem;
  }

  .file-icon {
    font-size: 2rem;
  }

  .file-details {
    flex: 1;
    text-align: left;
  }

  .file-name {
    font-weight: 600;
    color: #111827;
    margin-bottom: 0.25rem;
  }

  .file-size {
    font-size: 0.875rem;
    color: #6b7280;
  }

  .btn-remove {
    background: none;
    border: none;
    font-size: 1.5rem;
    cursor: pointer;
    color: #6b7280;
    padding: 0.5rem;
    line-height: 1;
  }

  .btn-remove:hover {
    color: #ef4444;
  }

  .actions {
    display: flex;
    justify-content: center;
    gap: 0.75rem;
    margin-bottom: 1rem;
  }

  .btn {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1.5rem;
    font-size: 1rem;
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

  .btn:disabled {
    opacity: 0.5;
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

  .result-summary {
    background: #f9fafb;
    border: 1px solid #e5e7eb;
    border-radius: 0.75rem;
    padding: 1rem 1.5rem;
  }

  .summary-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: 1rem;
  }

  .summary-grid .label {
    display: block;
    font-size: 0.8rem;
    color: #6b7280;
    margin-bottom: 0.35rem;
  }

  .summary-grid .value {
    font-weight: 700;
    color: #111827;
  }

  .errors-detail {
    margin-top: 1rem;
    padding: 1rem;
    background: #fef2f2;
    border: 1px solid #fecaca;
    border-radius: 0.5rem;
  }

  .errors-detail h4 {
    font-size: 0.95rem;
    color: #991b1b;
    margin: 0 0 0.75rem;
  }

  .errors-detail ul {
    margin: 0;
    padding-left: 1.25rem;
  }

  .errors-detail li {
    margin-bottom: 0.5rem;
  }

  .errors-detail .error-msg {
    display: block;
    font-size: 0.875rem;
    color: #7f1d1d;
  }

  .preview-section {
    margin-top: 2rem;
    padding-top: 1.5rem;
    border-top: 1px solid #e5e7eb;
  }

  .preview-section .table-wrapper {
    overflow-x: auto;
    overflow-y: auto;
    max-height: 35rem; /* ~15 filas visibles con barra de desplazamiento */
    border: 1px solid #e5e7eb;
    border-radius: 0.5rem;
    background: #fff;
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
    font-size: 0.85rem;
  }

  th,
  td {
    padding: 0.6rem 0.75rem;
    border-bottom: 1px solid #e5e7eb;
    text-align: left;
  }

  .preview-section th {
    background: #f9fafb;
    font-weight: 600;
    position: sticky;
    top: 0;
    z-index: 1;
    box-shadow: 0 1px 0 #e5e7eb;
  }

  th {
    background: #f9fafb;
    font-weight: 600;
  }

  .preview-note {
    font-size: 0.85rem;
    color: #6b7280;
    margin-top: 0.75rem;
  }
</style>
