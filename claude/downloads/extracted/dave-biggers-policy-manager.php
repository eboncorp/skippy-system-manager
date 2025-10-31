<?php
/**
 * Plugin Name: Dave Biggers Policy Manager
 * Plugin URI: https://rundaverun.org
 * Description: Complete policy document management system with voter education glossary for Louisville mayoral campaign
 * Version: 1.1.0
 * Author: Dave Biggers Campaign
 * Author URI: https://rundaverun.org
 * License: GPL v2 or later
 * License URI: https://www.gnu.org/licenses/gpl-2.0.html
 * Text Domain: dave-biggers-policy
 * Domain Path: /languages
 *
 * @package Dave_Biggers_Policy_Manager
 */

// Exit if accessed directly
if (!defined('ABSPATH')) {
    exit;
}

// Define plugin constants
define('DB_POLICY_VERSION', '1.1.0');
define('DB_POLICY_PLUGIN_DIR', plugin_dir_path(__FILE__));
define('DB_POLICY_PLUGIN_URL', plugin_dir_url(__FILE__));
define('DB_POLICY_PLUGIN_BASENAME', plugin_basename(__FILE__));

/**
 * Main Plugin Class
 */
class Dave_Biggers_Policy_Manager {
    
    /**
     * Instance of this class
     */
    private static $instance = null;
    
    /**
     * Get instance of this class
     */
    public static function get_instance() {
        if (null === self::$instance) {
            self::$instance = new self();
        }
        return self::$instance;
    }
    
    /**
     * Constructor
     */
    private function __construct() {
        $this->load_dependencies();
        $this->define_hooks();
    }
    
    /**
     * Load required dependencies
     */
    private function load_dependencies() {
        // Core classes
        require_once DB_POLICY_PLUGIN_DIR . 'includes/class-core.php';
        require_once DB_POLICY_PLUGIN_DIR . 'includes/class-activator.php';
        require_once DB_POLICY_PLUGIN_DIR . 'includes/class-deactivator.php';
        
        // Policy document classes (existing functionality)
        require_once DB_POLICY_PLUGIN_DIR . 'includes/class-post-types.php';
        require_once DB_POLICY_PLUGIN_DIR . 'includes/class-taxonomies.php';
        require_once DB_POLICY_PLUGIN_DIR . 'includes/class-importer.php';
        require_once DB_POLICY_PLUGIN_DIR . 'includes/class-pdf-generator.php';
        require_once DB_POLICY_PLUGIN_DIR . 'includes/class-search.php';
        require_once DB_POLICY_PLUGIN_DIR . 'includes/class-email-signup.php';
        require_once DB_POLICY_PLUGIN_DIR . 'includes/class-volunteer-access.php';
        
        // NEW: Glossary functionality
        require_once DB_POLICY_PLUGIN_DIR . 'includes/class-glossary-post-type.php';
        require_once DB_POLICY_PLUGIN_DIR . 'includes/class-glossary-importer.php';
        
        // Admin and public classes
        if (is_admin()) {
            require_once DB_POLICY_PLUGIN_DIR . 'admin/class-admin.php';
        } else {
            require_once DB_POLICY_PLUGIN_DIR . 'public/class-public.php';
        }
    }
    
    /**
     * Define WordPress hooks
     */
    private function define_hooks() {
        // Activation and deactivation hooks
        register_activation_hook(__FILE__, array('DB_Plugin_Activator', 'activate'));
        register_deactivation_hook(__FILE__, array('DB_Plugin_Deactivator', 'deactivate'));
        
        // Load plugin textdomain
        add_action('plugins_loaded', array($this, 'load_textdomain'));
        
        // Enqueue scripts and styles
        add_action('wp_enqueue_scripts', array($this, 'enqueue_public_assets'));
        add_action('admin_enqueue_scripts', array($this, 'enqueue_admin_assets'));
        
        // Template loading for glossary
        add_filter('template_include', array($this, 'load_glossary_templates'));
        
        // Add glossary to navigation menu
        add_action('wp_nav_menu_items', array($this, 'add_glossary_to_menu'), 10, 2);
    }
    
    /**
     * Load plugin textdomain for translations
     */
    public function load_textdomain() {
        load_plugin_textdomain(
            'dave-biggers-policy',
            false,
            dirname(DB_POLICY_PLUGIN_BASENAME) . '/languages'
        );
    }
    
    /**
     * Enqueue public-facing assets
     */
    public function enqueue_public_assets() {
        // Main public stylesheet
        wp_enqueue_style(
            'db-policy-public',
            DB_POLICY_PLUGIN_URL . 'public/css/public-style.css',
            array(),
            DB_POLICY_VERSION
        );
        
        // Main public JavaScript
        wp_enqueue_script(
            'db-policy-public',
            DB_POLICY_PLUGIN_URL . 'public/js/public-script.js',
            array('jquery'),
            DB_POLICY_VERSION,
            true
        );
        
        // Localize script
        wp_localize_script('db-policy-public', 'dbPolicyAjax', array(
            'ajaxurl' => admin_url('admin-ajax.php'),
            'nonce' => wp_create_nonce('db_policy_public_nonce')
        ));
    }
    
    /**
     * Enqueue admin assets
     */
    public function enqueue_admin_assets($hook) {
        // Admin stylesheet
        wp_enqueue_style(
            'db-policy-admin',
            DB_POLICY_PLUGIN_URL . 'admin/css/admin-style.css',
            array(),
            DB_POLICY_VERSION
        );
        
        // Admin JavaScript
        wp_enqueue_script(
            'db-policy-admin',
            DB_POLICY_PLUGIN_URL . 'admin/js/admin-script.js',
            array('jquery'),
            DB_POLICY_VERSION,
            true
        );
    }
    
    /**
     * Load custom templates for glossary
     */
    public function load_glossary_templates($template) {
        if (is_post_type_archive('glossary_term')) {
            $custom_template = DB_POLICY_PLUGIN_DIR . 'templates/archive-glossary_term.php';
            if (file_exists($custom_template)) {
                return $custom_template;
            }
        }
        
        if (is_singular('glossary_term')) {
            $custom_template = DB_POLICY_PLUGIN_DIR . 'templates/single-glossary_term.php';
            if (file_exists($custom_template)) {
                return $custom_template;
            }
        }
        
        return $template;
    }
    
    /**
     * Add glossary link to navigation menu
     */
    public function add_glossary_to_menu($items, $args) {
        // Only add to primary menu
        if ($args->theme_location == 'primary') {
            $glossary_link = '<li class="menu-item menu-item-glossary">';
            $glossary_link .= '<a href="' . get_post_type_archive_link('glossary_term') . '">Voter Glossary</a>';
            $glossary_link .= '</li>';
            $items .= $glossary_link;
        }
        return $items;
    }
}

/**
 * Initialize the plugin
 */
function dave_biggers_policy_manager_init() {
    return Dave_Biggers_Policy_Manager::get_instance();
}

// Start the plugin
add_action('plugins_loaded', 'dave_biggers_policy_manager_init');

/**
 * Plugin activation hook
 */
function db_policy_activate() {
    // Flush rewrite rules to register custom post types and taxonomies
    flush_rewrite_rules();
    
    // Set default options
    add_option('db_policy_version', DB_POLICY_VERSION);
    add_option('db_policy_glossary_enabled', '1');
    
    // Create glossary categories on activation
    db_policy_create_default_glossary_categories();
}
register_activation_hook(__FILE__, 'db_policy_activate');

/**
 * Create default glossary categories
 */
function db_policy_create_default_glossary_categories() {
    $categories = array(
        'Voting & Elections',
        'Government Structure',
        'Budget & Finance',
        'Economic Development & Accountability',
        'Environmental & Sustainability',
        'Housing & Homelessness',
        'Public Safety & Policing',
        'Education',
        'Healthcare & Public Health',
        'Workforce Development',
        'Transportation & Infrastructure',
        'Government Accountability & Transparency',
        'Data Center Development'
    );
    
    foreach ($categories as $category) {
        if (!term_exists($category, 'glossary_category')) {
            wp_insert_term($category, 'glossary_category');
        }
    }
}

/**
 * Plugin deactivation hook
 */
function db_policy_deactivate() {
    // Flush rewrite rules
    flush_rewrite_rules();
}
register_deactivation_hook(__FILE__, 'db_policy_deactivate');

/**
 * Helper function to check if glossary is enabled
 */
function db_policy_is_glossary_enabled() {
    return get_option('db_policy_glossary_enabled', '1') === '1';
}

/**
 * Get glossary statistics
 */
function db_policy_get_glossary_stats() {
    $stats = array();
    
    // Total terms
    $stats['total_terms'] = wp_count_posts('glossary_term')->publish;
    
    // Terms by category
    $categories = get_terms(array(
        'taxonomy' => 'glossary_category',
        'hide_empty' => false
    ));
    
    $stats['categories'] = count($categories);
    $stats['terms_by_category'] = array();
    
    if (!empty($categories) && !is_wp_error($categories)) {
        foreach ($categories as $category) {
            $stats['terms_by_category'][$category->name] = $category->count;
        }
    }
    
    // Featured terms
    $featured_count = get_posts(array(
        'post_type' => 'glossary_term',
        'posts_per_page' => -1,
        'meta_query' => array(
            array(
                'key' => '_glossary_featured',
                'value' => '1',
                'compare' => '='
            )
        ),
        'fields' => 'ids'
    ));
    
    $stats['featured_terms'] = count($featured_count);
    
    // Campaign priority terms
    $campaign_count = get_posts(array(
        'post_type' => 'glossary_term',
        'posts_per_page' => -1,
        'meta_query' => array(
            array(
                'key' => '_glossary_priority',
                'value' => 'campaign',
                'compare' => '='
            )
        ),
        'fields' => 'ids'
    ));
    
    $stats['campaign_terms'] = count($campaign_count);
    
    return $stats;
}

/**
 * Get random glossary term
 * Useful for "Term of the Day" widgets
 */
function db_policy_get_random_term() {
    $args = array(
        'post_type' => 'glossary_term',
        'posts_per_page' => 1,
        'orderby' => 'rand',
        'post_status' => 'publish'
    );
    
    $random_term = get_posts($args);
    
    if (!empty($random_term)) {
        return $random_term[0];
    }
    
    return null;
}

/**
 * Shortcode: Display glossary term
 * Usage: [glossary_term name="Living Wage"]
 */
function db_policy_glossary_term_shortcode($atts) {
    $atts = shortcode_atts(array(
        'name' => '',
        'show_link' => 'yes'
    ), $atts);
    
    if (empty($atts['name'])) {
        return '';
    }
    
    $term = get_page_by_title($atts['name'], OBJECT, 'glossary_term');
    
    if (!$term) {
        return esc_html($atts['name']);
    }
    
    $output = '';
    
    if ($atts['show_link'] === 'yes') {
        $output = '<a href="' . get_permalink($term->ID) . '" class="glossary-term-link" title="View definition: ' . esc_attr($term->post_title) . '">';
        $output .= esc_html($term->post_title);
        $output .= '</a>';
    } else {
        $output = '<span class="glossary-term-inline">';
        $output .= esc_html($term->post_title);
        $output .= ': ' . wp_trim_words($term->post_content, 20);
        $output .= '</span>';
    }
    
    return $output;
}
add_shortcode('glossary_term', 'db_policy_glossary_term_shortcode');

/**
 * Shortcode: Display featured glossary terms
 * Usage: [featured_glossary_terms count="3"]
 */
function db_policy_featured_glossary_shortcode($atts) {
    $atts = shortcode_atts(array(
        'count' => 3
    ), $atts);
    
    $args = array(
        'post_type' => 'glossary_term',
        'posts_per_page' => intval($atts['count']),
        'meta_query' => array(
            array(
                'key' => '_glossary_featured',
                'value' => '1',
                'compare' => '='
            )
        )
    );
    
    $featured_terms = get_posts($args);
    
    if (empty($featured_terms)) {
        return '';
    }
    
    $output = '<div class="featured-glossary-terms">';
    $output .= '<h3>Featured Terms</h3>';
    $output .= '<div class="glossary-term-cards">';
    
    foreach ($featured_terms as $term) {
        $why_matters = get_post_meta($term->ID, '_glossary_why_matters', true);
        
        $output .= '<div class="glossary-term-card">';
        $output .= '<h4><a href="' . get_permalink($term->ID) . '">' . esc_html($term->post_title) . '</a></h4>';
        $output .= '<p>' . wp_trim_words($why_matters, 30) . '</p>';
        $output .= '<a href="' . get_permalink($term->ID) . '" class="read-more">Learn More →</a>';
        $output .= '</div>';
    }
    
    $output .= '</div>';
    $output .= '</div>';
    
    return $output;
}
add_shortcode('featured_glossary_terms', 'db_policy_featured_glossary_shortcode');

/**
 * Add glossary stats to dashboard
 */
function db_policy_dashboard_widget() {
    if (!db_policy_is_glossary_enabled()) {
        return;
    }
    
    wp_add_dashboard_widget(
        'db_policy_glossary_stats',
        'Voter Education Glossary Statistics',
        'db_policy_dashboard_widget_content'
    );
}
add_action('wp_dashboard_setup', 'db_policy_dashboard_widget');

/**
 * Dashboard widget content
 */
function db_policy_dashboard_widget_content() {
    $stats = db_policy_get_glossary_stats();
    
    echo '<div class="glossary-dashboard-stats">';
    echo '<p><strong>Total Terms:</strong> ' . $stats['total_terms'] . '</p>';
    echo '<p><strong>Categories:</strong> ' . $stats['categories'] . '</p>';
    echo '<p><strong>Featured Terms:</strong> ' . $stats['featured_terms'] . '</p>';
    echo '<p><strong>Campaign Essentials:</strong> ' . $stats['campaign_terms'] . '</p>';
    echo '<p style="margin-top: 15px;">';
    echo '<a href="' . admin_url('edit.php?post_type=glossary_term') . '" class="button button-primary">Manage Glossary</a> ';
    echo '<a href="' . admin_url('edit.php?post_type=glossary_term&page=glossary-importer') . '" class="button">Import Terms</a>';
    echo '</p>';
    echo '</div>';
}

// End of file
