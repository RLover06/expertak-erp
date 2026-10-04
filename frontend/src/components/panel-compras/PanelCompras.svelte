<script>
  /**
   * PanelCompras - Vista tipo panel administrativo ERP.
   * Secciones: Documentos, Informes, Documentos Electrónicos.
   */
  import CardSection from './CardSection.svelte';

  // Placeholder para acciones (sin modificar lógica existente)
  function noop() {}

  const documentosItems = [
    {
      label: 'Facturas de Compra',
      icon: '📄',
      buttons: [
        { label: 'Crear', variant: 'crear', onClick: noop },
        { label: 'Consultar', variant: 'consultar', onClick: noop },
      ],
      iconButtons: [
        { icon: '⚙', title: 'Configuración', onClick: noop },
        { icon: '📤', title: 'Subir', onClick: noop },
        { icon: '★', title: 'Favorito', onClick: noop },
      ],
    },
    {
      label: 'Remisiones de Compra',
      icon: '📋',
      buttons: [
        { label: 'Crear', variant: 'crear', onClick: noop },
        { label: 'Consultar', variant: 'consultar', onClick: noop },
      ],
      iconButtons: [
        { icon: '⚙', title: 'Configuración', onClick: noop },
        { icon: '📤', title: 'Subir', onClick: noop },
        { icon: '★', title: 'Favorito', onClick: noop },
      ],
    },
    {
      label: 'Notas Débito de Compra',
      icon: '📝',
      buttons: [
        { label: 'Crear', variant: 'crear', onClick: noop },
        { label: 'Consultar', variant: 'consultar', onClick: noop },
      ],
      iconButtons: [
        { icon: '⚙', title: 'Configuración', onClick: noop },
        { icon: '📤', title: 'Subir', onClick: noop },
        { icon: '★', title: 'Favorito', onClick: noop },
      ],
    },
    {
      label: 'Ordenes de Compra',
      icon: '📄',
      buttons: [
        { label: 'Crear', variant: 'crear', onClick: noop },
        { label: 'Consultar', variant: 'consultar', onClick: noop },
      ],
      iconButtons: [
        { icon: '⚙', title: 'Configuración', onClick: noop },
        { icon: '📤', title: 'Subir', onClick: noop },
        { icon: '★', title: 'Favorito', onClick: noop },
      ],
    },
    {
      label: 'Devoluciones de Remisiones de Compra',
      icon: '↩',
      buttons: [
        { label: 'Crear', variant: 'crear', onClick: noop },
        { label: 'Consultar', variant: 'consultar', onClick: noop },
      ],
      iconButtons: [
        { icon: '⚙', title: 'Configuración', onClick: noop },
        { icon: '📤', title: 'Subir', onClick: noop },
        { icon: '★', title: 'Favorito', onClick: noop },
      ],
    },
    {
      label: 'Notas Crédito de Compra',
      icon: '🔒',
      buttons: [
        { label: 'Crear', variant: 'crear', onClick: noop },
        { label: 'Consultar', variant: 'consultar', onClick: noop },
      ],
      iconButtons: [
        { icon: '⚙', title: 'Configuración', onClick: noop },
        { icon: '📤', title: 'Subir', onClick: noop },
        { icon: '★', title: 'Favorito', onClick: noop },
      ],
    },
  ];

  const informesItems = [
    {
      label: 'Compras Agrupadas por Centro de Costo',
      icon: '💼',
      buttons: [{ label: 'Generar', variant: 'generar', onClick: noop }],
      iconButtons: [{ icon: '★', title: 'Favorito', onClick: noop }],
    },
    {
      label: 'Compras Agrupadas por Forma de Pago',
      icon: '💳',
      buttons: [{ label: 'Generar', variant: 'generar', onClick: noop }],
      iconButtons: [{ icon: '★', title: 'Favorito', onClick: noop }],
    },
    {
      label: 'Compras Comparativo por Comprador Mensual',
      icon: '📅',
      buttons: [{ label: 'Generar', variant: 'generar', onClick: noop }],
      iconButtons: [{ icon: '★', title: 'Favorito', onClick: noop }],
    },
    {
      label: 'Compras por Proveedor Agrupadas por Comprador',
      icon: '👥',
      buttons: [{ label: 'Generar', variant: 'generar', onClick: noop }],
      iconButtons: [{ icon: '★', title: 'Favorito', onClick: noop }],
    },
    {
      label: 'Compras por Documento',
      icon: '📊',
      buttons: [{ label: 'Generar', variant: 'generar', onClick: noop }],
      iconButtons: [{ icon: '★', title: 'Favorito', onClick: noop }],
    },
    {
      label: 'Compras por Producto Detallado por Documento',
      icon: '📊',
      buttons: [{ label: 'Generar', variant: 'generar', onClick: noop }],
      iconButtons: [{ icon: '★', title: 'Favorito', onClick: noop }],
    },
    {
      label: 'Compras por Proveedor Agrupadas por Zonas',
      icon: '🌐',
      buttons: [{ label: 'Generar', variant: 'generar', onClick: noop }],
      iconButtons: [{ icon: '★', title: 'Favorito', onClick: noop }],
    },
  ];

  const documentosElectronicosItems = [
    {
      label: 'Documentos Sin Enviar',
      icon: '⚠',
      buttons: [{ label: 'Abrir', variant: 'abrir', onClick: noop }],
      iconButtons: [{ icon: '★', title: 'Favorito', onClick: noop }],
    },
    {
      label: 'Tercero Aprobador Eventos de Recepción de FE',
      icon: '✓',
      buttons: [{ label: 'Abrir', variant: 'abrir', onClick: noop }],
      iconButtons: [{ icon: '★', title: 'Favorito', onClick: noop }],
    },
    {
      label: 'Eventos de Recepción de FE',
      icon: '✎',
      buttons: [{ label: 'Abrir', variant: 'abrir', onClick: noop }],
      iconButtons: [{ icon: '★', title: 'Favorito', onClick: noop }],
    },
  ];
</script>

<div class="panel-compras">
  <div class="search-bar">
    <span class="search-icon" aria-hidden="true">🔍</span>
    <input
      type="text"
      placeholder="Buscar documento o informe..."
      class="search-input"
    />
  </div>

  <div class="sections">
    <CardSection title="Documentos" items={documentosItems} />
    <CardSection title="Informes" items={informesItems} />
    <CardSection title="Documentos Electrónicos" items={documentosElectronicosItems} />
  </div>
</div>

<style>
  .panel-compras {
    background: #f3f4f6;
    padding: 1.5rem;
    border-radius: 0.5rem;
    min-height: 100%;
  }

  .search-bar {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 0.5rem;
    padding: 0.6rem 1rem;
    margin-bottom: 1.5rem;
    max-width: 100%;
  }

  .search-icon {
    font-size: 1rem;
    color: #6b7280;
  }

  .search-input {
    flex: 1;
    border: none;
    outline: none;
    font-size: 0.95rem;
    background: transparent;
  }

  .search-input::placeholder {
    color: #9ca3af;
  }

  .sections {
    display: flex;
    flex-direction: column;
  }

  @media (max-width: 768px) {
    .panel-compras {
      padding: 1rem;
    }
  }
</style>
