<script>
  import ConsolidadoUpload from './components/ConsolidadoUpload.svelte';
  // import DocumentosResumen from './components/DocumentosResumen.svelte'; // oculto (duplicado)
  import InformeReporte from './components/InformeReporte.svelte';
  // import PivotTable from './components/PivotTable.svelte'; // oculto de momento
  import PanelCompras from './components/panel-compras/PanelCompras.svelte';
  import FacturaForm from './components/FacturaForm.svelte';
  import { DEMO } from './services/api';
  const base = import.meta.env.BASE_URL;

  let currentView = 'panel';
</script>

<main>
  {#if DEMO}
    <div class="demo-banner">
      <strong>Demo</strong> con datos ficticios: todo se procesa en tu navegador y nada se envía a la DIAN.
      Prueba la carga con el <a href="{base}ejemplo-documentos-dian.xlsx" download>Excel de ejemplo</a>
      · <a href="https://github.com/RLover06/expertak-erp" target="_blank" rel="noopener">Código en GitHub</a>
    </div>
  {/if}
  <div class="tabs-bar">
    <button
      type="button"
      class="tab"
      class:active={currentView === 'panel'}
      on:click={() => (currentView = 'panel')}
    >
      Panel
    </button>
    <button
      type="button"
      class="tab"
      class:active={currentView === 'panel-compras'}
      on:click={() => (currentView = 'panel-compras')}
    >
      Panel Compras
    </button>
    <button
      type="button"
      class="tab"
      class:active={currentView === 'facturacion'}
      on:click={() => (currentView = 'facturacion')}
    >
      Facturación
    </button>
  </div>

  {#if currentView === 'panel'}
    <header>
      <h1>Expertak - Consolidado y Analisis</h1>
      <p class="subtitle">Carga de consolidado + filtros y tabla dinámica (Supabase o memoria)</p>
    </header>

    <div class="container">
      <ConsolidadoUpload />
      <!-- DocumentosResumen oculto (duplicado con InformeReporte) -->
      <!-- <DocumentosResumen /> -->
      <InformeReporte />
      <!-- PivotTable oculto de momento -->
      <!-- <PivotTable /> -->
    </div>
  {:else if currentView === 'panel-compras'}
    <div class="panel-compras-wrapper">
      <PanelCompras />
    </div>
  {:else}
    <header>
      <h1>Facturación electrónica</h1>
      <p class="subtitle">Crear borradores y emitir facturas de venta (DIAN)</p>
    </header>
    <div class="container">
      <FacturaForm />
    </div>
  {/if}

  <footer>
    <p>Expertak - Sistema de Importación Masiva</p>
  </footer>
</main>

<style>
  .demo-banner {
    background: #fff7e6;
    border-bottom: 1px solid #f3d19c;
    color: #5c3d00;
    font-size: 0.9rem;
    padding: 0.6rem 1rem;
    text-align: center;
  }
  .demo-banner a { color: #7a4b00; font-weight: 600; }
  :global(body) {
    margin: 0;
    padding: 0;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
    background-color: #f9fafb;
    color: #111827;
    line-height: 1.6;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
  }

  main {
    flex: 1;
    display: flex;
    flex-direction: column;
    max-width: 1200px;
    margin: 0 auto;
    padding: 2rem;
    width: 100%;
  }

  header {
    text-align: center;
    margin-bottom: 3rem;
  }

  header h1 {
    font-size: 2.5rem;
    font-weight: 700;
    color: #111827;
    margin-bottom: 0.5rem;
  }

  .subtitle {
    color: #6b7280;
    font-size: 1.125rem;
  }

  .container {
    background: #ffffff;
    border-radius: 0.75rem;
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
    padding: 2rem;
    margin-bottom: 2rem;
  }

  footer {
    text-align: center;
    padding: 2rem;
    color: #6b7280;
    font-size: 0.875rem;
  }

  /* Estilos para navegación por pestañas (Panel / Panel Compras) */
  .tabs-bar {
    display: flex;
    gap: 0;
    background: #e5e7eb;
    border-radius: 0.5rem 0.5rem 0 0;
    padding: 0.25rem 0.25rem 0 0.25rem;
    margin-bottom: 0;
  }

  .tab {
    padding: 0.6rem 1.25rem;
    font-size: 0.9rem;
    font-weight: 500;
    border: none;
    background: transparent;
    color: #6b7280;
    cursor: pointer;
    border-radius: 0.375rem 0.375rem 0 0;
  }

  .tab:hover {
    color: #374151;
  }

  .tab.active {
    background: #ffffff;
    color: #111827;
    box-shadow: 0 -1px 2px rgba(0, 0, 0, 0.05);
  }

  .panel-compras-wrapper {
    flex: 1;
    width: 100%;
  }

  @media (max-width: 768px) {
    main {
      padding: 1rem;
    }

    header h1 {
      font-size: 2rem;
    }

    .container {
      padding: 1.5rem;
    }
  }
</style>