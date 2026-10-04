<script>
  import { excelPreview } from '../stores/importStore';

  let preview = null;
  excelPreview.subscribe(value => {
    preview = value;
  });
</script>

{#if preview}
  <section class="preview-section">
    <h2>Previsualización del Excel</h2>

    <div class="table-wrapper">
      <table>
        <thead>
          <tr>
            {#each preview.headers as header}
              <th>{header}</th>
            {/each}
          </tr>
        </thead>
        <tbody>
          {#each preview.rows as row}
            <tr>
              {#each preview.headers as header}
                <td>{row[header] ?? ''}</td>
              {/each}
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  </section>
{/if}

<style>
  .preview-section {
    margin-top: 2rem;
    padding-top: 2rem;
    border-top: 1px solid #e5e7eb;
  }

  h2 {
    font-size: 1.25rem;
    margin-bottom: 1rem;
    color: #111827;
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
    font-size: 0.9rem;
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
</style>
