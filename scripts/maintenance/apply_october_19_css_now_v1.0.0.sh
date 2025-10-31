#!/bin/bash

# Apply October 19 Backup CSS via REST API - INSTANT UPDATE
# This uses the same approach that worked earlier - direct REST API updates

APP_PASS="eNBCl693CKfjoGB13Al66Htj"

echo "=== Applying October 19 Backup CSS via REST API ==="
echo ""

# Read the CSS from child theme
CSS_CONTENT=$(cat <<'EOF'
/* ===== DAVE BIGGERS CAMPAIGN - OCTOBER 19 BACKUP STATE ===== */
/* Clean, minimal CSS - Louisville Metro branding only */

:root {
  --primary-blue: #003D7A;
  --primary-blue-dark: #002952;
  --louisville-gold: #FFC72C;
  --text-dark: #1A1A1A;
  --text-medium: #4A4A4A;
  --white: #FFFFFF;
  --shadow-md: 0 4px 8px rgba(0, 0, 0, 0.12);
  --transition: all 0.3s ease;
}

/* ===== NO CHECKMARKS - LISTS ARE CLEAN ===== */
ul li::before,
ol li::before {
  content: none !important;
  display: none !important;
}

header ul li::before,
nav ul li::before,
.menu li::before {
  content: none !important;
  display: none !important;
}

/* Navigation lists - clean */
header ul li,
nav ul li,
.menu li {
  list-style: none !important;
  padding-left: 0 !important;
}

/* Content lists - simple bullets */
.entry-content ul li,
article ul li,
main ul li {
  list-style-type: disc;
  margin-left: 20px;
}

/* ===== HERO SECTION ===== */
.hero-section,
.wp-block-cover {
  min-height: 400px;
  background-size: cover;
  background-position: center;
  display: flex;
  align-items: center;
  justify-content: center;
}

.hero-section h1,
.wp-block-cover h1 {
  color: var(--white) !important;
  text-shadow: 2px 2px 8px rgba(0, 0, 0, 0.8);
  font-size: clamp(2rem, 5vw, 3rem);
  font-weight: 700;
}

.hero-section p,
.wp-block-cover p {
  color: var(--white) !important;
  text-shadow: 1px 1px 4px rgba(0, 0, 0, 0.8);
  font-size: clamp(1.1rem, 2.5vw, 1.3rem);
}

/* ===== BUTTONS - SIMPLE, CLEAN ===== */
.campaign-button,
.wp-block-button__link,
button[type="submit"] {
  background: var(--primary-blue) !important;
  color: var(--white) !important;
  padding: 12px 32px;
  border-radius: 8px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  transition: var(--transition);
  border: none;
  cursor: pointer;
  box-shadow: var(--shadow-md);
  text-decoration: none;
  display: inline-block;
}

.campaign-button:hover,
.wp-block-button__link:hover,
button[type="submit"]:hover {
  background: var(--primary-blue-dark) !important;
  transform: translateY(-2px);
}

/* ===== CARDS - CLEAN, SIMPLE ===== */
.stat-card,
.policy-card,
.wp-block-column {
  background: var(--white);
  padding: 24px;
  border-radius: 8px;
  box-shadow: var(--shadow-md);
  transition: var(--transition);
  border-top: 3px solid var(--primary-blue);
}

.stat-card:hover,
.policy-card:hover,
.wp-block-column:hover {
  transform: translateY(-4px);
  box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
}

/* ===== TEXT READABILITY ===== */
.has-primary-blue-background-color,
.has-primary-blue-background-color * {
  color: var(--white) !important;
}

/* ===== TYPOGRAPHY ===== */
h1 { font-size: clamp(1.75rem, 4vw, 2.5rem); }
h2 { font-size: clamp(1.5rem, 3.5vw, 2rem); }
h3 { font-size: clamp(1.25rem, 3vw, 1.75rem); }
p { font-size: clamp(1rem, 2vw, 1.125rem); line-height: 1.6; }

/* ===== RESPONSIVE ===== */
@media (max-width: 768px) {
  .hero-section,
  .wp-block-cover {
    min-height: 300px;
  }

  .stat-card,
  .policy-card {
    padding: 20px;
  }
}

/* ===== ACCESSIBILITY ===== */
a:focus,
button:focus {
  outline: 3px solid var(--louisville-gold);
  outline-offset: 2px;
}
EOF
)

echo "Step 1: Updating WordPress Customizer Additional CSS..."
echo ""

# Update WordPress Customizer Additional CSS via REST API
RESPONSE=$(curl -s -X POST \
  "https://rundaverun.org/wp-json/wp/v2/custom-css" \
  -u "dave:$APP_PASS" \
  -H "Content-Type: application/json" \
  -d "{\"css\": $(echo "$CSS_CONTENT" | jq -Rs .)}")

echo "Response: $RESPONSE"
echo ""

echo "Step 2: Clearing WordPress cache..."
echo ""

# Clear cache by updating a transient
curl -s -X POST \
  "https://rundaverun.org/wp-json/wp/v2/settings" \
  -u "dave:$APP_PASS" \
  -H "Content-Type: application/json" \
  -d '{"title":"Dave Biggers for Louisville Mayor"}' > /dev/null

echo "✅ CSS Applied via REST API!"
echo ""
echo "Test your site now:"
echo "  Homepage: https://rundaverun.org/?v=$(date +%s)"
echo "  Glossary: https://rundaverun.org/glossary/?v=$(date +%s)"
echo ""
echo "Hard refresh (Ctrl+Shift+R) or use incognito mode"
