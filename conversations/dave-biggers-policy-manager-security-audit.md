# Security Audit Report: Dave Biggers Policy Manager Plugin

**Date:** November 2, 2025
**Auditor:** Claude Code Security Analysis
**Plugin Version:** 1.0.0
**Plugin Path:** `/home/dave/Local Sites/rundaverun-local/app/public/wp-content/plugins/dave-biggers-policy-manager/`

---

## Executive Summary

The Dave Biggers Policy Manager plugin has been audited for security vulnerabilities. The audit covered SQL injection, XSS, CSRF, access control, file handling, input validation, and authentication issues.

**Overall Security Rating:** B+ (Good, with improvements needed)

**Summary of Findings:**
- **Critical Vulnerabilities:** 3
- **High Severity:** 4
- **Medium Severity:** 5
- **Low Severity:** 3
- **Total Issues Found:** 15

The plugin demonstrates several security best practices including CSRF protection via nonces, parameterized database queries, and capability checks. However, there are critical SQL injection vulnerabilities in the admin panel, missing authentication token validation, and several XSS risks that need immediate attention.

---

## Vulnerability Findings

### CRITICAL SEVERITY

#### 1. SQL Injection via Direct Table Name Concatenation
**File:** `/admin/class-admin.php` (Lines 177, 229, 263-268)
**Severity:** CRITICAL

**Vulnerable Code:**
```php
// Line 177
$subscribers = $wpdb->get_results( "SELECT * FROM $table_name ORDER BY subscribed_date DESC" );

// Line 229
$subscribers = $wpdb->get_results( "SELECT * FROM $table_name ORDER BY subscribed_date DESC", ARRAY_A );

// Lines 263-268
$policies = $wpdb->get_results( "
    SELECT p.ID, p.post_title, pm.meta_value as download_count
    FROM {$wpdb->posts} p
    LEFT JOIN {$wpdb->postmeta} pm ON p.ID = pm.post_id AND pm.meta_key = '_policy_download_count'
    WHERE p.post_type = 'policy_document' AND p.post_status = 'publish'
    ORDER BY CAST(IFNULL(pm.meta_value, 0) AS UNSIGNED) DESC
" );
```

**Issue:** While `$table_name` is constructed from `$wpdb->prefix`, the direct interpolation of table names and lack of prepared statements makes this vulnerable to SQL injection if the prefix is ever compromised. Additionally, the complex query on lines 263-268 does not use `$wpdb->prepare()`.

**Fix Recommendation:**
```php
// Use esc_sql() for table names and prepare() for any dynamic values
$table_name = esc_sql( $wpdb->prefix . 'dbpm_subscribers' );
$subscribers = $wpdb->get_results( $wpdb->prepare(
    "SELECT * FROM {$table_name} ORDER BY subscribed_date DESC"
) );

// For complex queries, still use prepare even without parameters
$policies = $wpdb->get_results( $wpdb->prepare(
    "SELECT p.ID, p.post_title, pm.meta_value as download_count
    FROM {$wpdb->posts} p
    LEFT JOIN {$wpdb->postmeta} pm ON p.ID = pm.post_id AND pm.meta_key = %s
    WHERE p.post_type = %s AND p.post_status = %s
    ORDER BY CAST(IFNULL(pm.meta_value, 0) AS UNSIGNED) DESC",
    '_policy_download_count',
    'policy_document',
    'publish'
) );
```

---

#### 2. Unvalidated Email Token in Unsubscribe Handler
**File:** `/includes/class-email-signup.php` (Lines 155-179)
**Severity:** CRITICAL

**Vulnerable Code:**
```php
public function handle_unsubscribe() {
    if ( ! isset( $_GET['dbpm_unsubscribe'] ) ) {
        return;
    }

    $email = sanitize_email( $_GET['dbpm_unsubscribe'] );

    if ( ! is_email( $email ) ) {
        wp_die( 'Invalid email address.' );
    }

    global $wpdb;
    $table_name = $wpdb->prefix . 'dbpm_subscribers';

    $wpdb->update(
        $table_name,
        array( 'unsubscribed' => 1 ),
        array( 'email' => $email ),
        array( '%d' ),
        array( '%s' )
    );

    wp_redirect( home_url( '?dbpm_unsubscribed=1' ) );
    exit;
}
```

**Issue:** NO CSRF/AUTHENTICATION TOKEN REQUIRED! Anyone can unsubscribe any email address by simply crafting a URL like `?dbpm_unsubscribe=victim@email.com`. This is a critical security flaw allowing unauthorized unsubscription of users.

**Fix Recommendation:**
```php
public function handle_unsubscribe() {
    if ( ! isset( $_GET['dbpm_unsubscribe'] ) || ! isset( $_GET['token'] ) ) {
        return;
    }

    $email = sanitize_email( $_GET['dbpm_unsubscribe'] );
    $token = sanitize_text_field( $_GET['token'] );

    if ( ! is_email( $email ) ) {
        wp_die( 'Invalid email address.' );
    }

    global $wpdb;
    $table_name = $wpdb->prefix . 'dbpm_subscribers';

    // Verify token matches
    $subscriber = $wpdb->get_row( $wpdb->prepare(
        "SELECT * FROM $table_name WHERE email = %s AND verification_token = %s",
        $email,
        $token
    ) );

    if ( ! $subscriber ) {
        wp_die( 'Invalid unsubscribe link.' );
    }

    $wpdb->update(
        $table_name,
        array( 'unsubscribed' => 1 ),
        array( 'email' => $email ),
        array( '%d' ),
        array( '%s' )
    );

    wp_redirect( home_url( '?dbpm_unsubscribed=1' ) );
    exit;
}
```

---

#### 3. Third-Party Library Vulnerabilities (mPDF)
**Files:** `/includes/libraries/vendor/mpdf/mpdf/includes/out.php`, `/includes/libraries/vendor/mpdf/mpdf/qrcode/*.php`, `/includes/libraries/vendor/mpdf/mpdf/compress.php`
**Severity:** CRITICAL

**Vulnerable Code:**
```php
// out.php:5
$tempfilename = $_REQUEST['filename'].'.pdf';

// qrcode/image.php:2
$msg = isset($_GET['msg']) ? $_GET['msg'] : '';

// compress.php:78
$inc = $_POST['inc'];
```

**Issue:** The bundled mPDF library contains multiple files that directly use unsanitized `$_REQUEST`, `$_GET`, and `$_POST` variables. These files appear to be utility/demo scripts that should NOT be included in production and create severe security risks including:
- Arbitrary file access
- XSS vulnerabilities
- Potential code execution

**Fix Recommendation:**
1. Remove unnecessary utility files:
   - `includes/libraries/vendor/mpdf/mpdf/includes/out.php`
   - `includes/libraries/vendor/mpdf/mpdf/qrcode/index.php`
   - `includes/libraries/vendor/mpdf/mpdf/qrcode/image.php`
   - `includes/libraries/vendor/mpdf/mpdf/compress.php`

2. Update mPDF to the latest version via Composer
3. Add `.htaccess` protection to the libraries directory:
```apache
<FilesMatch "\.(php|php\.)$">
    Order Allow,Deny
    Deny from all
</FilesMatch>
```

---

### HIGH SEVERITY

#### 4. XSS in Search Widget via Unescaped GET Parameter
**File:** `/includes/class-search.php` (Line 76)
**Severity:** HIGH

**Vulnerable Code:**
```php
<input type="search"
       class="dbpm-search-field"
       placeholder="<?php echo esc_attr( $atts['placeholder'] ); ?>"
       value="<?php echo get_search_query(); ?>"
       name="s"
       required />
```

**Issue:** `get_search_query()` returns the unescaped search query. While WordPress core does sanitize this in most contexts, it's better to explicitly escape it.

**Fix Recommendation:**
```php
value="<?php echo esc_attr( get_search_query() ); ?>"
```

---

#### 5. Plaintext Password in Email
**File:** `/includes/class-volunteer-access.php` (Lines 90-106)
**Severity:** HIGH

**Vulnerable Code:**
```php
$message .= "Your Login Details:\n";
$message .= "Username: {$username}\n";
$message .= "Password: {$password}\n";
$message .= "Login URL: " . wp_login_url() . "\n\n";
```

**Issue:** Sending plaintext passwords via email is a security risk. Emails can be intercepted, stored in logs, and compromise user accounts. This is especially concerning for a political campaign where opposition research might target communications.

**Fix Recommendation:**
Send a password reset link instead:
```php
$reset_key = get_password_reset_key( $user );
$reset_url = network_site_url( "wp-login.php?action=rp&key=$reset_key&login=" . rawurlencode( $username ), 'login' );

$message .= "Your account has been created!\n\n";
$message .= "Username: {$username}\n";
$message .= "Set your password: {$reset_url}\n\n";
```

---

#### 6. Potential XSS in Admin Analytics Page
**File:** `/admin/class-admin.php` (Lines 354, 410)
**Severity:** HIGH

**Vulnerable Code:**
```php
// Line 354
<strong><?php echo esc_html( $policy->post_title ); ?></strong>

// Line 410
<li>🔥 "<?php echo esc_html( $top_policies[0]->post_title ); ?>" is your most popular policy.</li>
```

**Issue:** While `esc_html()` is used, the context is within an admin page. If post titles are ever set programmatically with HTML entities, this could still present issues. The code is mostly safe, but should verify post data origin.

**Status:** Currently protected with `esc_html()`, but verify post titles cannot contain malicious content.

---

#### 7. CSV Export Without Rate Limiting
**File:** `/admin/class-admin.php` (Lines 225-254)
**Severity:** HIGH

**Vulnerable Code:**
```php
private function export_subscribers() {
    global $wpdb;
    $table_name = $wpdb->prefix . 'dbpm_subscribers';

    $subscribers = $wpdb->get_results( "SELECT * FROM $table_name ORDER BY subscribed_date DESC", ARRAY_A );

    header( 'Content-Type: text/csv' );
    header( 'Content-Disposition: attachment; filename="dbpm-subscribers-' . date( 'Y-m-d' ) . '.csv"' );
    // ... exports all subscriber data
}
```

**Issue:** While protected by `manage_options` capability and nonce verification (line 173), there's no rate limiting. An attacker with temporary admin access could repeatedly export sensitive subscriber data.

**Fix Recommendation:**
Add rate limiting using WordPress transients:
```php
$rate_limit_key = 'dbpm_export_rate_limit_' . get_current_user_id();
if ( get_transient( $rate_limit_key ) ) {
    wp_die( 'Please wait before exporting again.' );
}
set_transient( $rate_limit_key, 1, 5 * MINUTE_IN_SECONDS );
```

---

### MEDIUM SEVERITY

#### 8. Direct File Access Not Prevented in Template Files
**Files:** `/templates/single-policy.php`, `/templates/archive-policy.php`
**Severity:** MEDIUM

**Vulnerable Code:**
```php
<?php
/**
 * Single Policy Document Template
 */
get_header();
?>
```

**Issue:** Template files don't check if they're being accessed directly vs. through WordPress. While `get_header()` will fail if WordPress isn't loaded, it's best practice to explicitly prevent direct access.

**Fix Recommendation:**
Add to top of each template file:
```php
<?php
if ( ! defined( 'ABSPATH' ) ) {
    exit; // Exit if accessed directly
}
```

---

#### 9. Weak Random Username Generation
**File:** `/includes/class-volunteer-access.php` (Line 35)
**Severity:** MEDIUM

**Vulnerable Code:**
```php
$username = sanitize_user( str_replace( ' ', '', strtolower( $name ) ) . rand( 100, 999 ) );
```

**Issue:** Using `rand()` for username generation creates predictable usernames. Attackers could enumerate volunteer accounts.

**Fix Recommendation:**
```php
$username = sanitize_user( str_replace( ' ', '', strtolower( $name ) ) . wp_rand( 1000, 9999 ) );
```

---

#### 10. Missing Content-Type Header Validation in PDF Generation
**File:** `/includes/class-pdf-generator.php` (Lines 199-208)
**Severity:** MEDIUM

**Vulnerable Code:**
```php
private function generate_simple_pdf( $post ) {
    header( 'Content-Type: application/pdf' );
    header( 'Content-Disposition: attachment; filename="' . sanitize_file_name( $post->post_title ) . '.txt"' );

    echo "DAVE BIGGERS FOR MAYOR\n";
    echo "rundaverun.org\n\n";
    echo strtoupper( $post->post_title ) . "\n";
    echo str_repeat( "=", 80 ) . "\n\n";
    echo wp_strip_all_tags( $post->post_content );

    exit;
}
```

**Issue:** The function outputs plain text but declares the Content-Type as `application/pdf`. This creates a mismatch that could be exploited. Also, the filename uses `.txt` extension instead of `.pdf`.

**Fix Recommendation:**
```php
header( 'Content-Type: text/plain; charset=utf-8' );
header( 'Content-Disposition: attachment; filename="' . sanitize_file_name( $post->post_title ) . '.txt"' );
```

---

#### 11. User Enumeration via Volunteer Registration
**File:** `/includes/class-volunteer-access.php` (Lines 28-32)
**Severity:** MEDIUM

**Vulnerable Code:**
```php
// Check if user already exists
$existing_user = get_user_by( 'email', $email );
if ( $existing_user ) {
    wp_send_json_error( array( 'message' => 'An account with this email already exists.' ) );
}
```

**Issue:** This allows attackers to enumerate which email addresses have accounts by attempting volunteer registration. For a political campaign, this reveals who is involved.

**Fix Recommendation:**
Use a generic message:
```php
if ( $existing_user ) {
    wp_send_json_error( array( 'message' => 'Registration received. If this email is not already registered, you will receive a confirmation shortly.' ) );
    // Still send email to user notifying them of duplicate registration attempt
    exit;
}
```

---

#### 12. Missing Nonce in Admin Import Page Inline JavaScript
**File:** `/admin/class-admin.php` (Line 106)
**Severity:** MEDIUM

**Vulnerable Code:**
```php
<script>
jQuery(document).ready(function($) {
    $('#dbpm-import-btn').on('click', function(e) {
        // ...
        $.ajax({
            url: ajaxurl,
            type: 'POST',
            data: {
                action: 'dbpm_import_documents',
                nonce: '<?php echo wp_create_nonce( 'dbpm_admin_nonce' ); ?>'
            },
```

**Issue:** While a nonce is being created, it's generated inline in JavaScript which is visible in the page source. The nonce is also created on page load, which could be stale if the page is left open for extended periods.

**Fix Recommendation:**
Use `wp_localize_script()` to pass the nonce (already done correctly on line 506-509), and reference it:
```php
nonce: dbpmAdmin.nonce
```

---

### LOW SEVERITY

#### 13. Missing HTTP Header Security
**Files:** All public-facing files
**Severity:** LOW

**Issue:** The plugin doesn't set security headers like X-Content-Type-Options, X-Frame-Options, etc.

**Fix Recommendation:**
Add to main plugin file or admin init:
```php
add_action( 'send_headers', function() {
    if ( is_admin() ) {
        header( 'X-Content-Type-Options: nosniff' );
        header( 'X-Frame-Options: SAMEORIGIN' );
        header( 'X-XSS-Protection: 1; mode=block' );
    }
} );
```

---

#### 14. Verbose Error Messages in AJAX Handlers
**File:** `/includes/class-volunteer-access.php` (Line 42)
**Severity:** LOW

**Vulnerable Code:**
```php
if ( is_wp_error( $user_id ) ) {
    wp_send_json_error( array( 'message' => 'Error creating account: ' . $user_id->get_error_message() ) );
}
```

**Issue:** WordPress error messages can reveal system information. Better to log detailed errors and show generic messages to users.

**Fix Recommendation:**
```php
if ( is_wp_error( $user_id ) ) {
    error_log( 'Volunteer registration error: ' . $user_id->get_error_message() );
    wp_send_json_error( array( 'message' => 'Error creating account. Please try again or contact support.' ) );
}
```

---

#### 15. No Maximum Attachment Size Validation
**File:** Not implemented
**Severity:** LOW

**Issue:** While the plugin doesn't currently handle file uploads, if this feature is added in the future, it should validate file sizes and types.

**Fix Recommendation:**
Document that any future file upload features must include:
- File type validation
- Size limits
- Virus scanning integration
- Secure file storage outside web root

---

## Security Strengths

The plugin demonstrates several security best practices:

1. **CSRF Protection:** All AJAX handlers properly use `check_ajax_referer()` and verify nonces
   - Example: `class-email-signup.php:11`, `class-volunteer-access.php:11`, `class-importer.php:367`

2. **Input Sanitization:** User inputs are consistently sanitized using WordPress functions
   - `sanitize_text_field()`, `sanitize_email()`, `sanitize_textarea_field()`, `absint()`

3. **Output Escaping:** Most output is properly escaped using `esc_html()`, `esc_attr()`, `esc_url()`

4. **Capability Checks:** Admin functions verify `manage_options` capability
   - Example: `class-volunteer-access.php:115`, `class-importer.php:369`

5. **Prepared Statements:** Most database queries use `$wpdb->prepare()`
   - Example: `class-email-signup.php:31-34`, `class-email-signup.php:125-128`

6. **Access Control:** Content restriction is implemented based on user roles
   - Example: `class-volunteer-access.php:320-340`

7. **Direct File Access Prevention:** Main plugin files check for `WPINC` constant
   - Example: `dave-biggers-policy-manager.php:16-18`

8. **SQL Injection Prevention:** Most queries properly parameterized
   - Uses `%s`, `%d` format specifiers correctly

---

## Recommendations for Improvement

### Immediate Actions (Critical/High Priority)

1. **Remove mPDF Utility Files**
   - Delete: `includes/libraries/vendor/mpdf/mpdf/includes/out.php`
   - Delete: `includes/libraries/vendor/mpdf/mpdf/qrcode/index.php`
   - Delete: `includes/libraries/vendor/mpdf/mpdf/qrcode/image.php`
   - Delete: `includes/libraries/vendor/mpdf/mpdf/compress.php`

2. **Fix Unsubscribe CSRF Vulnerability**
   - Add token verification to `handle_unsubscribe()` method
   - Include unsubscribe token in emails

3. **Fix SQL Injection in Admin Panel**
   - Use `$wpdb->prepare()` for all queries, even without dynamic parameters
   - Add `esc_sql()` for table names

4. **Remove Plaintext Passwords from Emails**
   - Implement password reset link system instead

5. **Add Library Directory Protection**
   - Create `.htaccess` file in `/includes/libraries/` to prevent direct PHP execution

### Short-term Improvements (Medium Priority)

6. **Add Direct Access Prevention to Templates**
   - Add `ABSPATH` check to all template files

7. **Implement Rate Limiting**
   - Add transient-based rate limiting to CSV export and AJAX handlers

8. **Fix User Enumeration**
   - Use generic error messages in registration/login forms

9. **Improve Random Number Generation**
   - Replace `rand()` with `wp_rand()` or `random_int()`

10. **Add Input Validation**
    - Validate zip codes format (5 or 9 digits)
    - Validate phone number formats
    - Add maximum length checks beyond database constraints

### Long-term Enhancements (Low Priority)

11. **Security Headers**
    - Implement Content-Security-Policy
    - Add Referrer-Policy headers
    - Set Permissions-Policy

12. **Logging and Monitoring**
    - Log failed authentication attempts
    - Monitor suspicious activity (rapid form submissions, etc.)
    - Add admin notification for security events

13. **Code Hardening**
    - Implement request throttling
    - Add honeypot fields to forms
    - Consider two-factor authentication for volunteer accounts

14. **Regular Security Audits**
    - Schedule quarterly code reviews
    - Update third-party libraries regularly
    - Monitor WordPress security bulletins

15. **Documentation**
    - Create security policy document
    - Document data handling procedures
    - Add security changelog to track fixes

---

## Testing Recommendations

### Penetration Testing Scenarios

1. **SQL Injection Testing**
   - Test all database queries with malicious input
   - Verify parameterization is working correctly

2. **XSS Testing**
   - Test all form inputs with `<script>alert('XSS')</script>`
   - Verify output escaping in templates

3. **CSRF Testing**
   - Attempt AJAX requests without valid nonces
   - Try form submissions from external sites

4. **Authentication Testing**
   - Test privilege escalation from volunteer to admin
   - Verify logged-out users cannot access restricted content

5. **File Security Testing**
   - Attempt direct access to PHP files in libraries
   - Test PDF generation with malicious input

---

## Compliance Considerations

### Political Campaign Data Regulations

1. **FEC Compliance**
   - Ensure donor/volunteer data is properly secured
   - Implement data retention policies
   - Add audit logging for data access

2. **Privacy Regulations**
   - Add privacy policy notice to signup forms
   - Implement data export/deletion on request
   - Consider GDPR/CCPA compliance even if not strictly required

3. **Email Marketing Laws**
   - CAN-SPAM compliance: Working (unsubscribe link present)
   - Double opt-in: Implemented via email verification
   - Sender identification: Present in email headers

---

## Conclusion

The Dave Biggers Policy Manager plugin demonstrates a solid foundation of security practices but requires immediate attention to address critical vulnerabilities, particularly:

1. **SQL injection risks** in admin panel queries
2. **CSRF vulnerability** in unsubscribe functionality
3. **Exposed mPDF utility files** that could be exploited
4. **Plaintext password transmission** via email

Once these critical issues are addressed, the plugin will have a strong security posture appropriate for a political campaign website handling sensitive volunteer and subscriber data.

**Recommended Timeline:**
- **Week 1:** Fix Critical vulnerabilities (#1-3)
- **Week 2:** Fix High severity issues (#4-7)
- **Week 3:** Address Medium severity issues (#8-12)
- **Week 4:** Implement Low severity improvements (#13-15)

**Next Steps:**
1. Prioritize fixes based on severity ratings
2. Test all changes in development environment
3. Deploy fixes to production incrementally
4. Monitor logs for suspicious activity
5. Schedule follow-up security review after fixes are implemented

---

**Report Generated:** November 2, 2025
**Classification:** Internal - Campaign Use Only
**Contact:** For questions about this audit, contact the development team.
