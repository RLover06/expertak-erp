<script>
  /**
   * CardSection - Componente reutilizable para secciones tipo panel ERP.
   * Muestra un título y una lista de opciones con botones alineados a la derecha.
   */
  export let title = '';
  export let items = [];
  export let expanded = true;

  function toggle() {
    expanded = !expanded;
  }
</script>

<div class="card-section">
  <button class="section-header" on:click={toggle} type="button">
    <span class="section-title">{title}</span>
    <span class="chevron" class:collapsed={!expanded}>{expanded ? '▲' : '▼'}</span>
  </button>

  {#if expanded}
    <div class="section-content">
      <div class="items-grid">
        {#each items as item}
          <div class="item-row">
            <div class="item-info">
              {#if item.icon}
                <span class="item-icon" aria-hidden="true">{item.icon}</span>
              {/if}
              <span class="item-label">{item.label}</span>
            </div>
            <div class="item-actions">
              {#each item.buttons || [] as btn}
                <button
                  type="button"
                  class="btn btn-{btn.variant}"
                  on:click={() => btn.onClick && btn.onClick()}
                >
                  {btn.label}
                </button>
              {/each}
              {#if item.iconButtons}
                {#each item.iconButtons || [] as iconBtn}
                  <button
                    type="button"
                    class="btn-icon"
                    title={iconBtn.title || ''}
                    on:click={() => iconBtn.onClick && iconBtn.onClick()}
                    aria-label={iconBtn.title || iconBtn.ariaLabel || 'Acción'}
                  >
                    {iconBtn.icon}
                  </button>
                {/each}
              {/if}
            </div>
          </div>
        {/each}
      </div>
    </div>
  {/if}
</div>

<style>
  .card-section {
    background: #ffffff;
    border-radius: 0.5rem;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
    margin-bottom: 1.25rem;
    overflow: hidden;
  }

  .section-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    width: 100%;
    padding: 1rem 1.25rem;
    background: transparent;
    border: none;
    cursor: pointer;
    font-size: 1rem;
    font-weight: 700;
    color: #374151;
    text-align: left;
  }

  .section-header:hover {
    background: #f9fafb;
  }

  .section-title {
    flex: 1;
  }

  .chevron {
    font-size: 0.75rem;
    color: #6b7280;
  }

  .section-content {
    padding: 0 1.25rem 1.25rem;
    border-top: 1px solid #f3f4f6;
  }

  .items-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
    gap: 0;
  }

  .item-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.75rem 0;
    border-bottom: 1px solid #f3f4f6;
    gap: 1rem;
  }

  .item-row:last-child {
    border-bottom: none;
  }

  .item-info {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    flex: 1;
    min-width: 0;
  }

  .item-icon {
    font-size: 1.125rem;
    color: #6b7280;
    flex-shrink: 0;
  }

  .item-label {
    font-size: 0.9rem;
    color: #374151;
  }

  .item-actions {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    flex-shrink: 0;
  }

  .btn {
    padding: 0.4rem 0.85rem;
    font-size: 0.8rem;
    font-weight: 600;
    border-radius: 0.375rem;
    border: none;
    cursor: pointer;
    white-space: nowrap;
  }

  .btn-crear {
    background: #16a34a;
    color: white;
  }

  .btn-crear:hover {
    background: #15803d;
  }

  .btn-consultar {
    background: #2563eb;
    color: white;
  }

  .btn-consultar:hover {
    background: #1d4ed8;
  }

  .btn-generar {
    background: #7c3aed;
    color: white;
  }

  .btn-generar:hover {
    background: #6d28d9;
  }

  .btn-abrir {
    background: #0ea5e9;
    color: white;
  }

  .btn-abrir:hover {
    background: #0284c7;
  }

  .btn-icon {
    width: 2rem;
    height: 2rem;
    padding: 0;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    background: transparent;
    border: none;
    border-radius: 0.375rem;
    color: #6b7280;
    cursor: pointer;
    font-size: 1rem;
  }

  .btn-icon:hover {
    background: #f3f4f6;
    color: #374151;
  }

  @media (max-width: 768px) {
    .items-grid {
      grid-template-columns: 1fr;
    }

    .item-row {
      flex-direction: column;
      align-items: flex-start;
    }

    .item-actions {
      width: 100%;
      justify-content: flex-end;
    }
  }
</style>
