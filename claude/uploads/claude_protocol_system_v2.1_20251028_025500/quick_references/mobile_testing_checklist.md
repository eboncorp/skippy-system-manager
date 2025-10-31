# Mobile Testing Checklist

**Date Created**: 2025-10-28
**Purpose**: Quick checklist for mobile testing before deployment
**Applies To**: All web development (WordPress sites, web apps)
**Priority**: HIGH (mobile usage is 50%+ of traffic)

## Overview

Mobile testing is critical as 50% or more of web traffic comes from mobile devices. This checklist ensures mobile users have a good experience.

---

## Pre-Testing Setup

### Test Environments

1. **Browser DevTools** (Quick check)
   - Chrome: F12 → Toggle device toolbar (Ctrl+Shift+M)
   - Firefox: F12 → Responsive Design Mode (Ctrl+Shift+M)
   - Safari: Develop → Enter Responsive Design Mode

2. **Actual Devices** (Final verification)
   - iPhone/iPad (iOS)
   - Android phone/tablet
   - Different screen sizes if available

### Common Mobile Screen Sizes

| Device Type       | Width (px) | Height (px) | Common Devices                    |
|-------------------|------------|-------------|-----------------------------------|
| Small Phone       | 320        | 568         | iPhone SE                         |
| Standard Phone    | 375        | 667         | iPhone 6/7/8                      |
| Large Phone       | 414        | 896         | iPhone 11/12/13                   |
| Extra Large Phone | 428        | 926         | iPhone 14 Pro Max                 |
| Tablet Portrait   | 768        | 1024        | iPad                              |
| Tablet Landscape  | 1024       | 768         | iPad (rotated)                    |

---

## Visual/Layout Testing

### Viewport & Scaling

- [ ] **Viewport meta tag present**
  ```html
  <meta name="viewport" content="width=device-width, initial-scale=1">
  ```
  - Check in <head> section
  - Without this, site will render at desktop width on mobile

- [ ] **No horizontal scrolling**
  - Scroll horizontally on page
  - All content should fit within screen width
  - Check at different screen widths (320px, 375px, 414px)

- [ ] **Text readable without zooming**
  - Body text minimum 16px
  - Headings appropriately sized
  - No tiny text that requires zoom

- [ ] **Images scale properly**
  - Images don't overflow container
  - Images maintain aspect ratio
  - No pixelated/stretched images
  - Images load (not broken)

### Layout & Spacing

- [ ] **Content stacks vertically**
  - Multi-column layouts become single column
  - Sidebars move below main content
  - No overlapping content

- [ ] **Adequate spacing**
  - Elements not cramped together
  - Comfortable padding/margins
  - White space used effectively

- [ ] **No cut-off content**
  - All text visible
  - No partially hidden elements
  - Headers/footers display completely

- [ ] **Proper text wrapping**
  - Long words break appropriately
  - No text overflow
  - Links don't break awkwardly

---

## Navigation Testing

### Mobile Menu

- [ ] **Mobile menu exists**
  - Hamburger icon (≡) or similar visible
  - Positioned prominently (usually top-right)
  - Obvious it's clickable

- [ ] **Menu opens/closes**
  - Tap menu button → menu opens
  - Tap again or close button → menu closes
  - Smooth animation (not jarring)

- [ ] **Menu items accessible**
  - All menu items visible
  - Can scroll if many items
  - Submenu items accessible (if applicable)

- [ ] **Menu items clickable**
  - All links work
  - Tap area adequate (44x44px minimum)
  - Visual feedback on tap

- [ ] **Menu overlay works**
  - Menu slides in/overlays page
  - Background dims or blurs
  - Can close by tapping outside (if designed that way)

- [ ] **z-index correct**
  - Menu appears above all other content
  - Not hidden behind other elements
  - Close button accessible

### Navigation Flow

- [ ] **Back navigation works**
  - Browser back button works
  - On-page back buttons work (if any)

- [ ] **Breadcrumbs visible** (if applicable)
  - Display on mobile
  - Not too small
  - Functional

- [ ] **Footer navigation accessible**
  - Footer links visible and clickable
  - Not too small
  - Important links present

---

## Touch Interaction Testing

### Touch Targets

- [ ] **Minimum touch target size**
  - 44x44px minimum (Apple guideline)
  - 48x48px recommended (Google guideline)
  - Test all buttons, links, form fields

- [ ] **Adequate spacing between targets**
  - At least 8px between clickable elements
  - Prevents mis-taps
  - Especially important for small buttons

- [ ] **Visual feedback on touch**
  - Buttons change appearance when tapped
  - Links show active state
  - User knows tap registered

### Gestures

- [ ] **Tap works**
  - Single tap activates links/buttons
  - No delay (should feel instant)

- [ ] **Scroll works**
  - Can scroll smoothly up/down
  - Can scroll lists/dropdowns
  - Momentum scrolling feels natural

- [ ] **Pinch zoom** (if applicable)
  - Can zoom in/out on images (if desired)
  - Or zooming disabled intentionally (for web apps)

- [ ] **Swipe works** (if applicable)
  - Image galleries swipeable
  - Carousels swipeable
  - Other swipe interactions work

### Forms on Mobile

- [ ] **Form fields large enough**
  - Input height minimum 44px
  - Text inside input readable (16px+)
  - Labels visible and clear

- [ ] **Correct keyboard type**
  - Email fields: `type="email"` (shows @ key)
  - Phone fields: `type="tel"` (shows number pad)
  - Number fields: `type="number"` (shows numbers)
  - URLs: `type="url"` (shows .com key)

- [ ] **Form submits correctly**
  - Submit button large and obvious
  - Submission works
  - Success message displays

- [ ] **Validation visible**
  - Error messages show clearly
  - Red/warning colors visible
  - User knows what to fix

---

## Content Testing

### Text Content

- [ ] **Font sizes appropriate**
  - Body text: 16px minimum
  - Small text: 14px minimum
  - Headings scaled appropriately

- [ ] **Line length comfortable**
  - 50-75 characters per line ideal
  - Not too wide (hard to read)
  - Not too narrow (choppy)

- [ ] **Line height adequate**
  - 1.5 line-height minimum for body text
  - Better readability with breathing room

- [ ] **Color contrast sufficient**
  - Text readable against background
  - Minimum 4.5:1 contrast ratio (WCAG AA)
  - Check light-on-dark and dark-on-light

### Media Content

- [ ] **Images display correctly**
  - All images load
  - Appropriate size (not tiny, not huge)
  - Alt text present (accessibility)

- [ ] **Videos work**
  - Video player displays
  - Play button accessible
  - Full screen option works

- [ ] **Audio works** (if applicable)
  - Audio player displays
  - Controls accessible

- [ ] **Icons visible**
  - Icon fonts load
  - SVG icons display
  - Icons recognizable at mobile size

---

## Functionality Testing

### Page Load

- [ ] **Page loads on cellular**
  - Test on 3G/4G (DevTools can throttle)
  - Acceptable load time (< 3 seconds ideal)
  - Progressive loading (content appears incrementally)

- [ ] **All assets load**
  - CSS loads (page styled)
  - JavaScript loads (interactions work)
  - Fonts load (or fallback fonts display)

### Interactive Elements

- [ ] **Buttons work**
  - All buttons functional
  - Tap activates action
  - Disabled buttons look disabled

- [ ] **Links work**
  - All links navigate correctly
  - External links open (in new tab if desired)
  - Tel: links open phone dialer
  - Mailto: links open email

- [ ] **Dropdowns/selects work**
  - Can open dropdown
  - Can select option
  - Selection registers
  - Native mobile picker appears (not desktop dropdown)

- [ ] **Accordions/toggles work**
  - Expand/collapse works
  - Smooth animation
  - Content doesn't jump

- [ ] **Modals/popups work**
  - Modal opens
  - Modal displays correctly on small screen
  - Can close modal
  - Can scroll modal content if long

- [ ] **Search works**
  - Search box accessible
  - Can type search query
  - Search executes
  - Results display

### WordPress-Specific

- [ ] **WordPress site features**
  - Can view posts/pages
  - Can comment (if enabled)
  - Can share (if enabled)
  - Can login (if membership site)

- [ ] **Custom features work**
  - Glossary search (if applicable)
  - Policy documents load (if applicable)
  - Contact form submits
  - Any custom shortcodes render

---

## Performance Testing

### Speed

- [ ] **Time to First Contentful Paint < 2 seconds**
  - Use Lighthouse in DevTools
  - Performance tab → Reload

- [ ] **Time to Interactive < 3 seconds**
  - When can user actually interact with page?
  - Test on simulated 3G connection

- [ ] **No layout shift**
  - Page doesn't jump around while loading
  - Content doesn't move after load
  - Cumulative Layout Shift (CLS) score low

### Resource Usage

- [ ] **Images optimized**
  - Images compressed
  - Appropriate format (WebP if supported)
  - Responsive images used (srcset)

- [ ] **Minimal requests**
  - Check DevTools Network tab
  - Fewer requests = faster load

- [ ] **Battery/CPU usage reasonable**
  - Page doesn't drain battery fast
  - Phone doesn't get hot
  - Animations don't cause lag

---

## Browser Compatibility Testing

### iOS Safari

- [ ] **Renders correctly**
  - Layout correct
  - Colors correct
  - Fonts load

- [ ] **Interactions work**
  - Tap works
  - Scroll works
  - Forms work

- [ ] **No iOS-specific bugs**
  - Fixed positioning works
  - 100vh works correctly
  - Hover states don't stick

### Android Chrome

- [ ] **Renders correctly**
  - Layout matches design
  - All content displays

- [ ] **Interactions work**
  - Touch events work
  - Scroll smooth
  - Forms functional

### Other Mobile Browsers (If time permits)

- [ ] Firefox Mobile
- [ ] Samsung Internet
- [ ] Opera Mobile

---

## Accessibility Testing

### Screen Reader Friendly

- [ ] **Logical heading structure**
  - H1 → H2 → H3 (don't skip levels)
  - Headings describe content

- [ ] **Alt text on images**
  - All images have alt attribute
  - Alt text descriptive
  - Decorative images: alt=""

- [ ] **Form labels present**
  - All inputs have associated label
  - Labels descriptive
  - Required fields indicated

### Keyboard/Focus

- [ ] **Can navigate with keyboard** (Bluetooth keyboard)
  - Tab through interactive elements
  - Enter activates buttons/links
  - Escape closes modals

- [ ] **Focus visible**
  - Can see which element has focus
  - Focus outline present
  - Focus order logical

---

## Testing Workflow

### Quick Test (5 minutes)

**For every deployment, minimum**:

1. Open in Chrome DevTools mobile view (F12 → Toggle device)
2. Test iPhone SE (320px) and iPhone 12 (390px) sizes
3. Check layout doesn't break
4. Tap mobile menu, verify it works
5. Check homepage, 1-2 key pages
6. Verify no horizontal scrolling

### Standard Test (15 minutes)

**For significant changes**:

1. All steps from Quick Test
2. Test multiple screen sizes (320px, 375px, 414px, 768px)
3. Test in Chrome and Firefox DevTools
4. Test all key pages (home, about, contact, etc.)
5. Test all interactive elements (forms, menus, buttons)
6. Check performance (Lighthouse audit)

### Comprehensive Test (30-45 minutes)

**Before major releases**:

1. All steps from Standard Test
2. Test on actual devices (iOS and Android)
3. Test on multiple browsers per platform
4. Test all pages (or representative sample)
5. Test all functionality thoroughly
6. Run full Lighthouse audit
7. Test on slow connection (3G throttle)
8. Accessibility check
9. Document any issues found

---

## Common Mobile Issues & Quick Fixes

### Issue: Viewport not working
```html
<!-- Add to <head>: -->
<meta name="viewport" content="width=device-width, initial-scale=1">
```

### Issue: Text too small
```css
/* Increase base font size: */
body {
    font-size: 16px;
}
```

### Issue: Touch targets too small
```css
/* Make buttons/links larger: */
button, a {
    min-height: 44px;
    min-width: 44px;
    padding: 12px 16px;
}
```

### Issue: Horizontal scrolling
```css
/* Add to body or container: */
body {
    overflow-x: hidden;
}

/* Or find and fix wide element: */
* {
    box-sizing: border-box;
}
```

### Issue: Mobile menu not working
```bash
# Check JavaScript console (F12) for errors
# Verify mobile-menu-injector.php exists
ls -la wp-content/mu-plugins/mobile-menu-injector.php

# Check z-index is high enough
# Should be 9999 or higher
```

### Issue: Images too large
```css
/* Make images responsive: */
img {
    max-width: 100%;
    height: auto;
}
```

---

## Mobile Testing Tools

### Browser DevTools
- **Chrome**: F12 → Toggle device toolbar (Ctrl+Shift+M)
- **Firefox**: F12 → Responsive Design Mode (Ctrl+Shift+M)
- **Safari**: Develop menu → Responsive Design Mode

### Online Tools
- **Google Mobile-Friendly Test**: https://search.google.com/test/mobile-friendly
- **Responsinator**: http://www.responsinator.com/
- **BrowserStack**: https://www.browserstack.com/ (Actual devices in cloud)

### Lighthouse Audit
```bash
# In Chrome DevTools:
# 1. F12 → Lighthouse tab
# 2. Select "Mobile"
# 3. Click "Generate report"

# Check scores for:
# - Performance
# - Accessibility
# - Best Practices
# - SEO
```

---

## Quick Reference: Mobile Testing Priorities

### Must Test (Every Deployment)
1. ✅ Mobile menu works
2. ✅ No horizontal scrolling
3. ✅ Key pages display correctly
4. ✅ Text readable without zoom

### Should Test (Significant Changes)
5. ✅ Forms work on mobile
6. ✅ Touch targets adequate size
7. ✅ Performance acceptable
8. ✅ Multiple screen sizes

### Nice to Test (Major Releases)
9. ✅ Actual device testing
10. ✅ Multiple browsers
11. ✅ Accessibility features
12. ✅ Slow connection test

---

**Integration**: This checklist is referenced in:
- Deployment Checklist Protocol (`deployment_checklist_protocol.md`)
- Testing & QA Protocol (`testing_qa_protocol.md`)
- WordPress Maintenance Protocol (`wordpress_maintenance_protocol.md`)

**Quick Access**: Print or bookmark this checklist for easy reference during development.
