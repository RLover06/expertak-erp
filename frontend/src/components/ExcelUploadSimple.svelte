<script>
  import { uploadExcelFile } from '../services/api';

  let selectedFile = null;
  let isSending = false;
  let statusMessage = null;
  let statusType = 'success';

  function handleFileSelect(event) {
    const file = event.target.files?.[0];
    if (file) {
      selectedFile = file;
      statusMessage = null;
    }
  }

  async function handleSend() {
    if (!selectedFile) {
      statusType = 'error';
      statusMessage = 'Seleccione un archivo primero.';
      return;
    }

    if (!selectedFile.name.endsWith('.xlsx')) {
      statusType = 'error';
      statusMessage = 'Solo se permiten archivos .xlsx';
      return;
    }

    try {
      isSending = true;
      statusMessage = null;
      await uploadExcelFile(selectedFile);
      statusType = 'success';
      statusMessage = 'Archivo enviado correctamente.';
    } catch (err) {
      statusType = 'error';
      statusMessage = err?.message || 'Error al enviar el archivo.';
    } finally {
      isSending = false;
    }
  }
</script>

<section class="simple-upload">
  <h2>Enviar archivo Excel</h2>

  <input type="file" accept=".xlsx" on:change={handleFileSelect} />
  <button class="btn" on:click={handleSend} disabled={isSending}>
    {#if isSending}Enviando...{:else}Enviar{/if}
  </button>

  {#if statusMessage}
    <div class="status" class:success={statusType === 'success'} class:error={statusType === 'error'}>
      {statusMessage}
    </div>
  {/if}
</section>

<style>
  .simple-upload {
    padding: 1rem 0;
    margin-bottom: 2rem;
  }

  h2 {
    font-size: 1.25rem;
    margin-bottom: 0.75rem;
    color: #111827;
  }

  input[type="file"] {
    display: block;
    margin-bottom: 0.75rem;
  }

  .btn {
    display: inline-flex;
    align-items: center;
    padding: 0.5rem 1rem;
    background: #2563eb;
    color: white;
    border: none;
    border-radius: 0.5rem;
    cursor: pointer;
    font-weight: 600;
  }

  .btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .status {
    margin-top: 0.75rem;
    padding: 0.75rem 1rem;
    border-radius: 0.5rem;
  }

  .status.success {
    background: #dcfce7;
    color: #166534;
    border: 1px solid #86efac;
  }

  .status.error {
    background: #fee2e2;
    color: #991b1b;
    border: 1px solid #fca5a5;
  }
</style>
