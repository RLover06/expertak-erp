<script>
  import { importStore, error, excelPreview } from '../stores/importStore';
  import { previewExcelFile, importRows } from '../services/api';

  let selectedFile = null;
  let fileInfo = null;
  let dragOver = false;
  let successMessage = null;
  let previewLoading = false;
  let importLoading = false;
  let previewData = null;

  excelPreview.subscribe((value) => {
    previewData = value;
  });

  $: canPreview = selectedFile && !previewLoading;
  $: canImport = selectedFile && previewData?.rows?.length > 0 && !importLoading;

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
      error.set('Solo se permiten archivos .xlsx');
      successMessage = null;
      return;
    }

    selectedFile = file;
    fileInfo = {
      name: file.name,
      size: formatFileSize(file.size)
    };
    excelPreview.set(null);
    error.set(null);
    successMessage = null;
  }

  async function handlePreview() {
    if (!selectedFile) {
      return;
    }

    try {
      previewLoading = true;
      error.set(null);

      // FastAPI: POST /api/v1/import/preview
      const preview = await previewExcelFile(selectedFile);
      excelPreview.set(preview);
      importStore.set(null);
      successMessage = `Archivo previsualizado. Filas: ${preview.rows?.length ?? 0}`;
    } catch (err) {
      const message = err?.message || 'Error al previsualizar';
      error.set(
        message.startsWith('Error al previsualizar')
          ? message
          : `Error al previsualizar: ${message}`
      );
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
      error.set(null);

      if (!previewData || !Array.isArray(previewData.rows) || previewData.rows.length === 0) {
        error.set('Debe previsualizar el archivo antes de importar.');
        importLoading = false;
        return;
      }

      // FastAPI: POST /api/v1/import
      const result = await importRows(previewData.rows, selectedFile?.name);
      importStore.set(result);
      successMessage = 'Importación completada correctamente.';
    } catch (err) {
      const message = err?.message || 'Error al importar';
      error.set(
        message.startsWith('Error al importar')
          ? message
          : `Error al importar: ${message}`
      );
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
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  }

  function resetForm() {
    selectedFile = null;
    fileInfo = null;
    excelPreview.set(null);
    error.set(null);
    importStore.set(null);
    successMessage = null;
    previewLoading = false;
    importLoading = false;
  }
</script>

<div class="upload-section">
  <h2>Subir Archivo Excel</h2>

  {#if $error}
    <div class="error-message">
      {$error}
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
    aria-label="Zona de carga de archivo Excel"
    on:drop={handleDrop}
    on:dragover={handleDragOver}
    on:dragleave={handleDragLeave}
  >
    <input 
      type="file" 
      id="file-input" 
      accept=".xlsx"
      on:change={handleFileSelect}
      style="display: none;"
    />
    
    {#if !selectedFile}
      <label for="file-input" class="drop-label">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
          <polyline points="17 8 12 3 7 8"></polyline>
          <line x1="12" y1="3" x2="12" y2="15"></line>
        </svg>
        <span>Haga clic o arrastre un archivo Excel (.xlsx) aquí</span>
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
    <button
      class="btn btn-secondary"
      disabled={!canPreview}
      on:click={handlePreview}
    >
      {#if previewLoading}
        <span class="spinner"></span>
        <span>Previsualizando...</span>
      {:else}
        <span>Previsualizar</span>
      {/if}
    </button>

    <button
      class="btn btn-primary"
      disabled={!canImport}
      on:click={handleImport}
    >
      {#if importLoading}
        <span class="spinner"></span>
        <span>Importando...</span>
      {:else}
        <span>Importar</span>
      {/if}
    </button>
  </div>
</div>

<style>
  .upload-section {
    margin-bottom: 2rem;
  }

  h2 {
    font-size: 1.5rem;
    margin-bottom: 1.5rem;
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
    padding: 3rem;
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
    gap: 1rem;
    cursor: pointer;
    color: #6b7280;
  }

  .drop-label svg {
    color: #2563eb;
  }

  .drop-label span {
    font-size: 1.125rem;
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

  .validation-result {
    padding: 1.5rem;
    border-radius: 0.5rem;
    margin-bottom: 1.5rem;
    background: #fef2f2;
    border: 1px solid #fecaca;
  }

  .validation-result.valid {
    background: #f0fdf4;
    border-color: #86efac;
  }

  .validation-result h3 {
    font-size: 1.125rem;
    margin-bottom: 0.75rem;
  }

  .columns-preview ul,
  .validation-errors ul {
    margin-top: 0.5rem;
    padding-left: 1.5rem;
  }

  .columns-preview li,
  .validation-errors li {
    margin-bottom: 0.25rem;
  }

  .actions {
    display: flex;
    justify-content: center;
    gap: 0.75rem;
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

  .btn-primary:hover:not(:disabled) {
    background: #1d4ed8;
    transform: translateY(-1px);
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
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
</style>
