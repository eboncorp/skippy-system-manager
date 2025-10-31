<?php
/**
 * Glossary Post Type Registration
 *
 * Registers the 'glossary_term' custom post type for voter education glossary
 *
 * @package Dave_Biggers_Policy_Manager
 * @subpackage Includes
 * @since 1.1.0
 */

// Exit if accessed directly
if (!defined('ABSPATH')) {
    exit;
}

class DB_Glossary_Post_Type {
    
    /**
     * Initialize the class
     */
    public function __construct() {
        add_action('init', array($this, 'register_glossary_post_type'));
        add_action('init', array($this, 'register_glossary_taxonomies'));
        add_filter('enter_title_here', array($this, 'change_title_placeholder'));
        add_action('add_meta_boxes', array($this, 'add_glossary_meta_boxes'));
        add_action('save_post_glossary_term', array($this, 'save_glossary_meta'), 10, 2);
    }
    
    /**
     * Register the glossary_term custom post type
     */
    public function register_glossary_post_type() {
        $labels = array(
            'name'                  => _x('Glossary Terms', 'Post type general name', 'dave-biggers-policy'),
            'singular_name'         => _x('Glossary Term', 'Post type singular name', 'dave-biggers-policy'),
            'menu_name'             => _x('Voter Glossary', 'Admin Menu text', 'dave-biggers-policy'),
            'name_admin_bar'        => _x('Glossary Term', 'Add New on Toolbar', 'dave-biggers-policy'),
            'add_new'               => __('Add New', 'dave-biggers-policy'),
            'add_new_item'          => __('Add New Glossary Term', 'dave-biggers-policy'),
            'new_item'              => __('New Glossary Term', 'dave-biggers-policy'),
            'edit_item'             => __('Edit Glossary Term', 'dave-biggers-policy'),
            'view_item'             => __('View Glossary Term', 'dave-biggers-policy'),
            'all_items'             => __('All Terms', 'dave-biggers-policy'),
            'search_items'          => __('Search Terms', 'dave-biggers-policy'),
            'parent_item_colon'     => __('Parent Terms:', 'dave-biggers-policy'),
            'not_found'             => __('No terms found.', 'dave-biggers-policy'),
            'not_found_in_trash'    => __('No terms found in Trash.', 'dave-biggers-policy'),
            'featured_image'        => _x('Term Image', 'Overrides the "Featured Image" phrase', 'dave-biggers-policy'),
            'set_featured_image'    => _x('Set term image', 'Overrides the "Set featured image" phrase', 'dave-biggers-policy'),
            'remove_featured_image' => _x('Remove term image', 'Overrides the "Remove featured image" phrase', 'dave-biggers-policy'),
            'use_featured_image'    => _x('Use as term image', 'Overrides the "Use as featured image" phrase', 'dave-biggers-policy'),
            'archives'              => _x('Term archives', 'The post type archive label used in nav menus', 'dave-biggers-policy'),
            'insert_into_item'      => _x('Insert into term', 'Overrides the "Insert into post"/"Insert into page" phrase', 'dave-biggers-policy'),
            'uploaded_to_this_item' => _x('Uploaded to this term', 'Overrides the "Uploaded to this post"/"Uploaded to this page" phrase', 'dave-biggers-policy'),
            'filter_items_list'     => _x('Filter terms list', 'Screen reader text for the filter links', 'dave-biggers-policy'),
            'items_list_navigation' => _x('Terms list navigation', 'Screen reader text for the pagination', 'dave-biggers-policy'),
            'items_list'            => _x('Terms list', 'Screen reader text for the items list', 'dave-biggers-policy'),
        );

        $args = array(
            'labels'             => $labels,
            'public'             => true,
            'publicly_queryable' => true,
            'show_ui'            => true,
            'show_in_menu'       => true,
            'menu_icon'          => 'dashicons-book-alt',
            'menu_position'      => 21, // Below Policy Documents
            'query_var'          => true,
            'rewrite'            => array('slug' => 'glossary'),
            'capability_type'    => 'post',
            'has_archive'        => true,
            'hierarchical'       => false,
            'supports'           => array('title', 'editor', 'author', 'thumbnail', 'excerpt', 'revisions'),
            'show_in_rest'       => true, // Enable Gutenberg editor
            'description'        => 'Voter education glossary terms explaining Louisville Metro government and policy concepts',
        );

        register_post_type('glossary_term', $args);
    }
    
    /**
     * Register glossary taxonomies
     */
    public function register_glossary_taxonomies() {
        // Glossary Category (13 main categories)
        $category_labels = array(
            'name'              => _x('Glossary Categories', 'taxonomy general name', 'dave-biggers-policy'),
            'singular_name'     => _x('Glossary Category', 'taxonomy singular name', 'dave-biggers-policy'),
            'search_items'      => __('Search Categories', 'dave-biggers-policy'),
            'all_items'         => __('All Categories', 'dave-biggers-policy'),
            'parent_item'       => __('Parent Category', 'dave-biggers-policy'),
            'parent_item_colon' => __('Parent Category:', 'dave-biggers-policy'),
            'edit_item'         => __('Edit Category', 'dave-biggers-policy'),
            'update_item'       => __('Update Category', 'dave-biggers-policy'),
            'add_new_item'      => __('Add New Category', 'dave-biggers-policy'),
            'new_item_name'     => __('New Category Name', 'dave-biggers-policy'),
            'menu_name'         => __('Categories', 'dave-biggers-policy'),
        );

        $category_args = array(
            'hierarchical'      => true,
            'labels'            => $category_labels,
            'show_ui'           => true,
            'show_admin_column' => true,
            'query_var'         => true,
            'rewrite'           => array('slug' => 'glossary-category'),
            'show_in_rest'      => true,
        );

        register_taxonomy('glossary_category', array('glossary_term'), $category_args);
        
        // Glossary Tag (for cross-referencing and additional organization)
        $tag_labels = array(
            'name'                       => _x('Glossary Tags', 'taxonomy general name', 'dave-biggers-policy'),
            'singular_name'              => _x('Glossary Tag', 'taxonomy singular name', 'dave-biggers-policy'),
            'search_items'               => __('Search Tags', 'dave-biggers-policy'),
            'popular_items'              => __('Popular Tags', 'dave-biggers-policy'),
            'all_items'                  => __('All Tags', 'dave-biggers-policy'),
            'edit_item'                  => __('Edit Tag', 'dave-biggers-policy'),
            'update_item'                => __('Update Tag', 'dave-biggers-policy'),
            'add_new_item'               => __('Add New Tag', 'dave-biggers-policy'),
            'new_item_name'              => __('New Tag Name', 'dave-biggers-policy'),
            'separate_items_with_commas' => __('Separate tags with commas', 'dave-biggers-policy'),
            'add_or_remove_items'        => __('Add or remove tags', 'dave-biggers-policy'),
            'choose_from_most_used'      => __('Choose from the most used tags', 'dave-biggers-policy'),
            'menu_name'                  => __('Tags', 'dave-biggers-policy'),
        );

        $tag_args = array(
            'hierarchical'      => false,
            'labels'            => $tag_labels,
            'show_ui'           => true,
            'show_admin_column' => true,
            'query_var'         => true,
            'rewrite'           => array('slug' => 'glossary-tag'),
            'show_in_rest'      => true,
        );

        register_taxonomy('glossary_tag', array('glossary_term'), $tag_args);
    }
    
    /**
     * Change title placeholder text
     */
    public function change_title_placeholder($title) {
        $screen = get_current_screen();
        if ('glossary_term' === $screen->post_type) {
            $title = 'Enter term name (e.g., "Living Wage", "Community Policing")';
        }
        return $title;
    }
    
    /**
     * Add custom meta boxes for glossary terms
     */
    public function add_glossary_meta_boxes() {
        add_meta_box(
            'glossary_details',
            __('Glossary Term Details', 'dave-biggers-policy'),
            array($this, 'render_glossary_meta_box'),
            'glossary_term',
            'normal',
            'high'
        );
        
        add_meta_box(
            'glossary_related',
            __('Related Terms', 'dave-biggers-policy'),
            array($this, 'render_related_terms_meta_box'),
            'glossary_term',
            'side',
            'default'
        );
        
        add_meta_box(
            'glossary_priority',
            __('Display Priority', 'dave-biggers-policy'),
            array($this, 'render_priority_meta_box'),
            'glossary_term',
            'side',
            'default'
        );
    }
    
    /**
     * Render main glossary meta box
     */
    public function render_glossary_meta_box($post) {
        wp_nonce_field('glossary_meta_nonce', 'glossary_meta_nonce');
        
        $why_matters = get_post_meta($post->ID, '_glossary_why_matters', true);
        $louisville_context = get_post_meta($post->ID, '_glossary_louisville_context', true);
        $data_stats = get_post_meta($post->ID, '_glossary_data_stats', true);
        $campaign_alignment = get_post_meta($post->ID, '_glossary_campaign_alignment', true);
        
        ?>
        <style>
            .glossary-meta-field { margin-bottom: 20px; }
            .glossary-meta-field label { 
                display: block; 
                font-weight: 600; 
                margin-bottom: 5px; 
                color: #1d2327;
            }
            .glossary-meta-field textarea { 
                width: 100%; 
                min-height: 100px;
                padding: 8px;
                border: 1px solid #8c8f94;
                border-radius: 4px;
            }
            .glossary-meta-field .description {
                font-style: italic;
                color: #646970;
                margin-top: 5px;
            }
        </style>
        
        <div class="glossary-meta-field">
            <label for="glossary_why_matters">
                <?php _e('Why This Matters', 'dave-biggers-policy'); ?>
                <span style="color: #d63638;">*</span>
            </label>
            <textarea name="glossary_why_matters" id="glossary_why_matters" required><?php echo esc_textarea($why_matters); ?></textarea>
            <p class="description">Explain why voters should care about this term. Connect it to their daily lives.</p>
        </div>
        
        <div class="glossary-meta-field">
            <label for="glossary_louisville_context">
                <?php _e('Louisville-Specific Context', 'dave-biggers-policy'); ?>
                <span style="color: #d63638;">*</span>
            </label>
            <textarea name="glossary_louisville_context" id="glossary_louisville_context" required><?php echo esc_textarea($louisville_context); ?></textarea>
            <p class="description">Provide Louisville Metro-specific examples, data, or context.</p>
        </div>
        
        <div class="glossary-meta-field">
            <label for="glossary_data_stats">
                <?php _e('Data & Statistics', 'dave-biggers-policy'); ?>
            </label>
            <textarea name="glossary_data_stats" id="glossary_data_stats"><?php echo esc_textarea($data_stats); ?></textarea>
            <p class="description">Include relevant Louisville data, statistics, or research citations.</p>
        </div>
        
        <div class="glossary-meta-field">
            <label for="glossary_campaign_alignment">
                <?php _e('Campaign Alignment', 'dave-biggers-policy'); ?>
            </label>
            <textarea name="glossary_campaign_alignment" id="glossary_campaign_alignment"><?php echo esc_textarea($campaign_alignment); ?></textarea>
            <p class="description">How does this term relate to your campaign proposals? (e.g., 46 mini substations, $25M participatory budget)</p>
        </div>
        <?php
    }
    
    /**
     * Render related terms meta box
     */
    public function render_related_terms_meta_box($post) {
        $related_terms = get_post_meta($post->ID, '_glossary_related_terms', true);
        if (!is_array($related_terms)) {
            $related_terms = array();
        }
        
        // Get all glossary terms except current one
        $all_terms = get_posts(array(
            'post_type' => 'glossary_term',
            'posts_per_page' => -1,
            'post__not_in' => array($post->ID),
            'orderby' => 'title',
            'order' => 'ASC',
            'post_status' => 'any'
        ));
        
        ?>
        <p><strong><?php _e('Select related terms for cross-referencing:', 'dave-biggers-policy'); ?></strong></p>
        <div style="max-height: 300px; overflow-y: auto; border: 1px solid #ddd; padding: 10px; background: #f9f9f9;">
            <?php if (!empty($all_terms)) : ?>
                <?php foreach ($all_terms as $term) : ?>
                    <label style="display: block; margin-bottom: 5px;">
                        <input type="checkbox" 
                               name="glossary_related_terms[]" 
                               value="<?php echo esc_attr($term->ID); ?>"
                               <?php checked(in_array($term->ID, $related_terms)); ?>>
                        <?php echo esc_html($term->post_title); ?>
                    </label>
                <?php endforeach; ?>
            <?php else : ?>
                <p><em><?php _e('No other terms available yet.', 'dave-biggers-policy'); ?></em></p>
            <?php endif; ?>
        </div>
        <p class="description" style="margin-top: 10px;">
            <?php _e('Selected terms will appear as "Related Terms" on the term page.', 'dave-biggers-policy'); ?>
        </p>
        <?php
    }
    
    /**
     * Render priority meta box
     */
    public function render_priority_meta_box($post) {
        $priority = get_post_meta($post->ID, '_glossary_priority', true);
        $is_featured = get_post_meta($post->ID, '_glossary_featured', true);
        
        ?>
        <div style="margin-bottom: 15px;">
            <label for="glossary_priority">
                <strong><?php _e('Display Priority:', 'dave-biggers-policy'); ?></strong>
            </label>
            <select name="glossary_priority" id="glossary_priority" style="width: 100%; margin-top: 5px;">
                <option value="normal" <?php selected($priority, 'normal'); ?>><?php _e('Normal', 'dave-biggers-policy'); ?></option>
                <option value="high" <?php selected($priority, 'high'); ?>><?php _e('High Priority', 'dave-biggers-policy'); ?></option>
                <option value="campaign" <?php selected($priority, 'campaign'); ?>><?php _e('Campaign Essential', 'dave-biggers-policy'); ?></option>
            </select>
            <p class="description"><?php _e('High priority terms appear first in category lists.', 'dave-biggers-policy'); ?></p>
        </div>
        
        <div>
            <label>
                <input type="checkbox" name="glossary_featured" value="1" <?php checked($is_featured, '1'); ?>>
                <strong><?php _e('Featured Term', 'dave-biggers-policy'); ?></strong>
            </label>
            <p class="description"><?php _e('Featured terms appear on homepage and in special widgets.', 'dave-biggers-policy'); ?></p>
        </div>
        <?php
    }
    
    /**
     * Save glossary meta data
     */
    public function save_glossary_meta($post_id, $post) {
        // Check nonce
        if (!isset($_POST['glossary_meta_nonce']) || !wp_verify_nonce($_POST['glossary_meta_nonce'], 'glossary_meta_nonce')) {
            return;
        }
        
        // Check autosave
        if (defined('DOING_AUTOSAVE') && DOING_AUTOSAVE) {
            return;
        }
        
        // Check permissions
        if (!current_user_can('edit_post', $post_id)) {
            return;
        }
        
        // Save Why This Matters
        if (isset($_POST['glossary_why_matters'])) {
            update_post_meta($post_id, '_glossary_why_matters', sanitize_textarea_field($_POST['glossary_why_matters']));
        }
        
        // Save Louisville Context
        if (isset($_POST['glossary_louisville_context'])) {
            update_post_meta($post_id, '_glossary_louisville_context', sanitize_textarea_field($_POST['glossary_louisville_context']));
        }
        
        // Save Data & Stats
        if (isset($_POST['glossary_data_stats'])) {
            update_post_meta($post_id, '_glossary_data_stats', sanitize_textarea_field($_POST['glossary_data_stats']));
        }
        
        // Save Campaign Alignment
        if (isset($_POST['glossary_campaign_alignment'])) {
            update_post_meta($post_id, '_glossary_campaign_alignment', sanitize_textarea_field($_POST['glossary_campaign_alignment']));
        }
        
        // Save Related Terms
        $related_terms = isset($_POST['glossary_related_terms']) ? array_map('intval', $_POST['glossary_related_terms']) : array();
        update_post_meta($post_id, '_glossary_related_terms', $related_terms);
        
        // Save Priority
        if (isset($_POST['glossary_priority'])) {
            update_post_meta($post_id, '_glossary_priority', sanitize_text_field($_POST['glossary_priority']));
        }
        
        // Save Featured Status
        $is_featured = isset($_POST['glossary_featured']) ? '1' : '0';
        update_post_meta($post_id, '_glossary_featured', $is_featured);
    }
}

// Initialize the class
new DB_Glossary_Post_Type();
