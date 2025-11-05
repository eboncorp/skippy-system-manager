#!/bin/bash
# Skippy Quick Launcher v1.0.0
# Fast access to all Skippy tools
# Part of: Skippy Enhancement Project - TIER 2
# Created: 2025-11-04

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

SKIPPY_BASE="/home/dave/skippy"

# Show banner
show_banner() {
    echo -e "${CYAN}"
    cat <<'EOF'
╔═══════════════════════════════════════════╗
║                                           ║
║         SKIPPY QUICK LAUNCHER             ║
║     Run Dave Run Campaign Tools           ║
║                                           ║
╚═══════════════════════════════════════════╝
EOF
    echo -e "${NC}"
}

# Show main menu
show_menu() {
    echo -e "${BLUE}═══ Main Menu ═══${NC}"
    echo
    echo -e "${GREEN}WordPress Operations:${NC}"
    echo "  1) Pre-deployment validation"
    echo "  2) Deploy to production"
    echo "  3) Fact check content"
    echo "  4) Bulk operations"
    echo "  5) Content sync"
    echo
    echo -e "${GREEN}Security & Backup:${NC}"
    echo "  6) Security scan"
    echo "  7) Backup verification"
    echo "  8) Secrets management"
    echo "  9) Audit trail"
    echo
    echo -e "${GREEN}Development Tools:${NC}"
    echo "  10) Script debugger"
    echo "  11) Code snippets"
    echo "  12) Generate template"
    echo "  13) Environment setup"
    echo "  14) Script index"
    echo
    echo -e "${GREEN}System & Monitoring:${NC}"
    echo "  15) View logs"
    echo "  16) View reports"
    echo "  17) System health check"
    echo "  18) Recent alerts"
    echo
    echo -e "${YELLOW}Other:${NC}"
    echo "  h) Help"
    echo "  q) Quit"
    echo
}

# Execute tool
execute() {
    local tool="$1"
    shift

    echo -e "${CYAN}▶ Launching: $tool${NC}"
    echo

    if [ -x "$tool" ]; then
        "$tool" "$@"
        local exit_code=$?
        echo
        if [ $exit_code -eq 0 ]; then
            echo -e "${GREEN}✓ Completed successfully${NC}"
        else
            echo -e "${RED}✗ Exited with code: $exit_code${NC}"
        fi
    else
        echo -e "${RED}✗ Tool not found: $tool${NC}"
    fi

    echo
    read -p "Press Enter to continue..."
}

# WordPress pre-deployment validation
wp_validation() {
    execute "${SKIPPY_BASE}/scripts/wordpress/pre_deployment_validator_v1.0.0.sh"
}

# WordPress deployment
wp_deploy() {
    echo -e "${YELLOW}⚠ This will deploy to production!${NC}"
    read -p "Continue? (yes/no): " confirm
    if [ "$confirm" = "yes" ]; then
        execute "${SKIPPY_BASE}/scripts/wordpress/wp_quick_deploy_v1.0.0.sh"
    else
        echo "Cancelled"
    fi
}

# Fact checker
fact_check() {
    execute "${SKIPPY_BASE}/scripts/wordpress/fact_checker_v1.0.0.sh"
}

# Bulk operations
bulk_ops() {
    local bulk_tool="${SKIPPY_BASE}/scripts/wordpress/wp_bulk_operations_v1.0.0.sh"

    echo -e "${BLUE}Bulk Operations Menu:${NC}"
    echo "  1) Fix apostrophes"
    echo "  2) Fix budget figures"
    echo "  3) Update email address"
    echo "  4) Fix links"
    echo "  5) Clean revisions"
    echo "  6) Clean trash"
    echo "  b) Back"
    echo
    read -p "Select operation: " choice

    case "$choice" in
        1) execute "$bulk_tool" fix-apostrophes --report ;;
        2) execute "$bulk_tool" fix-budget-figures --report ;;
        3)
            read -p "Old email: " old_email
            read -p "New email: " new_email
            execute "$bulk_tool" update-email "$old_email" "$new_email" --report
            ;;
        4) execute "$bulk_tool" fix-links --report ;;
        5) execute "$bulk_tool" clean-revisions --report ;;
        6) execute "$bulk_tool" clean-trash --report ;;
        b) return ;;
    esac
}

# Content sync
content_sync() {
    local sync_tool="${SKIPPY_BASE}/scripts/wordpress/wp_content_sync_v1.0.0.sh"

    echo -e "${BLUE}Content Sync Menu:${NC}"
    echo "  1) Compare local vs production"
    echo "  2) Pull from production"
    echo "  3) Push to production"
    echo "  b) Back"
    echo
    read -p "Select operation: " choice

    case "$choice" in
        1) execute "$sync_tool" compare all ;;
        2) execute "$sync_tool" pull all --backup ;;
        3) execute "$sync_tool" push all --backup ;;
        b) return ;;
    esac
}

# Security scan
security_scan() {
    execute "${SKIPPY_BASE}/scripts/security/vulnerability_scanner_v1.0.0.sh"
}

# Backup verification
backup_verify() {
    execute "${SKIPPY_BASE}/scripts/backup/backup_verification_test_v1.0.0.sh"
}

# Secrets management
secrets_mgmt() {
    local secrets_tool="${SKIPPY_BASE}/scripts/security/secrets_manager_v1.0.0.sh"

    echo -e "${BLUE}Secrets Management Menu:${NC}"
    echo "  1) List all secrets"
    echo "  2) Add secret"
    echo "  3) Get secret"
    echo "  4) Delete secret"
    echo "  5) View audit log"
    echo "  6) Scan for exposed secrets"
    echo "  b) Back"
    echo
    read -p "Select operation: " choice

    case "$choice" in
        1) execute "$secrets_tool" list ;;
        2)
            read -p "Secret name: " name
            read -sp "Secret value: " value
            echo
            execute "$secrets_tool" add "$name" "$value"
            ;;
        3)
            read -p "Secret name: " name
            execute "$secrets_tool" get "$name"
            ;;
        4)
            read -p "Secret name: " name
            execute "$secrets_tool" delete "$name"
            ;;
        5) execute "$secrets_tool" audit ;;
        6) execute "$secrets_tool" scan ;;
        b) return ;;
    esac
}

# Audit trail viewer
audit_trail() {
    local audit_log="${SKIPPY_BASE}/logs/security/audit_trail.log"

    if [ -f "$audit_log" ]; then
        echo -e "${BLUE}Recent Audit Entries (last 50):${NC}"
        echo
        tail -50 "$audit_log"
        echo
        read -p "Press Enter to continue..."
    else
        echo -e "${YELLOW}No audit log found${NC}"
        read -p "Press Enter to continue..."
    fi
}

# Script debugger
script_debug() {
    local debug_tool="${SKIPPY_BASE}/scripts/utility/script_debugger_v1.0.0.sh"

    echo -e "${BLUE}Script Debugger Menu:${NC}"
    echo "  1) Check syntax"
    echo "  2) Full analysis"
    echo "  3) Lint code style"
    echo "  4) Find issues"
    echo "  5) Auto-fix issues"
    echo "  b) Back"
    echo
    read -p "Select operation: " choice

    case "$choice" in
        1|2|3|4|5)
            read -p "Script path: " script_path
            case "$choice" in
                1) execute "$debug_tool" syntax "$script_path" ;;
                2) execute "$debug_tool" full-debug "$script_path" --report ;;
                3) execute "$debug_tool" lint "$script_path" ;;
                4) execute "$debug_tool" find-issues "$script_path" ;;
                5) execute "$debug_tool" fix "$script_path" ;;
            esac
            ;;
        b) return ;;
    esac
}

# Code snippets
code_snippets() {
    local snippet_tool="${SKIPPY_BASE}/scripts/utility/snippet_manager_v1.0.0.sh"

    echo -e "${BLUE}Code Snippets Menu:${NC}"
    echo "  1) List all snippets"
    echo "  2) Search snippets"
    echo "  3) Show snippet"
    echo "  4) Add snippet"
    echo "  5) List categories"
    echo "  b) Back"
    echo
    read -p "Select operation: " choice

    case "$choice" in
        1) execute "$snippet_tool" list ;;
        2)
            read -p "Search keyword: " keyword
            execute "$snippet_tool" search "$keyword"
            ;;
        3)
            read -p "Snippet name: " name
            execute "$snippet_tool" show "$name"
            ;;
        4)
            read -p "Snippet name: " name
            read -p "File path: " file_path
            execute "$snippet_tool" add "$name" "$file_path"
            ;;
        5) execute "$snippet_tool" categories ;;
        b) return ;;
    esac
}

# Generate template
generate_template() {
    local template_tool="${SKIPPY_BASE}/scripts/utility/template_generator_v1.0.0.sh"

    echo -e "${BLUE}Template Types:${NC}"
    echo "  1) Bash script"
    echo "  2) WordPress tool"
    echo "  3) Backup script"
    echo "  4) Deployment script"
    echo "  5) Monitoring script"
    echo "  6) Security scanner"
    echo "  7) Python script"
    echo "  b) Back"
    echo
    read -p "Select template type: " choice

    local template_type=""
    case "$choice" in
        1) template_type="bash-script" ;;
        2) template_type="wordpress-tool" ;;
        3) template_type="backup-script" ;;
        4) template_type="deployment-script" ;;
        5) template_type="monitoring-script" ;;
        6) template_type="security-scanner" ;;
        7) template_type="python-script" ;;
        b) return ;;
        *) echo "Invalid choice"; return ;;
    esac

    read -p "Output file path: " output_file
    read -p "Script name (optional): " script_name

    if [ -n "$script_name" ]; then
        execute "$template_tool" "$template_type" "$output_file" --name "$script_name"
    else
        execute "$template_tool" "$template_type" "$output_file"
    fi
}

# Environment setup
env_setup() {
    execute "${SKIPPY_BASE}/scripts/utility/dev_environment_setup_v1.0.0.sh" check
}

# Script index
script_index() {
    local index_file="${SKIPPY_BASE}/SCRIPT_INDEX.md"

    if [ -f "$index_file" ]; then
        echo -e "${BLUE}Search script index:${NC}"
        read -p "Search keyword (or Enter for all): " keyword

        if [ -z "$keyword" ]; then
            less "$index_file"
        else
            grep -i "$keyword" "$index_file" | less
        fi
    else
        echo -e "${YELLOW}Script index not found${NC}"
        echo "Generate with: ${SKIPPY_BASE}/scripts/utility/generate_script_index_v1.0.0.sh"
        read -p "Press Enter to continue..."
    fi
}

# View logs
view_logs() {
    echo -e "${BLUE}Available Logs:${NC}"
    echo "  1) Security audit log"
    echo "  2) Critical alerts"
    echo "  3) Secrets access log"
    echo "  4) All logs directory"
    echo "  b) Back"
    echo
    read -p "Select log: " choice

    case "$choice" in
        1) less "${SKIPPY_BASE}/logs/security/audit_trail.log" 2>/dev/null || echo "Log not found" ;;
        2) less "${SKIPPY_BASE}/logs/alerts/critical_events.log" 2>/dev/null || echo "Log not found" ;;
        3) less "${SKIPPY_BASE}/logs/security/secrets_access.log" 2>/dev/null || echo "Log not found" ;;
        4) ls -lht "${SKIPPY_BASE}/logs/" && read -p "Press Enter..." ;;
        b) return ;;
    esac
}

# View reports
view_reports() {
    echo -e "${BLUE}Available Reports:${NC}"
    echo "  1) Security reports"
    echo "  2) Backup reports"
    echo "  3) Deployment reports"
    echo "  4) Validation reports"
    echo "  5) All reports directory"
    echo "  b) Back"
    echo
    read -p "Select report type: " choice

    case "$choice" in
        1) ls -lht "${SKIPPY_BASE}/conversations/security_reports/" 2>/dev/null | head -20 ;;
        2) ls -lht "${SKIPPY_BASE}/conversations/backup_reports/" 2>/dev/null | head -20 ;;
        3) ls -lht "${SKIPPY_BASE}/conversations/deployment_reports/" 2>/dev/null | head -20 ;;
        4) ls -lht "${SKIPPY_BASE}/conversations/deployment_validation_reports/" 2>/dev/null | head -20 ;;
        5) ls -lht "${SKIPPY_BASE}/conversations/" | head -30 ;;
        b) return ;;
    esac

    echo
    read -p "Press Enter to continue..."
}

# System health check
health_check() {
    echo -e "${BLUE}═══ System Health Check ═══${NC}"
    echo

    execute "${SKIPPY_BASE}/scripts/utility/dev_environment_setup_v1.0.0.sh" check
}

# Recent alerts
recent_alerts() {
    local alert_log="${SKIPPY_BASE}/logs/alerts/critical_events.log"

    if [ -f "$alert_log" ]; then
        echo -e "${BLUE}Recent Alerts (last 20):${NC}"
        echo
        tail -20 "$alert_log"
    else
        echo -e "${GREEN}✓ No alerts found${NC}"
    fi

    echo
    read -p "Press Enter to continue..."
}

# Show help
show_help() {
    echo -e "${BLUE}═══ Skippy Quick Launcher Help ═══${NC}"
    echo
    echo "This launcher provides quick access to all Skippy tools."
    echo
    echo "Navigation:"
    echo "  - Enter the number of the tool you want to run"
    echo "  - Use 'b' to go back in submenus"
    echo "  - Use 'q' to quit"
    echo
    echo "Tips:"
    echo "  - All operations are logged"
    echo "  - Backups are created automatically when needed"
    echo "  - Use validation before deploying"
    echo
    read -p "Press Enter to continue..."
}

# Main loop
main() {
    while true; do
        clear
        show_banner
        show_menu

        read -p "Select option: " choice
        echo

        case "$choice" in
            1) wp_validation ;;
            2) wp_deploy ;;
            3) fact_check ;;
            4) bulk_ops ;;
            5) content_sync ;;
            6) security_scan ;;
            7) backup_verify ;;
            8) secrets_mgmt ;;
            9) audit_trail ;;
            10) script_debug ;;
            11) code_snippets ;;
            12) generate_template ;;
            13) env_setup ;;
            14) script_index ;;
            15) view_logs ;;
            16) view_reports ;;
            17) health_check ;;
            18) recent_alerts ;;
            h|H) show_help ;;
            q|Q)
                echo -e "${GREEN}Goodbye!${NC}"
                exit 0
                ;;
            *)
                echo -e "${RED}Invalid option${NC}"
                sleep 1
                ;;
        esac
    done
}

# Run main
main
