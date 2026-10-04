<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Excel Bulk Import - Expertak</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <div class="container">
        <header>
            <h1>Importación Masiva de Excel</h1>
            <p class="subtitle">Sistema de importación de documentos contables</p>
        </header>

        <main>
            <div class="upload-section">
                <form id="uploadForm" enctype="multipart/form-data">
                    <div class="form-group">
                        <label for="excel_file" class="file-label">
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                                <polyline points="17 8 12 3 7 8"></polyline>
                                <line x1="12" y1="3" x2="12" y2="15"></line>
                            </svg>
                            <span id="fileLabel">Seleccionar archivo Excel (.xlsx)</span>
                        </label>
                        <input 
                            type="file" 
                            id="excel_file" 
                            name="excel_file" 
                            accept=".xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            required
                        >
                        <div class="file-info" id="fileInfo"></div>
                    </div>

                    <div class="form-group">
                        <button type="submit" id="submitBtn" class="btn btn-primary" disabled>
                            <span class="btn-text">Iniciar Importación</span>
                            <span class="btn-loader" style="display: none;">
                                <svg width="20" height="20" viewBox="0 0 24 24">
                                    <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none" opacity="0.25"/>
                                    <path d="M12 2a10 10 0 0 1 10 10" stroke="currentColor" stroke-width="4" fill="none">
                                        <animateTransform attributeName="transform" type="rotate" dur="1s" repeatCount="indefinite" values="0 12 12;360 12 12"/>
                                    </path>
                                </svg>
                            </span>
                        </button>
                    </div>
                </form>
            </div>

            <div id="results" class="results-section" style="display: none;">
                <h2>Resultados de la Importación</h2>
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-value" id="statTotal">0</div>
                        <div class="stat-label">Filas Procesadas</div>
                    </div>
                    <div class="stat-card success">
                        <div class="stat-value" id="statInserted">0</div>
                        <div class="stat-label">Insertadas</div>
                    </div>
                    <div class="stat-card warning">
                        <div class="stat-value" id="statDuplicates">0</div>
                        <div class="stat-label">Duplicadas</div>
                    </div>
                    <div class="stat-card error">
                        <div class="stat-value" id="statRejected">0</div>
                        <div class="stat-label">Rechazadas</div>
                    </div>
                </div>

                <div id="errorDetails" class="error-details" style="display: none;">
                    <h3>Detalles de Errores</h3>
                    <div class="error-list" id="errorList"></div>
                </div>
            </div>

            <div id="message" class="message" style="display: none;"></div>
        </main>

        <footer>
            <p>Expertak - Sistema de Importación Masiva</p>
        </footer>
    </div>

    <script src="script.js"></script>
</body>
</html>
