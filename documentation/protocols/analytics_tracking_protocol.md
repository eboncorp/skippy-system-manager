# Analytics & Tracking Protocol

**Version:** 1.0.0
**Last Updated:** 2025-11-08
**Owner:** Claude Code / Dave

---

## Context

Analytics tracking (Google Analytics 4, custom events) must follow consistent standards for naming, implementation, and privacy compliance.

## Purpose

- Standardize event naming
- Ensure privacy compliance
- Enable meaningful analytics
- Maintain tracking quality

---

## GA4 Event Naming Standards

### Event Categories
- `view_*` - Page/content views
- `click_*` - User interactions
- `form_*` - Form interactions
- `download_*` - File downloads

### Examples
```javascript
// Good
gtag('event', 'view_voter_registration', {
  'event_category': 'Voter Engagement',
  'event_label': 'Homepage Alert',
  'value': days_until_deadline
});

// Bad
gtag('event', 'thing_happened'); // Too vague
```

---

## Implementation Checklist

When adding analytics:
- [ ] Event name is descriptive
- [ ] Category is appropriate
- [ ] Label provides context
- [ ] Value is meaningful (if applicable)
- [ ] Privacy compliant (no PII)
- [ ] Documented in code comments

---

## Privacy Compliance

### NEVER Track:
- ❌ Personally identifiable information (PII)
- ❌ Email addresses
- ❌ Phone numbers
- ❌ Exact addresses

### CAN Track:
- ✅ Page views
- ✅ Button clicks
- ✅ Form submissions (not content)
- ✅ ZIP codes (aggregate data)
- ✅ Time on page

---

**Generated:** 2025-11-08
**Status:** Active
**Next Review:** 2025-12-08
