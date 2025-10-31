<?php
/**
 * Glossary Term Importer
 *
 * Handles bulk import of glossary terms from structured data files
 *
 * @package Dave_Biggers_Policy_Manager
 * @subpackage Includes
 * @since 1.1.0
 */

// Exit if accessed directly
if (!defined('ABSPATH')) {
    exit;
}

class DB_Glossary_Importer {
    
    /**
     * Initialize the importer
     */
    public function __construct() {
        add_action('admin_menu', array($this, 'add_importer_page'));
        add_action('wp_ajax_import_glossary_terms', array($this, 'ajax_import_terms'));
        add_action('admin_enqueue_scripts', array($this, 'enqueue_importer_scripts'));
    }
    
    /**
     * Add importer page to WordPress admin
     */
    public function add_importer_page() {
        add_submenu_page(
            'edit.php?post_type=glossary_term',
            __('Import Terms', 'dave-biggers-policy'),
            __('Import Terms', 'dave-biggers-policy'),
            'manage_options',
            'glossary-importer',
            array($this, 'render_importer_page')
        );
    }
    
    /**
     * Enqueue scripts for importer
     */
    public function enqueue_importer_scripts($hook) {
        if ('glossary_term_page_glossary-importer' !== $hook) {
            return;
        }
        
        wp_enqueue_script('glossary-importer', plugin_dir_url(__FILE__) . '../admin/js/glossary-importer.js', array('jquery'), '1.0', true);
        wp_localize_script('glossary-importer', 'glossaryImporter', array(
            'ajaxurl' => admin_url('admin-ajax.php'),
            'nonce' => wp_create_nonce('glossary_import_nonce')
        ));
    }
    
    /**
     * Render the importer page
     */
    public function render_importer_page() {
        ?>
        <div class="wrap">
            <h1><?php _e('Import Glossary Terms', 'dave-biggers-policy'); ?></h1>
            
            <div class="notice notice-info">
                <p><strong><?php _e('About the Glossary:', 'dave-biggers-policy'); ?></strong></p>
                <ul style="list-style: disc; margin-left: 20px;">
                    <li>468+ comprehensive terms across 13 policy categories</li>
                    <li>Louisville Metro-specific context for every term</li>
                    <li>"Why This Matters" sections connecting to voter lives</li>
                    <li>Cross-referenced terms for easy navigation</li>
                    <li>Aligned with campaign proposals (46 substations, $25M participatory budget, etc.)</li>
                </ul>
            </div>
            
            <div class="card" style="max-width: 800px; margin-top: 20px;">
                <h2><?php _e('Import Methods', 'dave-biggers-policy'); ?></h2>
                
                <!-- Method 1: JSON Upload -->
                <div style="margin-bottom: 30px; padding-bottom: 30px; border-bottom: 1px solid #ccc;">
                    <h3><?php _e('Method 1: Upload JSON File', 'dave-biggers-policy'); ?></h3>
                    <p><?php _e('Upload a JSON file containing glossary terms in the correct format.', 'dave-biggers-policy'); ?></p>
                    
                    <form id="glossary-json-upload-form" enctype="multipart/form-data">
                        <?php wp_nonce_field('glossary_import_nonce', 'glossary_import_nonce'); ?>
                        <input type="file" name="glossary_json" id="glossary_json" accept=".json" required>
                        <button type="submit" class="button button-primary"><?php _e('Upload & Import', 'dave-biggers-policy'); ?></button>
                    </form>
                    
                    <div id="json-upload-status" style="margin-top: 15px;"></div>
                </div>
                
                <!-- Method 2: Paste JSON -->
                <div style="margin-bottom: 30px; padding-bottom: 30px; border-bottom: 1px solid #ccc;">
                    <h3><?php _e('Method 2: Paste JSON Data', 'dave-biggers-policy'); ?></h3>
                    <p><?php _e('Paste glossary terms in JSON format directly.', 'dave-biggers-policy'); ?></p>
                    
                    <form id="glossary-json-paste-form">
                        <?php wp_nonce_field('glossary_import_nonce', 'glossary_import_paste_nonce'); ?>
                        <textarea name="glossary_json_data" id="glossary_json_data" rows="10" style="width: 100%; font-family: monospace;" placeholder='[{"term": "Living Wage", "category": "Workforce Development", ...}]'></textarea>
                        <button type="submit" class="button button-primary"><?php _e('Import from Paste', 'dave-biggers-policy'); ?></button>
                    </form>
                    
                    <div id="json-paste-status" style="margin-top: 15px;"></div>
                </div>
                
                <!-- Method 3: Import Priority Terms -->
                <div>
                    <h3><?php _e('Method 3: Import Priority Terms', 'dave-biggers-policy'); ?></h3>
                    <p><?php _e('Import the top 50 most important glossary terms for launch.', 'dave-biggers-policy'); ?></p>
                    
                    <button id="import-priority-terms" class="button button-primary button-hero">
                        <?php _e('Import Top 50 Priority Terms', 'dave-biggers-policy'); ?>
                    </button>
                    
                    <div id="priority-import-status" style="margin-top: 15px;"></div>
                </div>
            </div>
            
            <!-- Import Progress -->
            <div id="import-progress" style="display: none; margin-top: 30px; max-width: 800px;">
                <h2><?php _e('Import Progress', 'dave-biggers-policy'); ?></h2>
                <div class="progress-bar-container" style="width: 100%; height: 30px; background: #f0f0f0; border: 1px solid #ccc; border-radius: 5px; overflow: hidden;">
                    <div id="progress-bar" style="height: 100%; background: #0073aa; width: 0%; transition: width 0.3s;"></div>
                </div>
                <p id="progress-text" style="margin-top: 10px; font-weight: 600;">0 of 0 terms imported</p>
                <div id="import-log" style="max-height: 300px; overflow-y: auto; background: #f9f9f9; padding: 15px; border: 1px solid #ddd; margin-top: 15px; font-family: monospace; font-size: 12px;"></div>
            </div>
            
            <!-- JSON Format Documentation -->
            <div class="card" style="max-width: 800px; margin-top: 30px;">
                <h2><?php _e('JSON Format Documentation', 'dave-biggers-policy'); ?></h2>
                <p><?php _e('Each glossary term should be a JSON object with the following structure:', 'dave-biggers-policy'); ?></p>
                
                <pre style="background: #f5f5f5; padding: 15px; overflow-x: auto; border-radius: 4px;"><code>{
  "term": "Living Wage",
  "definition": "A wage that allows a worker to afford basic needs...",
  "category": "Workforce Development",
  "tags": ["employment", "equity", "economy"],
  "why_matters": "Explains the direct impact on Louisville residents...",
  "louisville_context": "In Louisville Metro, median household income is $60,444...",
  "data_stats": "According to MIT Living Wage Calculator...",
  "campaign_alignment": "Aligns with employee compensation plan...",
  "related_terms": ["Minimum Wage", "Income Inequality", "Poverty Line"],
  "priority": "high",
  "featured": true
}</code></pre>
                
                <h3><?php _e('Required Fields:', 'dave-biggers-policy'); ?></h3>
                <ul style="list-style: disc; margin-left: 20px;">
                    <li><code>term</code> - The term name (becomes post title)</li>
                    <li><code>definition</code> - Main definition (becomes post content)</li>
                    <li><code>category</code> - One of the 13 glossary categories</li>
                    <li><code>why_matters</code> - Why voters should care</li>
                    <li><code>louisville_context</code> - Louisville-specific information</li>
                </ul>
                
                <h3><?php _e('Optional Fields:', 'dave-biggers-policy'); ?></h3>
                <ul style="list-style: disc; margin-left: 20px;">
                    <li><code>tags</code> - Array of related keywords</li>
                    <li><code>data_stats</code> - Relevant data and statistics</li>
                    <li><code>campaign_alignment</code> - How it connects to campaign proposals</li>
                    <li><code>related_terms</code> - Array of related term names for cross-referencing</li>
                    <li><code>priority</code> - "normal", "high", or "campaign"</li>
                    <li><code>featured</code> - true or false</li>
                </ul>
            </div>
            
            <!-- The 13 Categories -->
            <div class="card" style="max-width: 800px; margin-top: 30px;">
                <h2><?php _e('The 13 Glossary Categories', 'dave-biggers-policy'); ?></h2>
                <ol>
                    <li>Voting & Elections (26 terms)</li>
                    <li>Government Structure (35 terms)</li>
                    <li>Budget & Finance (30 terms)</li>
                    <li>Economic Development & Accountability (45 terms)</li>
                    <li>Environmental & Sustainability (47 terms)</li>
                    <li>Housing & Homelessness (40 terms)</li>
                    <li>Public Safety & Policing (35 terms)</li>
                    <li>Education (25 terms)</li>
                    <li>Healthcare & Public Health (30 terms)</li>
                    <li>Workforce Development (40 terms)</li>
                    <li>Transportation & Infrastructure (35 terms)</li>
                    <li>Government Accountability & Transparency (40 terms)</li>
                    <li>Data Center Development (40 terms)</li>
                </ol>
                <p><strong>Total: 468+ terms</strong></p>
            </div>
        </div>
        
        <style>
            .glossary-import-success {
                padding: 10px;
                background: #d4edda;
                border: 1px solid #c3e6cb;
                color: #155724;
                border-radius: 4px;
                margin: 10px 0;
            }
            .glossary-import-error {
                padding: 10px;
                background: #f8d7da;
                border: 1px solid #f5c6cb;
                color: #721c24;
                border-radius: 4px;
                margin: 10px 0;
            }
            .glossary-import-warning {
                padding: 10px;
                background: #fff3cd;
                border: 1px solid #ffeeba;
                color: #856404;
                border-radius: 4px;
                margin: 10px 0;
            }
        </style>
        <?php
    }
    
    /**
     * AJAX handler for importing glossary terms
     */
    public function ajax_import_terms() {
        check_ajax_referer('glossary_import_nonce', 'nonce');
        
        if (!current_user_can('manage_options')) {
            wp_send_json_error(array('message' => 'Insufficient permissions.'));
        }
        
        $import_type = isset($_POST['import_type']) ? sanitize_text_field($_POST['import_type']) : '';
        $terms_data = array();
        
        // Handle different import types
        if ($import_type === 'json_upload') {
            if (!isset($_FILES['glossary_json'])) {
                wp_send_json_error(array('message' => 'No file uploaded.'));
            }
            
            $file = $_FILES['glossary_json'];
            $json_content = file_get_contents($file['tmp_name']);
            $terms_data = json_decode($json_content, true);
            
        } elseif ($import_type === 'json_paste') {
            $json_content = isset($_POST['json_data']) ? stripslashes($_POST['json_data']) : '';
            $terms_data = json_decode($json_content, true);
            
        } elseif ($import_type === 'priority') {
            $terms_data = $this->get_priority_terms_data();
        }
        
        // Validate JSON
        if (json_last_error() !== JSON_ERROR_NONE) {
            wp_send_json_error(array('message' => 'Invalid JSON format: ' . json_last_error_msg()));
        }
        
        if (empty($terms_data) || !is_array($terms_data)) {
            wp_send_json_error(array('message' => 'No valid terms found in data.'));
        }
        
        // Import terms
        $results = $this->import_terms_array($terms_data);
        
        wp_send_json_success($results);
    }
    
    /**
     * Import array of term data
     */
    private function import_terms_array($terms_data) {
        $imported = 0;
        $skipped = 0;
        $errors = array();
        $total = count($terms_data);
        
        foreach ($terms_data as $index => $term_data) {
            $result = $this->import_single_term($term_data);
            
            if ($result['success']) {
                $imported++;
            } else {
                $skipped++;
                $errors[] = "Term #{$index}: {$result['message']}";
            }
        }
        
        return array(
            'total' => $total,
            'imported' => $imported,
            'skipped' => $skipped,
            'errors' => $errors
        );
    }
    
    /**
     * Import a single glossary term
     */
    private function import_single_term($data) {
        // Validate required fields
        if (empty($data['term'])) {
            return array('success' => false, 'message' => 'Missing required field: term');
        }
        
        if (empty($data['definition'])) {
            return array('success' => false, 'message' => 'Missing required field: definition');
        }
        
        // Check if term already exists
        $existing = get_page_by_title($data['term'], OBJECT, 'glossary_term');
        if ($existing) {
            return array('success' => false, 'message' => 'Term already exists: ' . $data['term']);
        }
        
        // Create the post
        $post_data = array(
            'post_title'   => sanitize_text_field($data['term']),
            'post_content' => wp_kses_post($data['definition']),
            'post_status'  => 'publish',
            'post_type'    => 'glossary_term',
            'post_author'  => get_current_user_id(),
        );
        
        $post_id = wp_insert_post($post_data);
        
        if (is_wp_error($post_id)) {
            return array('success' => false, 'message' => 'Failed to create post: ' . $post_id->get_error_message());
        }
        
        // Set category
        if (!empty($data['category'])) {
            $category = get_term_by('name', $data['category'], 'glossary_category');
            if (!$category) {
                $category = wp_insert_term($data['category'], 'glossary_category');
                if (!is_wp_error($category)) {
                    $category = get_term($category['term_id'], 'glossary_category');
                }
            }
            if (!is_wp_error($category) && $category) {
                wp_set_object_terms($post_id, $category->term_id, 'glossary_category');
            }
        }
        
        // Set tags
        if (!empty($data['tags']) && is_array($data['tags'])) {
            wp_set_object_terms($post_id, $data['tags'], 'glossary_tag');
        }
        
        // Save meta fields
        if (!empty($data['why_matters'])) {
            update_post_meta($post_id, '_glossary_why_matters', sanitize_textarea_field($data['why_matters']));
        }
        
        if (!empty($data['louisville_context'])) {
            update_post_meta($post_id, '_glossary_louisville_context', sanitize_textarea_field($data['louisville_context']));
        }
        
        if (!empty($data['data_stats'])) {
            update_post_meta($post_id, '_glossary_data_stats', sanitize_textarea_field($data['data_stats']));
        }
        
        if (!empty($data['campaign_alignment'])) {
            update_post_meta($post_id, '_glossary_campaign_alignment', sanitize_textarea_field($data['campaign_alignment']));
        }
        
        // Priority
        $priority = isset($data['priority']) ? sanitize_text_field($data['priority']) : 'normal';
        update_post_meta($post_id, '_glossary_priority', $priority);
        
        // Featured status
        $featured = isset($data['featured']) && $data['featured'] ? '1' : '0';
        update_post_meta($post_id, '_glossary_featured', $featured);
        
        // Store related terms for later processing (after all terms are imported)
        if (!empty($data['related_terms']) && is_array($data['related_terms'])) {
            update_post_meta($post_id, '_glossary_related_terms_names', $data['related_terms']);
        }
        
        return array('success' => true, 'message' => 'Term imported: ' . $data['term'], 'post_id' => $post_id);
    }
    
    /**
     * Get priority terms data
     * Returns top 50 most important terms for initial launch
     */
    private function get_priority_terms_data() {
        // This would ideally be loaded from a JSON file in the plugin
        // For now, returning a sample structure that you would populate
        
        $priority_terms = array(
            array(
                'term' => 'Living Wage',
                'definition' => 'A wage sufficient to provide the necessities and comforts essential to an acceptable standard of living, based on local cost of living calculations.',
                'category' => 'Workforce Development',
                'tags' => array('employment', 'equity', 'economy'),
                'why_matters' => 'Understanding living wage helps voters evaluate whether proposed policies will genuinely improve working families\' lives or just sound good. It\'s the difference between a job that keeps you afloat and one that keeps you struggling.',
                'louisville_context' => 'In Louisville Metro, the MIT Living Wage Calculator estimates a living wage of $17.85/hour for a single adult, while a family with two working adults and two children needs each adult to earn $23.43/hour. This contrasts sharply with Kentucky\'s minimum wage of $7.25/hour.',
                'data_stats' => 'According to MIT Living Wage Calculator (2024), 43% of Louisville Metro workers earn less than a living wage. Median household income is $60,444, but this varies dramatically by ZIP code - from $27,000 in West Louisville to over $100,000 in Eastern suburbs.',
                'campaign_alignment' => 'Dave\'s Employee Compensation Plan includes competitive wages as part of the $25M investment to ensure Metro employees earn living wages, recognizing that government should model fair employment practices.',
                'related_terms' => array('Minimum Wage', 'Income Inequality', 'Poverty Line', 'Employee Compensation'),
                'priority' => 'campaign',
                'featured' => true
            ),
            // Add more priority terms here...
            // You would populate this with your top 50 terms
        );
        
        return $priority_terms;
    }
    
    /**
     * Process related terms connections after all terms are imported
     * This should be run as a separate admin action
     */
    public function process_related_terms_connections() {
        $args = array(
            'post_type' => 'glossary_term',
            'posts_per_page' => -1,
            'meta_query' => array(
                array(
                    'key' => '_glossary_related_terms_names',
                    'compare' => 'EXISTS'
                )
            )
        );
        
        $terms = get_posts($args);
        $processed = 0;
        
        foreach ($terms as $term) {
            $related_names = get_post_meta($term->ID, '_glossary_related_terms_names', true);
            
            if (!is_array($related_names)) {
                continue;
            }
            
            $related_ids = array();
            
            foreach ($related_names as $related_name) {
                $related_post = get_page_by_title($related_name, OBJECT, 'glossary_term');
                if ($related_post) {
                    $related_ids[] = $related_post->ID;
                }
            }
            
            if (!empty($related_ids)) {
                update_post_meta($term->ID, '_glossary_related_terms', $related_ids);
                $processed++;
            }
            
            // Clean up temporary meta
            delete_post_meta($term->ID, '_glossary_related_terms_names');
        }
        
        return $processed;
    }
}

// Initialize the importer
new DB_Glossary_Importer();
