/**
 * Frontend JavaScript for Excel Import System
 * Handles file upload, form submission, and result display
 */

(function() {
    'use strict';

    // DOM elements
    const fileInput = document.getElementById('excel_file');
    const fileLabel = document.getElementById('fileLabel');
    const fileInfo = document.getElementById('fileInfo');
    const uploadForm = document.getElementById('uploadForm');
    const submitBtn = document.getElementById('submitBtn');
    const resultsSection = document.getElementById('results');
    const messageDiv = document.getElementById('message');
    const errorDetails = document.getElementById('errorDetails');
    const errorList = document.getElementById('errorList');

    // API endpoint
    const API_ENDPOINT = '../api/import.php';

    /**
     * Format file size
     */
    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
    }

    /**
     * Show message
     */
    function showMessage(text, type = 'success') {
        messageDiv.textContent = text;
        messageDiv.className = `message ${type}`;
        messageDiv.style.display = 'block';
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            messageDiv.style.display = 'none';
        }, 5000);
    }

    /**
     * Update file info display
     */
    function updateFileInfo(file) {
        if (file) {
            fileLabel.textContent = file.name;
            fileInfo.textContent = `Tamaño: ${formatFileSize(file.size)}`;
            fileInfo.classList.add('show');
            submitBtn.disabled = false;
        } else {
            fileLabel.textContent = 'Seleccionar archivo Excel (.xlsx)';
            fileInfo.classList.remove('show');
            submitBtn.disabled = true;
        }
    }

    /**
     * Set loading state
     */
    function setLoading(loading) {
        submitBtn.disabled = loading;
        const btnText = submitBtn.querySelector('.btn-text');
        const btnLoader = submitBtn.querySelector('.btn-loader');
        
        if (loading) {
            btnText.style.display = 'none';
            btnLoader.style.display = 'inline-block';
        } else {
            btnText.style.display = 'inline';
            btnLoader.style.display = 'none';
        }
    }

    /**
     * Display import results
     */
    function displayResults(data) {
        // Update statistics
        document.getElementById('statTotal').textContent = data.total_rows || 0;
        document.getElementById('statInserted').textContent = data.inserted || 0;
        document.getElementById('statDuplicates').textContent = data.duplicates || 0;
        document.getElementById('statRejected').textContent = data.rejected || 0;

        // Display errors if any
        if (data.errors && data.errors.length > 0) {
            errorList.innerHTML = '';
            data.errors.forEach(error => {
                const errorItem = document.createElement('div');
                errorItem.className = 'error-item';
                
                const rowInfo = document.createElement('div');
                rowInfo.className = 'error-row';
                rowInfo.textContent = `Fila ${error.row || 'N/A'}:`;
                
                const errorMsg = document.createElement('div');
                errorMsg.className = 'error-message';
                
                if (Array.isArray(error.errors)) {
                    errorMsg.textContent = error.errors.join(', ');
                } else {
                    errorMsg.textContent = error.error || 'Error desconocido';
                }
                
                errorItem.appendChild(rowInfo);
                errorItem.appendChild(errorMsg);
                errorList.appendChild(errorItem);
            });
            
            errorDetails.style.display = 'block';
        } else {
            errorDetails.style.display = 'none';
        }

        // Show results section
        resultsSection.style.display = 'block';
        
        // Scroll to results
        resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    /**
     * Handle file input change
     */
    fileInput.addEventListener('change', function(e) {
        const file = e.target.files[0];
        updateFileInfo(file);
    });

    /**
     * Handle form submission
     */
    uploadForm.addEventListener('submit', async function(e) {
        e.preventDefault();

        const file = fileInput.files[0];
        if (!file) {
            showMessage('Por favor seleccione un archivo', 'error');
            return;
        }

        // Validate file extension
        if (!file.name.toLowerCase().endsWith('.xlsx')) {
            showMessage('Solo se permiten archivos .xlsx', 'error');
            return;
        }

        // Create FormData
        const formData = new FormData();
        formData.append('excel_file', file);

        // Set loading state
        setLoading(true);
        resultsSection.style.display = 'none';
        messageDiv.style.display = 'none';

        try {
            // Send request
            const response = await fetch(API_ENDPOINT, {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (result.success) {
                showMessage('Importación completada exitosamente', 'success');
                displayResults(result.data);
            } else {
                showMessage(result.message || 'Error en la importación', 'error');
                
                // Display error details if available
                if (result.details && result.details.length > 0) {
                    const errorData = {
                        errors: result.details.map((detail, index) => ({
                            row: index + 1,
                            error: typeof detail === 'string' ? detail : JSON.stringify(detail)
                        }))
                    };
                    displayResults({ ...result.data, errors: errorData.errors });
                }
            }
        } catch (error) {
            console.error('Error:', error);
            showMessage('Error de conexión. Por favor intente nuevamente.', 'error');
        } finally {
            setLoading(false);
        }
    });

    // Initialize
    updateFileInfo(null);
})();
