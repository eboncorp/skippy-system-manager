<?php
/**
 * Single Template for Glossary Term
 *
 * Displays individual glossary term with full details
 * Template: single-glossary_term.php
 *
 * @package Dave_Biggers_Policy_Manager
 * @since 1.1.0
 */

get_header(); ?>

<div class="glossary-single-container">
    <?php while (have_posts()) : the_post(); 
        // Get meta data
        $why_matters = get_post_meta(get_the_ID(), '_glossary_why_matters', true);
        $louisville_context = get_post_meta(get_the_ID(), '_glossary_louisville_context', true);
        $data_stats = get_post_meta(get_the_ID(), '_glossary_data_stats', true);
        $campaign_alignment = get_post_meta(get_the_ID(), '_glossary_campaign_alignment', true);
        $related_term_ids = get_post_meta(get_the_ID(), '_glossary_related_terms', true);
        $priority = get_post_meta(get_the_ID(), '_glossary_priority', true);
        $is_featured = get_post_meta(get_the_ID(), '_glossary_featured', true);
        
        // Get taxonomies
        $categories = get_the_terms(get_the_ID(), 'glossary_category');
        $tags = get_the_terms(get_the_ID(), 'glossary_tag');
        ?>
        
        <article id="post-<?php the_ID(); ?>" <?php post_class('glossary-term-single'); ?>>
            
            <!-- Back to Glossary Link -->
            <div class="glossary-navigation-top">
                <a href="<?php echo get_post_type_archive_link('glossary_term'); ?>" class="back-to-glossary">
                    ← Back to Glossary Index
                </a>
            </div>
            
            <!-- Term Header -->
            <header class="glossary-term-header">
                <h1 class="glossary-term-title">
                    <?php the_title(); ?>
                    <?php if ($priority === 'campaign') : ?>
                        <span class="priority-badge">Campaign Essential</span>
                    <?php endif; ?>
                    <?php if ($is_featured) : ?>
                        <span class="featured-badge">Featured</span>
                    <?php endif; ?>
                </h1>
                
                <?php if ($categories && !is_wp_error($categories)) : ?>
                    <div class="term-meta-categories">
                        <?php foreach ($categories as $category) : ?>
                            <a href="<?php echo get_term_link($category); ?>" class="term-category-link">
                                <?php echo esc_html($category->name); ?>
                            </a>
                        <?php endforeach; ?>
                    </div>
                <?php endif; ?>
            </header>
            
            <!-- Main Content -->
            <div class="glossary-term-content">
                
                <!-- Definition Section -->
                <section class="glossary-section definition-section">
                    <h2 class="section-heading">Definition</h2>
                    <div class="section-content">
                        <?php the_content(); ?>
                    </div>
                </section>
                
                <!-- Why This Matters Section -->
                <?php if ($why_matters) : ?>
                    <section class="glossary-section why-matters-section">
                        <h2 class="section-heading">
                            <span class="icon">💡</span>
                            Why This Matters
                        </h2>
                        <div class="section-content highlighted-content">
                            <?php echo wpautop(esc_html($why_matters)); ?>
                        </div>
                    </section>
                <?php endif; ?>
                
                <!-- Louisville Context Section -->
                <?php if ($louisville_context) : ?>
                    <section class="glossary-section louisville-section">
                        <h2 class="section-heading">
                            <span class="icon">📍</span>
                            Louisville Metro Context
                        </h2>
                        <div class="section-content">
                            <?php echo wpautop(esc_html($louisville_context)); ?>
                        </div>
                    </section>
                <?php endif; ?>
                
                <!-- Data & Statistics Section -->
                <?php if ($data_stats) : ?>
                    <section class="glossary-section data-section">
                        <h2 class="section-heading">
                            <span class="icon">📊</span>
                            Data & Statistics
                        </h2>
                        <div class="section-content data-content">
                            <?php echo wpautop(esc_html($data_stats)); ?>
                        </div>
                    </section>
                <?php endif; ?>
                
                <!-- Campaign Alignment Section -->
                <?php if ($campaign_alignment) : ?>
                    <section class="glossary-section campaign-section">
                        <h2 class="section-heading">
                            <span class="icon">🎯</span>
                            How This Relates to Our Campaign
                        </h2>
                        <div class="section-content campaign-content">
                            <?php echo wpautop(esc_html($campaign_alignment)); ?>
                            <p class="campaign-cta">
                                <a href="<?php echo home_url('/our-plan'); ?>" class="button-link">
                                    Read Our Full Plan for Louisville →
                                </a>
                            </p>
                        </div>
                    </section>
                <?php endif; ?>
                
            </div>
            
            <!-- Related Terms -->
            <?php if (!empty($related_term_ids) && is_array($related_term_ids)) : 
                $related_terms = get_posts(array(
                    'post_type' => 'glossary_term',
                    'post__in' => $related_term_ids,
                    'posts_per_page' => -1,
                    'orderby' => 'title',
                    'order' => 'ASC'
                ));
                
                if (!empty($related_terms)) :
            ?>
                <aside class="related-terms-section">
                    <h2 class="section-heading">Related Terms</h2>
                    <div class="related-terms-grid">
                        <?php foreach ($related_terms as $related_term) : 
                            $related_categories = get_the_terms($related_term->ID, 'glossary_category');
                            ?>
                            <div class="related-term-card">
                                <h3 class="related-term-title">
                                    <a href="<?php echo get_permalink($related_term->ID); ?>">
                                        <?php echo get_the_title($related_term->ID); ?>
                                    </a>
                                </h3>
                                <?php if ($related_categories && !is_wp_error($related_categories)) : ?>
                                    <span class="related-term-category">
                                        <?php echo esc_html($related_categories[0]->name); ?>
                                    </span>
                                <?php endif; ?>
                            </div>
                        <?php endforeach; ?>
                    </div>
                </aside>
            <?php 
                endif;
            endif; 
            ?>
            
            <!-- Tags -->
            <?php if ($tags && !is_wp_error($tags)) : ?>
                <footer class="glossary-term-footer">
                    <div class="term-tags">
                        <span class="tags-label">Tags:</span>
                        <?php foreach ($tags as $tag) : ?>
                            <a href="<?php echo get_term_link($tag); ?>" class="term-tag">
                                <?php echo esc_html($tag->name); ?>
                            </a>
                        <?php endforeach; ?>
                    </div>
                </footer>
            <?php endif; ?>
            
            <!-- Navigation to Next/Previous Term -->
            <nav class="glossary-term-navigation">
                <div class="nav-links">
                    <?php
                    $prev_post = get_previous_post(true, '', 'glossary_category');
                    $next_post = get_next_post(true, '', 'glossary_category');
                    
                    if ($prev_post) : ?>
                        <div class="nav-previous">
                            <a href="<?php echo get_permalink($prev_post); ?>">
                                <span class="nav-subtitle">← Previous Term</span>
                                <span class="nav-title"><?php echo get_the_title($prev_post); ?></span>
                            </a>
                        </div>
                    <?php endif; ?>
                    
                    <?php if ($next_post) : ?>
                        <div class="nav-next">
                            <a href="<?php echo get_permalink($next_post); ?>">
                                <span class="nav-subtitle">Next Term →</span>
                                <span class="nav-title"><?php echo get_the_title($next_post); ?></span>
                            </a>
                        </div>
                    <?php endif; ?>
                </div>
            </nav>
            
            <!-- Share & Actions -->
            <div class="glossary-actions">
                <button onclick="window.print()" class="action-button print-button">
                    🖨️ Print This Term
                </button>
                <button onclick="navigator.share ? navigator.share({title: '<?php echo esc_js(get_the_title()); ?>', url: '<?php echo esc_url(get_permalink()); ?>'}) : alert('Sharing not supported')" class="action-button share-button">
                    📤 Share This Term
                </button>
                <a href="<?php echo get_post_type_archive_link('glossary_term'); ?>" class="action-button index-button">
                    📖 View Full Glossary
                </a>
            </div>
            
        </article>
        
    <?php endwhile; ?>
</div>

<style>
/* Single Glossary Term Styles */
.glossary-single-container {
    max-width: 900px;
    margin: 0 auto;
    padding: 40px 20px;
}

.glossary-navigation-top {
    margin-bottom: 20px;
}

.back-to-glossary {
    display: inline-block;
    padding: 8px 15px;
    background: #f0f0f1;
    color: #1d2327;
    text-decoration: none;
    border-radius: 4px;
    transition: background 0.3s;
}

.back-to-glossary:hover {
    background: #dcdcde;
}

.glossary-term-header {
    margin-bottom: 40px;
    padding-bottom: 20px;
    border-bottom: 3px solid #0073aa;
}

.glossary-term-title {
    font-size: 2.5em;
    color: #1d2327;
    margin-bottom: 15px;
    line-height: 1.2;
}

.priority-badge {
    display: inline-block;
    padding: 5px 12px;
    background: #d63638;
    color: white;
    font-size: 0.4em;
    border-radius: 4px;
    margin-left: 15px;
    vertical-align: middle;
    font-weight: normal;
}

.featured-badge {
    display: inline-block;
    padding: 5px 12px;
    background: #00a32a;
    color: white;
    font-size: 0.4em;
    border-radius: 4px;
    margin-left: 10px;
    vertical-align: middle;
    font-weight: normal;
}

.term-meta-categories {
    margin-top: 15px;
}

.term-category-link {
    display: inline-block;
    padding: 6px 14px;
    background: #f0f0f1;
    color: #1d2327;
    text-decoration: none;
    border-radius: 4px;
    margin-right: 8px;
    font-size: 0.9em;
    transition: all 0.3s;
}

.term-category-link:hover {
    background: #0073aa;
    color: white;
}

.glossary-term-content {
    margin-bottom: 50px;
}

.glossary-section {
    margin-bottom: 40px;
    padding: 30px;
    background: #f9f9f9;
    border-radius: 8px;
}

.glossary-section.definition-section {
    background: white;
    border: 2px solid #0073aa;
}

.glossary-section.why-matters-section {
    background: #fff9e6;
    border-left: 5px solid #f0b429;
}

.glossary-section.louisville-section {
    background: #e8f4f8;
    border-left: 5px solid #0073aa;
}

.glossary-section.data-section {
    background: #f0f6f0;
    border-left: 5px solid #00a32a;
}

.glossary-section.campaign-section {
    background: #fff0f0;
    border-left: 5px solid #d63638;
}

.section-heading {
    margin-top: 0;
    margin-bottom: 20px;
    color: #1d2327;
    font-size: 1.5em;
    display: flex;
    align-items: center;
    gap: 10px;
}

.section-heading .icon {
    font-size: 1.2em;
}

.section-content {
    line-height: 1.7;
    color: #50575e;
}

.section-content p:last-child {
    margin-bottom: 0;
}

.highlighted-content {
    font-size: 1.05em;
    font-weight: 500;
}

.data-content {
    font-family: 'Courier New', monospace;
    font-size: 0.95em;
}

.campaign-content {
    font-weight: 500;
}

.campaign-cta {
    margin-top: 20px;
    padding-top: 20px;
    border-top: 1px solid rgba(0,0,0,0.1);
}

.button-link {
    display: inline-block;
    padding: 12px 24px;
    background: #d63638;
    color: white;
    text-decoration: none;
    border-radius: 4px;
    font-weight: 600;
    transition: background 0.3s;
}

.button-link:hover {
    background: #a02123;
}

.related-terms-section {
    margin-bottom: 40px;
    padding: 30px;
    background: #f0f0f1;
    border-radius: 8px;
}

.related-terms-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
    gap: 15px;
    margin-top: 20px;
}

.related-term-card {
    background: white;
    padding: 15px;
    border-radius: 6px;
    border-left: 3px solid #0073aa;
    transition: all 0.3s;
}

.related-term-card:hover {
    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    transform: translateY(-2px);
}

.related-term-title {
    margin: 0 0 8px 0;
    font-size: 1.1em;
}

.related-term-title a {
    color: #0073aa;
    text-decoration: none;
}

.related-term-title a:hover {
    text-decoration: underline;
}

.related-term-category {
    display: inline-block;
    padding: 3px 8px;
    background: #f0f0f1;
    color: #50575e;
    font-size: 0.8em;
    border-radius: 3px;
}

.glossary-term-footer {
    padding: 20px 0;
    border-top: 1px solid #dcdcde;
    margin-bottom: 30px;
}

.term-tags {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 10px;
}

.tags-label {
    font-weight: 600;
    color: #1d2327;
}

.term-tag {
    display: inline-block;
    padding: 5px 12px;
    background: #f0f0f1;
    color: #50575e;
    text-decoration: none;
    border-radius: 3px;
    font-size: 0.9em;
    transition: all 0.3s;
}

.term-tag:hover {
    background: #0073aa;
    color: white;
}

.glossary-term-navigation {
    margin: 40px 0;
    padding: 30px;
    background: #f6f7f7;
    border-radius: 8px;
}

.nav-links {
    display: flex;
    justify-content: space-between;
    gap: 20px;
}

.nav-previous,
.nav-next {
    flex: 1;
}

.nav-previous a,
.nav-next a {
    display: block;
    padding: 15px;
    background: white;
    border: 2px solid #dcdcde;
    border-radius: 6px;
    text-decoration: none;
    transition: all 0.3s;
}

.nav-previous a:hover,
.nav-next a:hover {
    border-color: #0073aa;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.nav-next {
    text-align: right;
}

.nav-subtitle {
    display: block;
    font-size: 0.85em;
    color: #646970;
    margin-bottom: 5px;
}

.nav-title {
    display: block;
    color: #0073aa;
    font-weight: 600;
}

.glossary-actions {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    justify-content: center;
    padding: 20px;
    background: #f0f0f1;
    border-radius: 8px;
}

.action-button {
    padding: 10px 20px;
    background: white;
    color: #1d2327;
    border: 2px solid #dcdcde;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.95em;
    text-decoration: none;
    transition: all 0.3s;
}

.action-button:hover {
    background: #0073aa;
    color: white;
    border-color: #0073aa;
}

/* Print Styles */
@media print {
    .glossary-navigation-top,
    .glossary-term-navigation,
    .glossary-actions {
        display: none;
    }
    
    .glossary-section {
        break-inside: avoid;
        page-break-inside: avoid;
    }
}

/* Responsive Design */
@media (max-width: 768px) {
    .glossary-term-title {
        font-size: 1.8em;
    }
    
    .priority-badge,
    .featured-badge {
        display: block;
        margin: 10px 0;
    }
    
    .nav-links {
        flex-direction: column;
    }
    
    .nav-next {
        text-align: left;
    }
    
    .glossary-actions {
        flex-direction: column;
    }
    
    .action-button {
        width: 100%;
    }
}
</style>

<?php get_footer(); ?>
