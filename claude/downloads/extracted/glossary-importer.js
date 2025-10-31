/**
 * Glossary Importer JavaScript
 * Handles AJAX import operations for glossary terms
 *
 * @package Dave_Biggers_Policy_Manager
 * @since 1.1.0
 */

(function($) {
    'use strict';

    var GlossaryImporter = {
        
        /**
         * Initialize the importer
         */
        init: function() {
            this.bindEvents();
        },
        
        /**
         * Bind event handlers
         */
        bindEvents: function() {
            // JSON file upload
            $('#glossary-json-upload-form').on('submit', this.handleJsonUpload);
            
            // JSON paste
            $('#glossary-json-paste-form').on('submit', this.handleJsonPaste);
            
            // Priority terms import
            $('#import-priority-terms').on('click', this.handlePriorityImport);
        },
        
        /**
         * Handle JSON file upload
         */
        handleJsonUpload: function(e) {
            e.preventDefault();
            
            var $form = $(this);
            var $statusDiv = $('#json-upload-status');
            var $fileInput = $('#glossary_json');
            
            if (!$fileInput[0].files.length) {
                GlossaryImporter.showMessage($statusDiv, 'Please select a JSON file.', 'error');
                return;
            }
            
            var formData = new FormData();
            formData.append('action', 'import_glossary_terms');
            formData.append('nonce', glossaryImporter.nonce);
            formData.append('import_type', 'json_upload');
            formData.append('glossary_json', $fileInput[0].files[0]);
            
            GlossaryImporter.showProgress();
            GlossaryImporter.addLog('Starting JSON file import...');
            
            $.ajax({
                url: glossaryImporter.ajaxurl,
                type: 'POST',
                data: formData,
                processData: false,
                contentType: false,
                success: function(response) {
                    if (response.success) {
                        GlossaryImporter.handleImportSuccess(response.data, $statusDiv);
                    } else {
                        GlossaryImporter.handleImportError(response.data.message, $statusDiv);
                    }
                },
                error: function(xhr, status, error) {
                    GlossaryImporter.handleImportError('AJAX error: ' + error, $statusDiv);
                }
            });
        },
        
        /**
         * Handle JSON paste import
         */
        handleJsonPaste: function(e) {
            e.preventDefault();
            
            var $form = $(this);
            var $statusDiv = $('#json-paste-status');
            var jsonData = $('#glossary_json_data').val();
            
            if (!jsonData.trim()) {
                GlossaryImporter.showMessage($statusDiv, 'Please paste JSON data.', 'error');
                return;
            }
            
            // Validate JSON before sending
            try {
                JSON.parse(jsonData);
            } catch (e) {
                GlossaryImporter.showMessage($statusDiv, 'Invalid JSON format: ' + e.message, 'error');
                return;
            }
            
            GlossaryImporter.showProgress();
            GlossaryImporter.addLog('Starting JSON paste import...');
            
            $.ajax({
                url: glossaryImporter.ajaxurl,
                type: 'POST',
                data: {
                    action: 'import_glossary_terms',
                    nonce: glossaryImporter.nonce,
                    import_type: 'json_paste',
                    json_data: jsonData
                },
                success: function(response) {
                    if (response.success) {
                        GlossaryImporter.handleImportSuccess(response.data, $statusDiv);
                    } else {
                        GlossaryImporter.handleImportError(response.data.message, $statusDiv);
                    }
                },
                error: function(xhr, status, error) {
                    GlossaryImporter.handleImportError('AJAX error: ' + error, $statusDiv);
                }
            });
        },
        
        /**
         * Handle priority terms import
         */
        handlePriorityImport: function(e) {
            e.preventDefault();
            
            var $button = $(this);
            var $statusDiv = $('#priority-import-status');
            
            if (!confirm('This will import the top 50 priority glossary terms. Continue?')) {
                return;
            }
            
            $button.prop('disabled', true).text('Importing...');
            
            GlossaryImporter.showProgress();
            GlossaryImporter.addLog('Starting priority terms import...');
            GlossaryImporter.addLog('Importing top 50 most important terms for launch...');
            
            $.ajax({
                url: glossaryImporter.ajaxurl,
                type: 'POST',
                data: {
                    action: 'import_glossary_terms',
                    nonce: glossaryImporter.nonce,
                    import_type: 'priority'
                },
                success: function(response) {
                    $button.prop('disabled', false).text('Import Top 50 Priority Terms');
                    
                    if (response.success) {
                        GlossaryImporter.handleImportSuccess(response.data, $statusDiv);
                    } else {
                        GlossaryImporter.handleImportError(response.data.message, $statusDiv);
                    }
                },
                error: function(xhr, status, error) {
                    $button.prop('disabled', false).text('Import Top 50 Priority Terms');
                    GlossaryImporter.handleImportError('AJAX error: ' + error, $statusDiv);
                }
            });
        },
        
        /**
         * Handle successful import
         */
        handleImportSuccess: function(data, $statusDiv) {
            var total = data.total || 0;
            var imported = data.imported || 0;
            var skipped = data.skipped || 0;
            var errors = data.errors || [];
            
            GlossaryImporter.updateProgress(imported, total);
            
            var message = 'Import complete!\n';
            message += 'Total: ' + total + ' terms\n';
            message += 'Imported: ' + imported + ' terms\n';
            message += 'Skipped: ' + skipped + ' terms';
            
            GlossaryImporter.addLog('✓ ' + message.replace(/\n/g, '<br>'));
            
            if (errors.length > 0) {
                GlossaryImporter.addLog('Errors:');
                errors.forEach(function(error) {
                    GlossaryImporter.addLog('⚠ ' + error);
                });
            }
            
            GlossaryImporter.showMessage($statusDiv, message, 'success');
            
            // Add link to view imported terms
            var viewLink = '<p><a href="edit.php?post_type=glossary_term" class="button">View Imported Terms</a></p>';
            $statusDiv.append(viewLink);
        },
        
        /**
         * Handle import error
         */
        handleImportError: function(message, $statusDiv) {
            GlossaryImporter.addLog('✗ Error: ' + message);
            GlossaryImporter.showMessage($statusDiv, 'Import failed: ' + message, 'error');
        },
        
        /**
         * Show progress section
         */
        showProgress: function() {
            $('#import-progress').show();
            $('#progress-bar').css('width', '0%');
            $('#progress-text').text('0 of 0 terms imported');
            $('#import-log').html('');
        },
        
        /**
         * Update progress bar
         */
        updateProgress: function(current, total) {
            var percentage = total > 0 ? Math.round((current / total) * 100) : 0;
            $('#progress-bar').css('width', percentage + '%');
            $('#progress-text').text(current + ' of ' + total + ' terms imported (' + percentage + '%)');
        },
        
        /**
         * Add log entry
         */
        addLog: function(message) {
            var timestamp = new Date().toLocaleTimeString();
            var logEntry = '<div>[' + timestamp + '] ' + message + '</div>';
            $('#import-log').append(logEntry);
            
            // Auto-scroll to bottom
            var $log = $('#import-log');
            $log.scrollTop($log[0].scrollHeight);
        },
        
        /**
         * Show status message
         */
        showMessage: function($container, message, type) {
            var className = 'glossary-import-' + type;
            var $message = $('<div class="' + className + '"></div>').text(message);
            $container.html($message);
        }
    };

    // Initialize when document is ready
    $(document).ready(function() {
        GlossaryImporter.init();
    });

})(jQuery);
