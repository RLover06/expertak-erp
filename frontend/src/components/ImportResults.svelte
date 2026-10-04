<script>
  export let result;

  function formatTime(seconds) {
    if (!seconds) return 'N/A';
    if (seconds < 60) {
      return `${seconds.toFixed(2)}s`;
    }
    const minutes = Math.floor(seconds / 60);
    const secs = (seconds % 60).toFixed(2);
    return `${minutes}m ${secs}s`;
  }
</script>

<div class="results-section">
  <h2>Resultados de la Importación</h2>

  <div class="stats-grid">
    <div class="stat-card">
      <div class="stat-value">{result.total_rows || 0}</div>
      <div class="stat-label">Filas Procesadas</div>
    </div>
    
    <div class="stat-card success">
      <div class="stat-value">{result.inserted || 0}</div>
      <div class="stat-label">Insertadas</div>
    </div>
    
    <div class="stat-card warning">
      <div class="stat-value">{result.duplicates || 0}</div>
      <div class="stat-label">Duplicadas</div>
    </div>
    
    <div class="stat-card error">
      <div class="stat-value">{result.rejected || 0}</div>
      <div class="stat-label">Rechazadas</div>
    </div>
  </div>

  <div class="file-info">
    <p><strong>Archivo:</strong> {result.file_name}</p>
    <p><strong>Tamaño:</strong> {(result.file_size / 1024).toFixed(2)} KB</p>
    <p><strong>Tiempo de procesamiento:</strong> {formatTime(result.processing_time_seconds)}</p>
  </div>

  {#if result.errors && result.errors.length > 0}
    <div class="error-details">
      <h3>Detalles de Errores ({result.errors.length})</h3>
      <div class="error-list">
        {#each result.errors as error}
          <div class="error-item">
            <div class="error-row">Fila {error.row_number}:</div>
            <div class="error-messages">
              {#if Array.isArray(error.errors)}
                {#each error.errors as err}
                  <div class="error-message">{err}</div>
                {/each}
              {:else}
                <div class="error-message">{error.errors || error.error || 'Error desconocido'}</div>
              {/if}
            </div>
          </div>
        {/each}
      </div>
    </div>
  {/if}

  {#if result.success}
    <div class="success-message">
      ✓ {result.message}
    </div>
  {/if}
</div>

<style>
  .results-section {
    margin-top: 2rem;
    padding-top: 2rem;
    border-top: 1px solid #e5e7eb;
  }

  h2 {
    font-size: 1.5rem;
    margin-bottom: 1.5rem;
    color: #111827;
  }

  .stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
    margin-bottom: 2rem;
  }

  .stat-card {
    background: #f9fafb;
    padding: 1.5rem;
    border-radius: 0.5rem;
    text-align: center;
    border: 1px solid #e5e7eb;
  }

  .stat-card.success {
    border-color: #10b981;
    background: #f0fdf4;
  }

  .stat-card.warning {
    border-color: #f59e0b;
    background: #fffbeb;
  }

  .stat-card.error {
    border-color: #ef4444;
    background: #fef2f2;
  }

  .stat-value {
    font-size: 2rem;
    font-weight: 700;
    margin-bottom: 0.5rem;
  }

  .stat-card.success .stat-value {
    color: #10b981;
  }

  .stat-card.warning .stat-value {
    color: #f59e0b;
  }

  .stat-card.error .stat-value {
    color: #ef4444;
  }

  .stat-label {
    font-size: 0.875rem;
    color: #6b7280;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .file-info {
    background: #f9fafb;
    padding: 1rem;
    border-radius: 0.5rem;
    margin-bottom: 1.5rem;
  }

  .file-info p {
    margin: 0.5rem 0;
    color: #374151;
  }

  .error-details {
    margin-top: 2rem;
  }

  .error-details h3 {
    font-size: 1.125rem;
    margin-bottom: 1rem;
    color: #ef4444;
  }

  .error-list {
    max-height: 400px;
    overflow-y: auto;
    border: 1px solid #e5e7eb;
    border-radius: 0.5rem;
    background: #f9fafb;
  }

  .error-item {
    padding: 1rem;
    border-bottom: 1px solid #e5e7eb;
  }

  .error-item:last-child {
    border-bottom: none;
  }

  .error-row {
    font-weight: 600;
    color: #111827;
    margin-bottom: 0.25rem;
  }

  .error-messages {
    margin-left: 1rem;
  }

  .error-message {
    color: #ef4444;
    font-size: 0.875rem;
    margin-bottom: 0.25rem;
  }

  .success-message {
    padding: 1rem;
    background: #d1fae5;
    color: #065f46;
    border: 1px solid #10b981;
    border-radius: 0.5rem;
    margin-top: 1.5rem;
    font-weight: 500;
  }

  @media (max-width: 768px) {
    .stats-grid {
      grid-template-columns: repeat(2, 1fr);
    }
  }

  @media (max-width: 480px) {
    .stats-grid {
      grid-template-columns: 1fr;
    }
  }
</style>
