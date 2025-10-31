<?php
/**
 * Archive Template for Glossary Terms
 *
 * Displays the glossary index with filtering and search
 * Template: archive-glossary_term.php
 *
 * @package Dave_Biggers_Policy_Manager
 * @since 1.1.0
 */

get_header(); ?>

<div class="glossary-archive-container">
    <header class="glossary-header">
        <h1 class="glossary-title">Voter Education Glossary</h1>
        <p class="glossary-subtitle">Understanding Louisville Metro Government & Policy</p>
        <p class="glossary-intro">
            This comprehensive glossary explains 468+ terms related to Louisville Metro government, 
            policy, and civic engagement. Each term includes Louisville-specific context and explains 
            why it matters to you as a voter.
        </p>
    </header>

    <!-- Category Filter -->
    <div class="glossary-filters">
        <div class="filter-section">
            <h3>Filter by Category:</h3>
            <?php
            $categories = get_terms(array(
                'taxonomy' => 'glossary_category',
                'hide_empty' => true,
                'orderby' => 'name',
                'order' => 'ASC'
            ));
            
            if (!empty($categories) && !is_wp_error($categories)) :
                $current_cat = get_query_var('glossary_category');
                ?>
                <ul class="glossary-category-filter">
                    <li>
                        <a href="<?php echo get_post_type_archive_link('glossary_term'); ?>" 
                           class="<?php echo empty($current_cat) ? 'active' : ''; ?>">
                            All Categories
                        </a>
                    </li>
                    <?php foreach ($categories as $category) : ?>
                        <li>
                            <a href="<?php echo get_term_link($category); ?>"
                               class="<?php echo $current_cat === $category->slug ? 'active' : ''; ?>">
                                <?php echo esc_html($category->name); ?>
                                <span class="count">(<?php echo $category->count; ?>)</span>
                            </a>
                        </li>
                    <?php endforeach; ?>
                </ul>
            <?php endif; ?>
        </div>
        
        <!-- Alphabetical Filter -->
        <div class="filter-section">
            <h3>Jump to Letter:</h3>
            <div class="alphabetical-filter">
                <?php
                $letters = range('A', 'Z');
                foreach ($letters as $letter) :
                    ?>
                    <a href="#letter-<?php echo strtolower($letter); ?>" class="letter-link">
                        <?php echo $letter; ?>
                    </a>
                <?php endforeach; ?>
            </div>
        </div>
        
        <!-- Search -->
        <div class="filter-section">
            <h3>Search Terms:</h3>
            <form role="search" method="get" class="glossary-search-form" action="<?php echo home_url('/'); ?>">
                <input type="hidden" name="post_type" value="glossary_term">
                <input type="search" 
                       class="glossary-search-field" 
                       placeholder="Search glossary..." 
                       value="<?php echo get_search_query(); ?>" 
                       name="s">
                <button type="submit" class="glossary-search-submit">Search</button>
            </form>
        </div>
    </div>

    <!-- Featured Terms (if any) -->
    <?php
    $featured_args = array(
        'post_type' => 'glossary_term',
        'posts_per_page' => 3,
        'meta_query' => array(
            array(
                'key' => '_glossary_featured',
                'value' => '1',
                'compare' => '='
            )
        )
    );
    $featured_query = new WP_Query($featured_args);
    
    if ($featured_query->have_posts()) : ?>
        <div class="glossary-featured-section">
            <h2>Featured Terms</h2>
            <div class="glossary-featured-grid">
                <?php while ($featured_query->have_posts()) : $featured_query->the_post(); ?>
                    <div class="glossary-featured-term">
                        <h3>
                            <a href="<?php the_permalink(); ?>">
                                <?php the_title(); ?>
                            </a>
                        </h3>
                        <div class="featured-excerpt">
                            <?php 
                            $why_matters = get_post_meta(get_the_ID(), '_glossary_why_matters', true);
                            echo wp_trim_words($why_matters, 30);
                            ?>
                        </div>
                        <a href="<?php the_permalink(); ?>" class="read-more">Read More →</a>
                    </div>
                <?php endwhile; ?>
            </div>
        </div>
        <?php wp_reset_postdata(); ?>
    <?php endif; ?>

    <!-- Terms List -->
    <div class="glossary-terms-list">
        <?php
        if (have_posts()) :
            // Group terms by first letter
            $terms_by_letter = array();
            while (have_posts()) : the_post();
                $first_letter = strtoupper(substr(get_the_title(), 0, 1));
                if (!isset($terms_by_letter[$first_letter])) {
                    $terms_by_letter[$first_letter] = array();
                }
                $terms_by_letter[$first_letter][] = get_post();
            endwhile;
            
            // Display grouped terms
            ksort($terms_by_letter);
            foreach ($terms_by_letter as $letter => $terms) :
                ?>
                <div class="glossary-letter-section" id="letter-<?php echo strtolower($letter); ?>">
                    <h2 class="letter-heading"><?php echo $letter; ?></h2>
                    <div class="terms-in-letter">
                        <?php foreach ($terms as $term) : 
                            setup_postdata($term);
                            $categories = get_the_terms($term->ID, 'glossary_category');
                            $priority = get_post_meta($term->ID, '_glossary_priority', true);
                            ?>
                            <div class="glossary-term-item <?php echo $priority === 'campaign' ? 'priority-campaign' : ''; ?>">
                                <h3 class="term-title">
                                    <a href="<?php echo get_permalink($term->ID); ?>">
                                        <?php echo get_the_title($term->ID); ?>
                                    </a>
                                    <?php if ($priority === 'campaign') : ?>
                                        <span class="priority-badge">Campaign Essential</span>
                                    <?php endif; ?>
                                </h3>
                                
                                <?php if ($categories && !is_wp_error($categories)) : ?>
                                    <div class="term-categories">
                                        <?php foreach ($categories as $category) : ?>
                                            <span class="term-category">
                                                <?php echo esc_html($category->name); ?>
                                            </span>
                                        <?php endforeach; ?>
                                    </div>
                                <?php endif; ?>
                                
                                <div class="term-excerpt">
                                    <?php echo wp_trim_words(get_the_excerpt($term->ID), 40); ?>
                                </div>
                                
                                <a href="<?php echo get_permalink($term->ID); ?>" class="term-read-more">
                                    Read Full Definition →
                                </a>
                            </div>
                        <?php endforeach; ?>
                        <?php wp_reset_postdata(); ?>
                    </div>
                </div>
            <?php endforeach;
        else :
            ?>
            <div class="no-terms-found">
                <p>No glossary terms found. <?php if (is_search()) : ?>Try a different search.<?php endif; ?></p>
            </div>
        <?php endif; ?>
    </div>

    <!-- Pagination -->
    <?php
    the_posts_pagination(array(
        'mid_size' => 2,
        'prev_text' => '← Previous',
        'next_text' => 'Next →',
    ));
    ?>
</div>

<style>
/* Glossary Archive Styles */
.glossary-archive-container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 40px 20px;
}

.glossary-header {
    text-align: center;
    margin-bottom: 40px;
    padding-bottom: 30px;
    border-bottom: 3px solid #0073aa;
}

.glossary-title {
    font-size: 2.5em;
    color: #1d2327;
    margin-bottom: 10px;
}

.glossary-subtitle {
    font-size: 1.3em;
    color: #646970;
    margin-bottom: 15px;
}

.glossary-intro {
    max-width: 800px;
    margin: 0 auto;
    line-height: 1.6;
    color: #50575e;
}

.glossary-filters {
    background: #f6f7f7;
    padding: 30px;
    border-radius: 8px;
    margin-bottom: 40px;
}

.filter-section {
    margin-bottom: 25px;
}

.filter-section:last-child {
    margin-bottom: 0;
}

.filter-section h3 {
    margin-top: 0;
    margin-bottom: 15px;
    color: #1d2327;
}

.glossary-category-filter {
    list-style: none;
    padding: 0;
    margin: 0;
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
}

.glossary-category-filter li a {
    display: inline-block;
    padding: 8px 15px;
    background: white;
    border: 2px solid #ddd;
    border-radius: 4px;
    text-decoration: none;
    color: #1d2327;
    transition: all 0.3s;
}

.glossary-category-filter li a:hover,
.glossary-category-filter li a.active {
    background: #0073aa;
    color: white;
    border-color: #0073aa;
}

.glossary-category-filter .count {
    opacity: 0.7;
    font-size: 0.9em;
}

.alphabetical-filter {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
}

.letter-link {
    display: inline-block;
    width: 35px;
    height: 35px;
    line-height: 35px;
    text-align: center;
    background: white;
    border: 2px solid #ddd;
    border-radius: 4px;
    text-decoration: none;
    color: #1d2327;
    font-weight: 600;
    transition: all 0.3s;
}

.letter-link:hover {
    background: #0073aa;
    color: white;
    border-color: #0073aa;
}

.glossary-search-form {
    display: flex;
    gap: 10px;
    max-width: 500px;
}

.glossary-search-field {
    flex: 1;
    padding: 10px 15px;
    border: 2px solid #ddd;
    border-radius: 4px;
    font-size: 16px;
}

.glossary-search-submit {
    padding: 10px 25px;
    background: #0073aa;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 16px;
    font-weight: 600;
    transition: background 0.3s;
}

.glossary-search-submit:hover {
    background: #005a87;
}

.glossary-featured-section {
    margin-bottom: 50px;
    padding: 30px;
    background: #e8f4f8;
    border-radius: 8px;
}

.glossary-featured-section h2 {
    margin-top: 0;
    color: #1d2327;
}

.glossary-featured-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 20px;
}

.glossary-featured-term {
    background: white;
    padding: 20px;
    border-radius: 6px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.glossary-featured-term h3 {
    margin-top: 0;
}

.glossary-featured-term h3 a {
    color: #0073aa;
    text-decoration: none;
}

.glossary-featured-term h3 a:hover {
    text-decoration: underline;
}

.featured-excerpt {
    margin: 15px 0;
    line-height: 1.6;
    color: #50575e;
}

.read-more {
    color: #0073aa;
    text-decoration: none;
    font-weight: 600;
}

.read-more:hover {
    text-decoration: underline;
}

.glossary-letter-section {
    margin-bottom: 40px;
}

.letter-heading {
    font-size: 2em;
    color: #0073aa;
    border-bottom: 2px solid #0073aa;
    padding-bottom: 10px;
    margin-bottom: 20px;
}

.glossary-term-item {
    background: white;
    padding: 25px;
    margin-bottom: 20px;
    border-radius: 6px;
    border-left: 4px solid #ddd;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    transition: all 0.3s;
}

.glossary-term-item:hover {
    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    border-left-color: #0073aa;
}

.glossary-term-item.priority-campaign {
    border-left-color: #d63638;
    background: #fff8f8;
}

.term-title {
    margin-top: 0;
    margin-bottom: 10px;
}

.term-title a {
    color: #1d2327;
    text-decoration: none;
}

.term-title a:hover {
    color: #0073aa;
}

.priority-badge {
    display: inline-block;
    padding: 3px 10px;
    background: #d63638;
    color: white;
    font-size: 0.7em;
    border-radius: 3px;
    margin-left: 10px;
    vertical-align: middle;
}

.term-categories {
    margin-bottom: 12px;
}

.term-category {
    display: inline-block;
    padding: 4px 10px;
    background: #f0f0f1;
    color: #50575e;
    font-size: 0.85em;
    border-radius: 3px;
    margin-right: 8px;
}

.term-excerpt {
    margin: 15px 0;
    line-height: 1.6;
    color: #50575e;
}

.term-read-more {
    color: #0073aa;
    text-decoration: none;
    font-weight: 600;
}

.term-read-more:hover {
    text-decoration: underline;
}

.no-terms-found {
    text-align: center;
    padding: 60px 20px;
    background: #f6f7f7;
    border-radius: 8px;
}

/* Responsive Design */
@media (max-width: 768px) {
    .glossary-title {
        font-size: 2em;
    }
    
    .glossary-search-form {
        flex-direction: column;
    }
    
    .glossary-search-submit {
        width: 100%;
    }
    
    .glossary-featured-grid {
        grid-template-columns: 1fr;
    }
}
</style>

<?php get_footer(); ?>
