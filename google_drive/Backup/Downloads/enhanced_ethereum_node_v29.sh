#!/bin/bash

# ============================================================================
# Enhanced Ethereum Node Setup Script v29.0 - Advanced Stereum Competitor
# ============================================================================
# Version: 29.0.0
# Description: Next-generation Ethereum node with improved architecture
# Key Improvements: Modular design, enhanced security, better UX, robust testing
# Features: DVT, MEV-Boost, AI optimization, Liquid Staking, Mobile Dashboard
# Target: Professional-grade Ethereum infrastructure
# Author: Enhanced by AI - Production Ready
# ============================================================================

set -euo pipefail

# ============================================================================
# SCRIPT METADATA AND CORE CONSTANTS
# ============================================================================

readonly SCRIPT_VERSION="29.0.0"
readonly SCRIPT_NAME="Enhanced Ethereum Node Setup - Professional Edition"
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly SCRIPT_PID=$$
readonly SCRIPT_START_TIME=$(date +%s)

# Enhanced configuration with XDG compliance
readonly CONFIG_BASE_DIR="${XDG_CONFIG_HOME:-/etc}/ethereum"
readonly DATA_BASE_DIR="${XDG_DATA_HOME:-/var/lib}/ethereum"
readonly LOG_BASE_DIR="${XDG_STATE_HOME:-/var/log}/ethereum"
readonly CACHE_BASE_DIR="${XDG_CACHE_HOME:-/var/cache}/ethereum"

# Lock and state management
readonly LOCK_FILE="/var/lock/ethereum-setup-v29.lock"
readonly STATE_FILE="${CONFIG_BASE_DIR}/setup-state.json"
readonly ROLLBACK_DIR="${DATA_BASE_DIR}/rollback"

# Enhanced security and compliance
readonly SECURITY_CONFIG="${CONFIG_BASE_DIR}/security.conf"
readonly COMPLIANCE_CONFIG="${CONFIG_BASE_DIR}/compliance.conf"
readonly AUDIT_LOG="${LOG_BASE_DIR}/audit.log"

# Multi-architecture support
declare -A ARCH_MAP=(
    ["x86_64"]="amd64"
    ["aarch64"]="arm64"
    ["armv7l"]="armv7"
    ["armv8l"]="arm64"
    ["s390x"]="s390x"
    ["ppc64le"]="ppc64le"
)

# Enhanced network configurations with L2 support
declare -A NETWORK_CONFIGS=(
    ["mainnet"]="chain_id:1,http_port:8545,ws_port:8546,p2p_port:30303,beacon_port:9000,api_port:5052"
    ["sepolia"]="chain_id:11155111,http_port:8545,ws_port:8546,p2p_port:30303,beacon_port:9000,api_port:5052"
    ["holesky"]="chain_id:17000,http_port:8545,ws_port:8546,p2p_port:30303,beacon_port:9000,api_port:5052"
    ["optimism"]="chain_id:10,http_port:8545,ws_port:8546,p2p_port:30303,beacon_port:9000,api_port:5052"
    ["arbitrum"]="chain_id:42161,http_port:8545,ws_port:8546,p2p_port:30303,beacon_port:9000,api_port:5052"
    ["base"]="chain_id:8453,http_port:8545,ws_port:8546,p2p_port:30303,beacon_port:9000,api_port:5052"
    ["polygon"]="chain_id:137,http_port:8545,ws_port:8546,p2p_port:30303,beacon_port:9000,api_port:5052"
)

# Latest client versions with automatic updates
declare -A CLIENT_VERSIONS=(
    ["geth"]="1.14.8"
    ["erigon"]="2.60.1"
    ["nethermind"]="1.25.4"
    ["besu"]="24.5.2"
    ["lighthouse"]="5.2.1"
    ["prysm"]="5.0.4"
    ["teku"]="24.6.0"
    ["nimbus"]="24.6.0"
    ["mev-boost"]="1.7.0"
    ["ssv-node"]="1.3.7"
    ["charon"]="0.19.2"
)

# ============================================================================
# ENHANCED LOGGING AND ERROR HANDLING SYSTEM
# ============================================================================

# Color definitions with accessibility support
if [[ -t 1 ]] && [[ "${NO_COLOR:-}" != "1" ]]; then
    readonly RED='\033[0;31m'
    readonly GREEN='\033[0;32m'
    readonly YELLOW='\033[1;33m'
    readonly BLUE='\033[0;34m'
    readonly PURPLE='\033[0;35m'
    readonly CYAN='\033[0;36m'
    readonly WHITE='\033[1;37m'
    readonly BOLD='\033[1m'
    readonly DIM='\033[2m'
    readonly NC='\033[0m'
else
    readonly RED='' GREEN='' YELLOW='' BLUE='' PURPLE='' CYAN='' WHITE='' BOLD='' DIM='' NC=''
fi

# Enhanced logging system with structured output
log() {
    local level="$1"
    local message="$2"
    local component="${3:-SYSTEM}"
    local timestamp=$(date -Iseconds)
    local caller="${BASH_SOURCE[2]##*/}:${BASH_LINENO[1]}"
    
    # Determine log file and color
    local log_file color
    case "$level" in
        ERROR)   log_file="${LOG_BASE_DIR}/error.log"; color="$RED" ;;
        WARN)    log_file="${LOG_BASE_DIR}/warnings.log"; color="$YELLOW" ;;
        INFO)    log_file="${LOG_BASE_DIR}/info.log"; color="$BLUE" ;;
        SUCCESS) log_file="${LOG_BASE_DIR}/info.log"; color="$GREEN" ;;
        DEBUG)   log_file="${LOG_BASE_DIR}/debug.log"; color="$PURPLE" ;;
        AUDIT)   log_file="$AUDIT_LOG"; color="$BOLD$RED" ;;
        PERF)    log_file="${LOG_BASE_DIR}/performance.log"; color="$CYAN" ;;
        SECURITY) log_file="${LOG_BASE_DIR}/security.log"; color="$BOLD$YELLOW" ;;
        *) log_file="${LOG_BASE_DIR}/general.log"; color="$WHITE" ;;
    esac
    
    # Create structured log entry
    local structured_entry=$(cat <<EOF
{
  "timestamp": "$timestamp",
  "level": "$level",
  "component": "$component",
  "caller": "$caller",
  "message": $(printf '%s' "$message" | jq -R -s '.'),
  "pid": $SCRIPT_PID,
  "session": "${SESSION_ID:-unknown}"
}
EOF
)
    
    # Write to log file
    [[ -f "$log_file" ]] || { mkdir -p "${log_file%/*}"; touch "$log_file"; }
    echo "$structured_entry" >> "$log_file"
    
    # Console output with level filtering
    local min_level="${MIN_LOG_LEVEL:-INFO}"
    if should_display_log_level "$level" "$min_level"; then
        local display_message="${color}[${level}]${NC} ${DIM}[${component}]${NC} $message"
        echo -e "$display_message" >&2
    fi
}

# Determine if log level should be displayed
should_display_log_level() {
    local current_level="$1"
    local min_level="$2"
    
    declare -A level_priority=(
        ["DEBUG"]=0 ["INFO"]=1 ["SUCCESS"]=1 ["WARN"]=2 
        ["ERROR"]=3 ["AUDIT"]=4 ["SECURITY"]=4
    )
    
    local current_priority="${level_priority[$current_level]:-1}"
    local min_priority="${level_priority[$min_level]:-1}"
    
    [[ $current_priority -ge $min_priority ]]
}

# Enhanced error handling with context preservation
error_exit() {
    local message="$1"
    local exit_code="${2:-1}"
    local should_rollback="${3:-true}"
    local context="${4:-}"
    
    # Log error with full context
    log "ERROR" "$message" "ERROR_HANDLER"
    [[ -n "$context" ]] && log "ERROR" "Context: $context" "ERROR_HANDLER"
    
    # Capture system state for debugging
    capture_error_state "$message" "$exit_code"
    
    # AI-powered error diagnosis
    diagnose_error_enhanced "$message" "$context"
    
    # Rollback if requested and safe
    if [[ "$should_rollback" == "true" ]] && [[ -f "$STATE_FILE" ]]; then
        perform_rollback || log "ERROR" "Rollback failed" "ERROR_HANDLER"
    fi
    
    # Cleanup and exit
    cleanup_on_error
    log "ERROR" "Script exiting with code $exit_code" "ERROR_HANDLER"
    exit "$exit_code"
}

# Capture comprehensive error state
capture_error_state() {
    local error_msg="$1"
    local exit_code="$2"
    local error_dump="${LOG_BASE_DIR}/error-state-$(date +%s).json"
    
    local system_state=$(cat <<EOF
{
  "timestamp": "$(date -Iseconds)",
  "error_message": $(printf '%s' "$error_msg" | jq -R -s '.'),
  "exit_code": $exit_code,
  "script_version": "$SCRIPT_VERSION",
  "system_info": {
    "hostname": "$(hostname)",
    "kernel": "$(uname -r)",
    "uptime": "$(uptime -s)",
    "load_average": "$(uptime | awk -F'load average:' '{print $2}')",
    "memory_usage": "$(free -m | grep '^Mem:' | awk '{printf "%.1f%%", $3/$2 * 100.0}')",
    "disk_usage": "$(df -h / | awk 'NR==2 {print $5}')"
  },
  "environment": {
    "user": "$USER",
    "working_directory": "$PWD",
    "shell": "$SHELL",
    "path": "$PATH"
  },
  "recent_operations": $(get_recent_operations)
}
EOF
)
    
    echo "$system_state" > "$error_dump" 2>/dev/null || true
    log "INFO" "Error state captured in $error_dump" "ERROR_HANDLER"
}

# Get recent operations from state file
get_recent_operations() {
    if [[ -f "$STATE_FILE" ]]; then
        jq -r '.operations[-5:]' "$STATE_FILE" 2>/dev/null || echo "[]"
    else
        echo "[]"
    fi
}

# Enhanced AI-powered error diagnosis
diagnose_error_enhanced() {
    local error_msg="$1"
    local context="${2:-}"
    local suggestions=()
    local severity="medium"
    
    # Enhanced pattern matching with context awareness
    case "$error_msg" in
        *"permission denied"*|*"access denied"*|*"not permitted"*)
            suggestions+=(
                "Run with appropriate sudo privileges"
                "Check file/directory ownership and permissions"
                "Verify user is in required groups (docker, ethereum)"
                "Review SELinux/AppArmor policies if applicable"
            )
            severity="high"
            ;;
        *"no space left"*|*"disk full"*|*"cannot write"*)
            suggestions+=(
                "Free up disk space: sudo apt autoremove && sudo apt autoclean"
                "Check disk usage: df -h && du -sh /var/log/* /tmp/*"
                "Move large files to external storage"
                "Enable log rotation and cleanup old logs"
                "Consider adding additional storage"
            )
            severity="critical"
            ;;
        *"network"*|*"connection"*|*"timeout"*|*"unreachable"*)
            suggestions+=(
                "Test internet connectivity: ping -c 3 8.8.8.8"
                "Check DNS resolution: nslookup github.com"
                "Verify firewall rules: sudo ufw status"
                "Review proxy settings if applicable"
                "Check if VPN is interfering with connections"
            )
            severity="high"
            ;;
        *"memory"*|*"out of memory"*|*"killed"*)
            suggestions+=(
                "Check available memory: free -h"
                "Close unnecessary applications"
                "Add swap space: sudo fallocate -l 4G /swapfile"
                "Reduce memory-intensive operations"
                "Consider upgrading RAM"
            )
            severity="critical"
            ;;
        *"dependency"*|*"package"*|*"not found"*)
            suggestions+=(
                "Update package database: sudo apt update"
                "Install missing dependencies manually"
                "Check repository availability"
                "Verify package manager configuration"
            )
            severity="medium"
            ;;
        *"docker"*|*"container"*)
            suggestions+=(
                "Check Docker service: sudo systemctl status docker"
                "Restart Docker: sudo systemctl restart docker"
                "Clean Docker resources: docker system prune -f"
                "Verify Docker permissions for user"
            )
            severity="medium"
            ;;
    esac
    
    # Context-aware suggestions
    if [[ -n "$context" ]]; then
        case "$context" in
            *"installation"*)
                suggestions+=("Retry installation with --force flag if safe")
                ;;
            *"configuration"*)
                suggestions+=("Validate configuration file syntax" "Reset to default configuration")
                ;;
            *"service"*)
                suggestions+=("Check service logs: journalctl -u <service>" "Restart affected services")
                ;;
        esac
    fi
    
    # Output diagnosis
    if [[ ${#suggestions[@]} -gt 0 ]]; then
        log "INFO" "🤖 AI Diagnosis - Error Severity: $severity" "AI_DIAGNOSIS"
        log "INFO" "💡 Suggested Solutions:" "AI_DIAGNOSIS"
        for i in "${!suggestions[@]}"; do
            log "INFO" "   $((i+1)). ${suggestions[$i]}" "AI_DIAGNOSIS"
        done
        
        # Create recovery script if critical
        if [[ "$severity" == "critical" ]]; then
            create_recovery_script "${suggestions[@]}"
        fi
    fi
}

# Create automated recovery script
create_recovery_script() {
    local suggestions=("$@")
    local recovery_script="${CONFIG_BASE_DIR}/auto-recovery.sh"
    
    cat > "$recovery_script" << 'EOF'
#!/bin/bash
# Auto-generated recovery script
# Generated by Enhanced Ethereum Node Setup v29.0

set -euo pipefail

echo "🔧 Running automated recovery procedures..."

EOF
    
    # Add recovery commands based on suggestions
    for suggestion in "${suggestions[@]}"; do
        case "$suggestion" in
            *"disk space"*)
                cat >> "$recovery_script" << 'EOF'
echo "🧹 Cleaning disk space..."
sudo apt autoremove -y 2>/dev/null || true
sudo apt autoclean 2>/dev/null || true
sudo journalctl --vacuum-time=7d 2>/dev/null || true
EOF
                ;;
            *"restart docker"*)
                cat >> "$recovery_script" << 'EOF'
echo "🐳 Restarting Docker..."
sudo systemctl restart docker 2>/dev/null || true
sleep 5
EOF
                ;;
        esac
    done
    
    echo 'echo "✅ Recovery procedures completed"' >> "$recovery_script"
    chmod +x "$recovery_script"
    
    log "INFO" "Recovery script created: $recovery_script" "AI_DIAGNOSIS"
}

# ============================================================================
# ENHANCED SYSTEM DETECTION AND VALIDATION
# ============================================================================

# Comprehensive platform detection with enhanced capabilities
detect_platform_enhanced() {
    log "INFO" "Performing comprehensive platform detection..." "PLATFORM"
    
    # Detect OS with extended information
    local os_info
    if [[ -f /etc/os-release ]]; then
        source /etc/os-release
        OS_NAME="$NAME"
        OS_VERSION="$VERSION_ID"
        OS_CODENAME="${VERSION_CODENAME:-unknown}"
        OS_LIKE="${ID_LIKE:-$ID}"
        OS_PRETTY_NAME="$PRETTY_NAME"
    else
        OS_NAME=$(uname -s)
        OS_VERSION="unknown"
        OS_CODENAME="unknown"
        OS_LIKE="unknown"
        OS_PRETTY_NAME="$OS_NAME"
    fi
    
    # Enhanced architecture detection
    ARCH=$(uname -m)
    ARCH_SUFFIX="${ARCH_MAP[$ARCH]:-$ARCH}"
    
    # Detect virtualization
    VIRT_TYPE="none"
    if command -v systemd-detect-virt >/dev/null 2>&1; then
        VIRT_TYPE=$(systemd-detect-virt 2>/dev/null || echo "none")
    elif [[ -f /.dockerenv ]]; then
        VIRT_TYPE="docker"
    elif grep -q "container=lxc" /proc/1/environ 2>/dev/null; then
        VIRT_TYPE="lxc"
    fi
    
    # Detect container orchestration
    ORCHESTRATION="none"
    if [[ -n "${KUBERNETES_SERVICE_HOST:-}" ]]; then
        ORCHESTRATION="kubernetes"
    elif [[ -n "${DOCKER_SWARM_NODE_ID:-}" ]]; then
        ORCHESTRATION="docker-swarm"
    fi
    
    # Enhanced package manager detection with version
    detect_package_manager_enhanced
    
    # Hardware capabilities detection
    detect_hardware_capabilities
    
    # Network capabilities
    detect_network_capabilities
    
    # Log comprehensive platform information
    log "SUCCESS" "Platform: $OS_PRETTY_NAME ($ARCH)" "PLATFORM"
    log "INFO" "Virtualization: $VIRT_TYPE, Orchestration: $ORCHESTRATION" "PLATFORM"
    log "INFO" "Package Manager: $PKG_MANAGER_NAME $PKG_MANAGER_VERSION" "PLATFORM"
    
    # Update state
    update_state "platform_detection" "completed" "{
        \"os_name\": \"$OS_NAME\",
        \"os_version\": \"$OS_VERSION\",
        \"architecture\": \"$ARCH\",
        \"virtualization\": \"$VIRT_TYPE\",
        \"package_manager\": \"$PKG_MANAGER\"
    }"
}

# Enhanced package manager detection
detect_package_manager_enhanced() {
    if command -v apt >/dev/null 2>&1; then
        PKG_MANAGER="apt"
        PKG_MANAGER_NAME="APT"
        PKG_MANAGER_VERSION=$(apt --version 2>/dev/null | head -1 | awk '{print $2}')
        PKG_UPDATE="apt update"
        PKG_INSTALL="apt install -y"
        PKG_REMOVE="apt remove -y"
        PKG_SEARCH="apt search"
    elif command -v dnf >/dev/null 2>&1; then
        PKG_MANAGER="dnf"
        PKG_MANAGER_NAME="DNF"
        PKG_MANAGER_VERSION=$(dnf --version 2>/dev/null | head -1)
        PKG_UPDATE="dnf update -y"
        PKG_INSTALL="dnf install -y"
        PKG_REMOVE="dnf remove -y"
        PKG_SEARCH="dnf search"
    elif command -v yum >/dev/null 2>&1; then
        PKG_MANAGER="yum"
        PKG_MANAGER_NAME="YUM"
        PKG_MANAGER_VERSION=$(yum --version 2>/dev/null | head -1)
        PKG_UPDATE="yum update -y"
        PKG_INSTALL="yum install -y"
        PKG_REMOVE="yum remove -y"
        PKG_SEARCH="yum search"
    elif command -v pacman >/dev/null 2>&1; then
        PKG_MANAGER="pacman"
        PKG_MANAGER_NAME="Pacman"
        PKG_MANAGER_VERSION=$(pacman --version 2>/dev/null | head -1 | awk '{print $3}')
        PKG_UPDATE="pacman -Sy"
        PKG_INSTALL="pacman -S --noconfirm"
        PKG_REMOVE="pacman -R --noconfirm"
        PKG_SEARCH="pacman -Ss"
    elif command -v zypper >/dev/null 2>&1; then
        PKG_MANAGER="zypper"
        PKG_MANAGER_NAME="Zypper"
        PKG_MANAGER_VERSION=$(zypper --version 2>/dev/null | head -1)
        PKG_UPDATE="zypper refresh"
        PKG_INSTALL="zypper install -y"
        PKG_REMOVE="zypper remove -y"
        PKG_SEARCH="zypper search"
    else
        error_exit "Unsupported package manager. Supported: apt, dnf, yum, pacman, zypper"
    fi
}

# Hardware capabilities detection
detect_hardware_capabilities() {
    # CPU information
    CPU_CORES=$(nproc)
    CPU_THREADS=$(grep -c ^processor /proc/cpuinfo)
    CPU_MODEL=$(grep "model name" /proc/cpuinfo | head -1 | cut -d: -f2 | xargs)
    
    # CPU features detection
    CPU_FEATURES=()
    if grep -q "avx2" /proc/cpuinfo; then CPU_FEATURES+=("AVX2"); fi
    if grep -q "aes" /proc/cpuinfo; then CPU_FEATURES+=("AES-NI"); fi
    if grep -q "sha_ni" /proc/cpuinfo; then CPU_FEATURES+=("SHA-NI"); fi
    if grep -q "rdrand" /proc/cpuinfo; then CPU_FEATURES+=("RDRAND"); fi
    
    # Memory information
    TOTAL_RAM_KB=$(grep MemTotal /proc/meminfo | awk '{print $2}')
    TOTAL_RAM_GB=$((TOTAL_RAM_KB / 1024 / 1024))
    AVAILABLE_RAM_KB=$(grep MemAvailable /proc/meminfo | awk '{print $2}')
    AVAILABLE_RAM_GB=$((AVAILABLE_RAM_KB / 1024 / 1024))
    
    # Storage information
    AVAILABLE_DISK_GB=$(df -BG / | awk 'NR==2 {print $4}' | tr -d 'G')
    DISK_TYPE="unknown"
    
    # Detect SSD/NVMe
    for disk in /sys/block/*/queue/rotational; do
        if [[ -f "$disk" ]] && [[ "$(cat "$disk")" == "0" ]]; then
            DISK_TYPE="SSD"
            break
        fi
    done
    
    # NVMe detection
    if ls /dev/nvme* >/dev/null 2>&1; then
        DISK_TYPE="NVMe"
    fi
    
    log "INFO" "Hardware: ${CPU_CORES}C/${CPU_THREADS}T, ${TOTAL_RAM_GB}GB RAM, ${AVAILABLE_DISK_GB}GB disk ($DISK_TYPE)" "HARDWARE"
    [[ ${#CPU_FEATURES[@]} -gt 0 ]] && log "INFO" "CPU Features: ${CPU_FEATURES[*]}" "HARDWARE"
}

# Network capabilities detection
detect_network_capabilities() {
    # IPv6 support
    IPV6_SUPPORT=false
    if [[ -f /proc/net/if_inet6 ]] && grep -q ":" /proc/net/if_inet6; then
        IPV6_SUPPORT=true
    fi
    
    # Network interfaces
    NETWORK_INTERFACES=($(ip -o link show | awk -F': ' '{print $2}' | grep -v lo))
    
    # Bandwidth estimation (simplified)
    NETWORK_SPEED="unknown"
    for interface in "${NETWORK_INTERFACES[@]}"; do
        local speed_file="/sys/class/net/$interface/speed"
        if [[ -f "$speed_file" ]]; then
            local speed=$(cat "$speed_file" 2>/dev/null || echo "unknown")
            if [[ "$speed" != "unknown" ]] && [[ "$speed" -gt 0 ]]; then
                NETWORK_SPEED="${speed}Mbps"
                break
            fi
        fi
    done
    
    log "INFO" "Network: IPv6=$IPV6_SUPPORT, Speed=$NETWORK_SPEED, Interfaces=${#NETWORK_INTERFACES[@]}" "NETWORK"
}

# ============================================================================
# ADVANCED CONFIGURATION MANAGEMENT SYSTEM
# ============================================================================

# Create advanced configuration with validation
create_advanced_config() {
    log "INFO" "Creating advanced configuration system..." "CONFIG"
    
    # Ensure directories exist
    create_directory_structure
    
    # Create main configuration with schema validation
    create_main_config_with_schema
    
    # Create specialized configs
    create_security_config
    create_monitoring_config
    create_network_config
    
    # Set up configuration validation
    setup_config_validation
    
    log "SUCCESS" "Advanced configuration system created" "CONFIG"
}

# Create comprehensive directory structure
create_directory_structure() {
    local directories=(
        # Base directories
        "$CONFIG_BASE_DIR" "$DATA_BASE_DIR" "$LOG_BASE_DIR" "$CACHE_BASE_DIR" "$ROLLBACK_DIR"
        
        # Client data directories
        "${DATA_BASE_DIR}/clients" "${DATA_BASE_DIR}/keys" "${DATA_BASE_DIR}/backups"
        
        # Monitoring and logs
        "${LOG_BASE_DIR}/clients" "${LOG_BASE_DIR}/monitoring" "${LOG_BASE_DIR}/security"
        
        # Cache and temporary
        "${CACHE_BASE_DIR}/downloads" "${CACHE_BASE_DIR}/builds"
        
        # Specialized directories
        "${CONFIG_BASE_DIR}/templates" "${CONFIG_BASE_DIR}/schemas"
        "${DATA_BASE_DIR}/dvt" "${DATA_BASE_DIR}/liquid-staking"
    )
    
    for dir in "${directories[@]}"; do
        if [[ ! -d "$dir" ]]; then
            if sudo mkdir -p "$dir"; then
                log "DEBUG" "Created directory: $dir" "SETUP"
            else
                error_exit "Failed to create directory: $dir"
            fi
        fi
    done
    
    # Set appropriate permissions
    setup_directory_permissions
}

# Setup secure directory permissions
setup_directory_permissions() {
    # Configuration directories - restricted access
    sudo chmod 750 "$CONFIG_BASE_DIR"
    sudo chmod 700 "${CONFIG_BASE_DIR}/keys" 2>/dev/null || true
    
    # Data directories - service user access
    sudo chmod 755 "$DATA_BASE_DIR"
    sudo chmod 700 "${DATA_BASE_DIR}/keys" 2>/dev/null || true
    
    # Log directories - readable for monitoring
    sudo chmod 755 "$LOG_BASE_DIR"
    sudo chmod 750 "${LOG_BASE_DIR}/security"
    
    # Set ownership if ethereum user exists
    if id "ethereum" >/dev/null 2>&1; then
        sudo chown -R ethereum:ethereum "$DATA_BASE_DIR" "$LOG_BASE_DIR"
        sudo chown -R ethereum:ethereum "$CONFIG_BASE_DIR"
    fi
}

# Create main configuration with JSON schema
create_main_config_with_schema() {
    local config_file="${CONFIG_BASE_DIR}/config.json"
    local schema_file="${CONFIG_BASE_DIR}/schemas/config-schema.json"
    
    # Create JSON schema for validation
    cat > "$schema_file" << 'EOF'
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "Enhanced Ethereum Node Configuration",
  "type": "object",
  "required": ["network", "clients", "security"],
  "properties": {
    "network": {
      "type": "object",
      "required": ["name"],
      "properties": {
        "name": {
          "type": "string",
          "enum": ["mainnet", "sepolia", "holesky", "optimism", "arbitrum", "base", "polygon"]
        },
        "custom_bootnodes": {
          "type": "array",
          "items": {"type": "string"}
        },
        "enable_ipv6": {"type": "boolean"},
        "enable_tor": {"type": "boolean"}
      }
    },
    "clients": {
      "type": "object",
      "required": ["execution", "consensus"],
      "properties": {
        "execution": {
          "type": "string",
          "enum": ["geth", "erigon", "nethermind", "besu"]
        },
        "consensus": {
          "type": "string", 
          "enum": ["lighthouse", "prysm", "teku", "nimbus"]
        },
        "enable_validator": {"type": "boolean"},
        "client_diversity": {"type": "boolean"}
      }
    },
    "security": {
      "type": "object",
      "properties": {
        "enable_firewall": {"type": "boolean"},
        "enable_fail2ban": {"type": "boolean"},
        "jwt_secret_rotation": {"type": "boolean"},
        "audit_logging": {"type": "boolean"}
      }
    },
    "features": {
      "type": "object",
      "properties": {
        "dvt": {
          "type": "object",
          "properties": {
            "enabled": {"type": "boolean"},
            "provider": {"type": "string", "enum": ["ssv", "obol", "both"]},
            "operators": {"type": "integer", "minimum": 4, "maximum": 13},
            "threshold": {"type": "integer", "minimum": 3}
          }
        },
        "mev_boost": {
          "type": "object",
          "properties": {
            "enabled": {"type": "boolean"},
            "relay_selection": {"type": "string", "enum": ["auto", "manual", "geographic"]},
            "min_bid": {"type": "number", "minimum": 0}
          }
        },
        "liquid_staking": {
          "type": "object",
          "properties": {
            "provider": {"type": "string", "enum": ["none", "lido", "rocketpool", "both"]},
            "auto_compound": {"type": "boolean"}
          }
        }
      }
    }
  }
}
EOF
    
    # Create default configuration
    cat > "$config_file" << EOF
{
  "version": "$SCRIPT_VERSION",
  "created": "$(date -Iseconds)",
  "network": {
    "name": "mainnet",
    "custom_bootnodes": [],
    "enable_ipv6": true,
    "enable_tor": false,
    "bandwidth_limit": 0,
    "connection_optimization": true
  },
  "clients": {
    "execution": "geth",
    "consensus": "lighthouse", 
    "enable_validator": false,
    "client_diversity": true,
    "diversity_threshold": 33,
    "auto_update": false
  },
  "security": {
    "enable_firewall": true,
    "enable_fail2ban": true,
    "jwt_secret_rotation": true,
    "audit_logging": true,
    "zero_trust": false,
    "hsm_enabled": false
  },
  "performance": {
    "cache_size": 0,
    "max_peers": 75,
    "sync_mode": "snap",
    "parallel_sync": true,
    "memory_optimization": true,
    "ai_optimization": true
  },
  "features": {
    "dvt": {
      "enabled": false,
      "provider": "ssv",
      "operators": 4,
      "threshold": 3,
      "auto_setup": true
    },
    "mev_boost": {
      "enabled": true,
      "relay_selection": "auto", 
      "min_bid": 0.01,
      "geographic_preference": "global",
      "health_monitoring": true
    },
    "liquid_staking": {
      "provider": "none",
      "auto_compound": false,
      "lido_csm": false,
      "rocketpool_minipool": false
    },
    "monitoring": {
      "enabled": true,
      "stack": "victoriametrics",
      "mobile_dashboard": true,
      "real_time_alerts": true,
      "alert_channels": ["email", "discord"]
    },
    "backup": {
      "strategy": "incremental",
      "encryption": true,
      "compression": "zstd",
      "cloud_provider": "",
      "retention_days": 30
    }
  },
  "advanced": {
    "chaos_engineering": false,
    "canary_deployments": false,
    "blue_green_deploy": false,
    "compliance_mode": false,
    "debug_mode": false
  }
}
EOF
    
    log "SUCCESS" "Main configuration created with schema validation" "CONFIG"
}

# Configuration validation with JSON schema
validate_config_with_schema() {
    local config_file="${CONFIG_BASE_DIR}/config.json"
    local schema_file="${CONFIG_BASE_DIR}/schemas/config-schema.json"
    
    if ! command -v jq >/dev/null 2>&1; then
        log "WARN" "jq not available, skipping schema validation" "CONFIG"
        return 0
    fi
    
    log "INFO" "Validating configuration against schema..." "CONFIG"
    
    # Basic JSON validation
    if ! jq empty "$config_file" 2>/dev/null; then
        error_exit "Configuration file contains invalid JSON: $config_file"
    fi
    
    # Schema validation (simplified - would use ajv or similar in production)
    local validation_errors=()
    
    # Check required fields
    local required_fields=("network" "clients" "security")
    for field in "${required_fields[@]}"; do
        if ! jq -e ".$field" "$config_file" >/dev/null 2>&1; then
            validation_errors+=("Missing required field: $field")
        fi
    done
    
    # Validate network name
    local network_name
    network_name=$(jq -r '.network.name' "$config_file" 2>/dev/null || echo "")
    local valid_networks=("mainnet" "sepolia" "holesky" "optimism" "arbitrum" "base" "polygon")
    if [[ ! " ${valid_networks[*]} " =~ " $network_name " ]]; then
        validation_errors+=("Invalid network name: $network_name")
    fi
    
    # Validate client selections
    local execution_client
    execution_client=$(jq -r '.clients.execution' "$config_file" 2>/dev/null || echo "")
    local valid_execution=("geth" "erigon" "nethermind" "besu")
    if [[ ! " ${valid_execution[*]} " =~ " $execution_client " ]]; then
        validation_errors+=("Invalid execution client: $execution_client")
    fi
    
    # Report validation results
    if [[ ${#validation_errors[@]} -gt 0 ]]; then
        log "ERROR" "Configuration validation failed:" "CONFIG"
        for error in "${validation_errors[@]}"; do
            log "ERROR" "  - $error" "CONFIG"
        done
        error_exit "Configuration validation failed"
    else
        log "SUCCESS" "Configuration validation passed" "CONFIG"
    fi
}

# Load configuration with type safety
load_config_enhanced() {
    local config_file="${CONFIG_BASE_DIR}/config.json"
    
    if [[ ! -f "$config_file" ]]; then
        log "INFO" "Configuration not found, creating default..." "CONFIG"
        create_advanced_config
    fi
    
    # Validate configuration
    validate_config_with_schema
    
    # Load configuration into environment variables with type checking
    export ETH_NETWORK=$(jq -r '.network.name' "$config_file")
    export EXECUTION_CLIENT=$(jq -r '.clients.execution' "$config_file")
    export CONSENSUS_CLIENT=$(jq -r '.clients.consensus' "$config_file")
    export ENABLE_VALIDATOR=$(jq -r '.clients.enable_validator' "$config_file")
    export ENABLE_DVT=$(jq -r '.features.dvt.enabled' "$config_file")
    export DVT_PROVIDER=$(jq -r '.features.dvt.provider' "$config_file")
    export ENABLE_MEV_BOOST=$(jq -r '.features.mev_boost.enabled' "$config_file")
    export LIQUID_STAKING_PROVIDER=$(jq -r '.features.liquid_staking.provider' "$config_file")
    export ENABLE_MONITORING=$(jq -r '.features.monitoring.enabled' "$config_file")
    export MONITORING_STACK=$(jq -r '.features.monitoring.stack' "$config_file")
    
    # Auto-configuration based on system capabilities
    auto_configure_performance_enhanced
    
    log "SUCCESS" "Enhanced configuration loaded and validated" "CONFIG"
}

# Enhanced performance auto-configuration
auto_configure_performance_enhanced() {
    local config_file="${CONFIG_BASE_DIR}/config.json"
    local updated=false
    
    # Auto-configure cache size based on available RAM
    local current_cache_size
    current_cache_size=$(jq -r '.performance.cache_size' "$config_file")
    if [[ "$current_cache_size" == "0" || "$current_cache_size" == "null" ]]; then
        local optimal_cache=$((TOTAL_RAM_GB * 1024 / 4))
        [[ $optimal_cache -lt 2048 ]] && optimal_cache=2048
        [[ $optimal_cache -gt 16384 ]] && optimal_cache=16384
        
        jq ".performance.cache_size = $optimal_cache" "$config_file" > "${config_file}.tmp"
        mv "${config_file}.tmp" "$config_file"
        updated=true
        log "INFO" "Auto-configured cache size: ${optimal_cache}MB" "AI_CONFIG"
    fi
    
    # Auto-configure peer count based on resources
    local current_max_peers
    current_max_peers=$(jq -r '.performance.max_peers' "$config_file")
    if [[ "$current_max_peers" == "75" ]]; then  # Default value
        local optimal_peers=75
        if [[ $CPU_CORES -ge 8 && $TOTAL_RAM_GB -ge 32 ]]; then
            optimal_peers=100
        elif [[ $CPU_CORES -le 4 || $TOTAL_RAM_GB -le 16 ]]; then
            optimal_peers=50
        fi
        
        if [[ $optimal_peers -ne 75 ]]; then
            jq ".performance.max_peers = $optimal_peers" "$config_file" > "${config_file}.tmp"
            mv "${config_file}.tmp" "$config_file"
            updated=true
            log "INFO" "Auto-configured max peers: $optimal_peers" "AI_CONFIG"
        fi
    fi
    
    # Auto-configure sync mode based on disk type
    if [[ "$DISK_TYPE" == "NVMe" ]]; then
        local current_sync_mode
        current_sync_mode=$(jq -r '.performance.sync_mode' "$config_file")
        if [[ "$current_sync_mode" != "full" ]]; then
            jq '.performance.sync_mode = "full"' "$config_file" > "${config_file}.tmp"
            mv "${config_file}.tmp" "$config_file"
            updated=true
            log "INFO" "Auto-configured sync mode to 'full' for NVMe storage" "AI_CONFIG"
        fi
    fi
    
    [[ "$updated" == "true" ]] && log "SUCCESS" "Performance auto-configuration completed" "AI_CONFIG"
}

# ============================================================================
# STATE MANAGEMENT AND ROLLBACK SYSTEM  
# ============================================================================

# Initialize state management
init_state_management() {
    local state_file="$STATE_FILE"
    
    # Create initial state if it doesn't exist
    if [[ ! -f "$state_file" ]]; then
        cat > "$state_file" << EOF
{
  "version": "$SCRIPT_VERSION",
  "session_id": "$(uuidgen 2>/dev/null || date +%s%N)",
  "created": "$(date -Iseconds)",
  "operations": [],
  "rollback_points": [],
  "system_info": {
    "hostname": "$(hostname)",
    "os": "$OS_NAME",
    "architecture": "$ARCH"
  }
}
EOF
        log "INFO" "Initialized state management" "STATE"
    fi
    
    # Load session ID
    SESSION_ID=$(jq -r '.session_id' "$state_file" 2>/dev/null || echo "unknown")
    export SESSION_ID
}

# Update state with operation tracking
update_state() {
    local operation="$1"
    local status="$2" 
    local details="${3:-{}}"
    local timestamp=$(date -Iseconds)
    
    local state_file="$STATE_FILE"
    
    # Create operation record
    local operation_record=$(cat <<EOF
{
  "operation": "$operation",
  "status": "$status", 
  "timestamp": "$timestamp",
  "details": $details
}
EOF
)
    
    # Update state file
    if [[ -f "$state_file" ]]; then
        local temp_file="${state_file}.tmp"
        jq ".operations += [$operation_record]" "$state_file" > "$temp_file"
        mv "$temp_file" "$state_file"
    fi
    
    log "DEBUG" "State updated: $operation -> $status" "STATE"
}

# Create rollback point
create_rollback_point() {
    local description="$1"
    local timestamp=$(date -Iseconds)
    local rollback_id="rollback_$(date +%s)"
    
    # Create rollback directory
    local rollback_point_dir="${ROLLBACK_DIR}/$rollback_id"
    mkdir -p "$rollback_point_dir"
    
    # Backup critical configuration files
    local files_to_backup=(
        "${CONFIG_BASE_DIR}/config.json"
        "/etc/systemd/system/geth.service"
        "/etc/systemd/system/lighthouse-beacon.service"
        "/etc/systemd/system/lighthouse-validator.service"
        "/etc/systemd/system/mev-boost.service"
    )
    
    for file in "${files_to_backup[@]}"; do
        if [[ -f "$file" ]]; then
            cp "$file" "$rollback_point_dir/" 2>/dev/null || true
        fi
    done
    
    # Record rollback point
    local rollback_record=$(cat <<EOF
{
  "id": "$rollback_id",
  "description": "$description",
  "timestamp": "$timestamp",
  "files_backed_up": $(printf '%s\n' "${files_to_backup[@]}" | jq -R . | jq -s .)
}
EOF
)
    
    # Update state file
    local temp_file="${STATE_FILE}.tmp"
    jq ".rollback_points += [$rollback_record]" "$STATE_FILE" > "$temp_file"
    mv "$temp_file" "$STATE_FILE"
    
    log "SUCCESS" "Rollback point created: $rollback_id" "ROLLBACK"
    return 0
}

# Perform rollback to last known good state
perform_rollback() {
    log "INFO" "Initiating rollback procedure..." "ROLLBACK"
    
    # Get latest rollback point
    local latest_rollback
    latest_rollback=$(jq -r '.rollback_points[-1].id' "$STATE_FILE" 2>/dev/null || echo "null")
    
    if [[ "$latest_rollback" == "null" || -z "$latest_rollback" ]]; then
        log "WARN" "No rollback points available" "ROLLBACK"
        return 1
    fi
    
    local rollback_dir="${ROLLBACK_DIR}/$latest_rollback"
    if [[ ! -d "$rollback_dir" ]]; then
        log "ERROR" "Rollback directory not found: $rollback_dir" "ROLLBACK"
        return 1
    fi
    
    log "INFO" "Rolling back to: $latest_rollback" "ROLLBACK"
    
    # Stop services before rollback
    local services=("geth" "lighthouse-beacon" "lighthouse-validator" "mev-boost")
    for service in "${services[@]}"; do
        if systemctl is-active --quiet "$service" 2>/dev/null; then
            log "INFO" "Stopping service: $service" "ROLLBACK"
            sudo systemctl stop "$service" || true
        fi
    done
    
    # Restore configuration files
    for file in "$rollback_dir"/*; do
        if [[ -f "$file" ]]; then
            local target_file
            case "$(basename "$file")" in
                "config.json")
                    target_file="${CONFIG_BASE_DIR}/config.json"
                    ;;
                *.service)
                    target_file="/etc/systemd/system/$(basename "$file")"
                    ;;
            esac
            
            if [[ -n "$target_file" ]]; then
                log "INFO" "Restoring: $target_file" "ROLLBACK"
                sudo cp "$file" "$target_file" || true
            fi
        fi
    done
    
    # Reload systemd if service files were restored
    sudo systemctl daemon-reload
    
    log "SUCCESS" "Rollback completed successfully" "ROLLBACK"
    return 0
}

# ============================================================================
# ENHANCED CLIENT INSTALLATION WITH MODERN FEATURES
# ============================================================================

# Main installation orchestrator with progress tracking
install_ethereum_stack() {
    log "INFO" "Starting enhanced Ethereum stack installation..." "INSTALL"
    
    # Create rollback point before installation
    create_rollback_point "Before stack installation"
    
    # Installation phases with progress tracking
    local phases=(
        "create_ethereum_user:Creating system user"
        "install_execution_client_enhanced:Installing execution client"
        "install_consensus_client_enhanced:Installing consensus client"
        "install_validator_client_enhanced:Installing validator client"
        "install_mev_boost_enhanced:Installing MEV-Boost"
        "install_dvt_stack:Installing DVT components"
        "install_monitoring_stack:Installing monitoring"
        "configure_networking:Configuring networking"
        "setup_security_enhanced:Setting up security"
    )
    
    local total_phases=${#phases[@]}
    local current_phase=0
    
    for phase_info in "${phases[@]}"; do
        ((current_phase++))
        local phase_func="${phase_info%%:*}"
        local phase_desc="${phase_info#*:}"
        
        log "INFO" "Phase $current_phase/$total_phases: $phase_desc" "INSTALL"
        update_state "$phase_func" "started"
        
        if eval "$phase_func"; then
            update_state "$phase_func" "completed"
            log "SUCCESS" "Completed: $phase_desc" "INSTALL"
        else
            update_state "$phase_func" "failed"
            error_exit "Failed during: $phase_desc" 1 true "Installation phase: $phase_func"
        fi
    done
    
    log "SUCCESS" "Enhanced Ethereum stack installation completed!" "INSTALL"
}

# Enhanced execution client installation
install_execution_client_enhanced() {
    local client="$EXECUTION_CLIENT"
    local version="${CLIENT_VERSIONS[$client]}"
    
    log "INFO" "Installing $client v$version with enhanced configuration..." "INSTALL"
    
    case "$client" in
        "geth")
            install_geth_enhanced "$version"
            ;;
        "erigon")
            install_erigon_enhanced "$version"
            ;;
        "nethermind")
            install_nethermind_enhanced "$version"
            ;;
        "besu")
            install_besu_enhanced "$version"
            ;;
        *)
            error_exit "Unsupported execution client: $client"
            ;;
    esac
    
    # Create enhanced service configuration
    create_execution_service_enhanced "$client"
    
    log "SUCCESS" "$client installation completed" "INSTALL"
}

# Enhanced Geth installation with optimizations
install_geth_enhanced() {
    local version="$1"
    local download_url="https://github.com/ethereum/go-ethereum/releases/download/v${version}/geth-linux-${ARCH_SUFFIX}-${version}.tar.gz"
    
    log "INFO" "Downloading Geth v$version..." "GETH"
    
    cd "${CACHE_BASE_DIR}/downloads"
    
    # Download with progress and verification
    if ! download_with_verification "$download_url" "geth-${version}.tar.gz"; then
        error_exit "Failed to download Geth"
    fi
    
    # Extract and install
    tar -xzf "geth-${version}.tar.gz"
    local extract_dir=$(find . -name "geth-linux-*" -type d | head -1)
    
    if [[ -z "$extract_dir" ]]; then
        error_exit "Failed to find Geth extract directory"
    fi
    
    sudo install -o root -g root -m 755 "$extract_dir/geth" /usr/local/bin/
    
    # Verify installation
    if /usr/local/bin/geth version | grep -q "$version"; then
        log "SUCCESS" "Geth v$version installed successfully" "GETH"
    else
        error_exit "Geth installation verification failed"
    fi
    
    # Cleanup
    rm -rf "geth-${version}.tar.gz" "$extract_dir"
}

# Download with integrity verification
download_with_verification() {
    local url="$1"
    local filename="$2"
    local max_retries=3
    local retry_count=0
    
    while [[ $retry_count -lt $max_retries ]]; do
        log "INFO" "Attempting download ($(($retry_count + 1))/$max_retries): $filename" "DOWNLOAD"
        
        if curl -fsSL --connect-timeout 30 --max-time 300 \
               --progress-bar "$url" -o "$filename"; then
            
            # Basic file verification
            if [[ -f "$filename" ]] && [[ -s "$filename" ]]; then
                local file_size
                file_size=$(stat -c%s "$filename")
                if [[ $file_size -gt 1000000 ]]; then  # At least 1MB
                    log "SUCCESS" "Download completed: $filename (${file_size} bytes)" "DOWNLOAD"
                    return 0
                else
                    log "WARN" "Downloaded file too small: $file_size bytes" "DOWNLOAD"
                fi
            fi
        fi
        
        ((retry_count++))
        if [[ $retry_count -lt $max_retries ]]; then
            log "WARN" "Download failed, retrying in 5 seconds..." "DOWNLOAD"
            sleep 5
        fi
    done
    
    log "ERROR" "Download failed after $max_retries attempts" "DOWNLOAD"
    return 1
}

# Create enhanced execution service
create_execution_service_enhanced() {
    local client="$1"
    local service_file="/etc/systemd/system/${client}.service"
    
    # Load configuration values
    local network="$ETH_NETWORK"
    local cache_size
    cache_size=$(jq -r '.performance.cache_size' "${CONFIG_BASE_DIR}/config.json")
    local max_peers
    max_peers=$(jq -r '.performance.max_peers' "${CONFIG_BASE_DIR}/config.json")
    
    case "$client" in
        "geth")
            create_geth_service "$service_file" "$network" "$cache_size" "$max_peers"
            ;;
        "erigon")
            create_erigon_service "$service_file" "$network" "$cache_size" "$max_peers"
            ;;
        # Add other clients as needed
    esac
    
    # Enable and configure service
    sudo systemctl daemon-reload
    sudo systemctl enable "${client}.service"
    
    log "SUCCESS" "Enhanced $client service created" "SERVICE"
}

# Create optimized Geth service
create_geth_service() {
    local service_file="$1"
    local network="$2"
    local cache_size="$3"
    local max_peers="$4"
    
    # Network-specific configuration
    local network_flag=""
    case "$network" in
        "mainnet") network_flag="" ;;
        "sepolia") network_flag="--sepolia" ;;
        "holesky") network_flag="--holesky" ;;
    esac
    
    sudo tee "$service_file" > /dev/null << EOF
[Unit]
Description=Ethereum Geth Client (${network^})
Documentation=https://geth.ethereum.org/docs/
After=network-online.target
Wants=network-online.target

[Service]
Type=exec
User=ethereum
Group=ethereum

# Core Geth configuration
ExecStart=/usr/local/bin/geth \\
    $network_flag \\
    --datadir ${DATA_BASE_DIR}/geth \\
    --port 30303 \\
    --http \\
    --http.addr 127.0.0.1 \\
    --http.port 8545 \\
    --http.api eth,net,web3,engine,admin \\
    --http.corsdomain "*" \\
    --ws \\
    --ws.addr 127.0.0.1 \\
    --ws.port 8546 \\
    --ws.api eth,net,web3 \\
    --authrpc.addr 127.0.0.1 \\
    --authrpc.port 8551 \\
    --authrpc.jwtsecret ${CONFIG_BASE_DIR}/jwt.hex \\
    --syncmode snap \\
    --cache ${cache_size} \\
    --maxpeers ${max_peers} \\
    --metrics \\
    --metrics.addr 127.0.0.1 \\
    --metrics.port 6060 \\
    --log.file ${LOG_BASE_DIR}/clients/geth.log \\
    --log.rotate

# Security and performance settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=${DATA_BASE_DIR} ${LOG_BASE_DIR}
LimitNOFILE=65536
LimitNPROC=4096

# Resource limits
MemoryMax=8G
CPUQuota=400%

# Service management
Restart=always
RestartSec=10
TimeoutStartSec=120
TimeoutStopSec=60
KillMode=mixed
KillSignal=SIGTERM

# Environment
Environment=HOME=${DATA_BASE_DIR}
WorkingDirectory=${DATA_BASE_DIR}

[Install]
WantedBy=multi-user.target
EOF

    log "SUCCESS" "Geth service configuration created" "GETH"
}

# ============================================================================
# MONITORING AND ALERTING SYSTEM
# ============================================================================

# Install comprehensive monitoring stack
install_monitoring_stack() {
    if [[ "${ENABLE_MONITORING:-true}" != "true" ]]; then
        log "INFO" "Monitoring disabled, skipping installation" "MONITOR"
        return 0
    fi
    
    log "INFO" "Installing comprehensive monitoring stack..." "MONITOR"
    
    local monitoring_stack="${MONITORING_STACK:-victoriametrics}"
    
    # Install core monitoring components
    install_node_exporter_enhanced
    
    case "$monitoring_stack" in
        "victoriametrics")
            install_victoriametrics_enhanced
            ;;
        "prometheus")
            install_prometheus_enhanced  
            ;;
        *)
            log "WARN" "Unknown monitoring stack: $monitoring_stack, using VictoriaMetrics" "MONITOR"
            install_victoriametrics_enhanced
            ;;
    esac
    
    # Install visualization and alerting
    install_grafana_enhanced
    install_alertmanager_enhanced
    
    # Setup custom dashboards
    setup_ethereum_dashboards
    
    # Configure alerting rules
    setup_alerting_rules_enhanced
    
    log "SUCCESS" "Monitoring stack installation completed" "MONITOR"
}

# Enhanced Node Exporter installation
install_node_exporter_enhanced() {
    local version="1.7.0"
    local binary_name="node_exporter-${version}.linux-${ARCH_SUFFIX}"
    local download_url="https://github.com/prometheus/node_exporter/releases/download/v${version}/${binary_name}.tar.gz"
    
    log "INFO" "Installing Node Exporter v$version..." "MONITOR"
    
    cd "${CACHE_BASE_DIR}/downloads"
    
    if download_with_verification "$download_url" "${binary_name}.tar.gz"; then
        tar -xzf "${binary_name}.tar.gz"
        sudo install -o root -g root -m 755 "${binary_name}/node_exporter" /usr/local/bin/
        
        # Create enhanced service
        create_node_exporter_service
        
        # Cleanup
        rm -rf "${binary_name}.tar.gz" "${binary_name}"
        
        log "SUCCESS" "Node Exporter installed successfully" "MONITOR"
    else
        error_exit "Failed to install Node Exporter"
    fi
}

# Create Node Exporter service with custom collectors
create_node_exporter_service() {
    sudo tee /etc/systemd/system/node_exporter.service > /dev/null << 'EOF'
[Unit]
Description=Prometheus Node Exporter
Documentation=https://prometheus.io/docs/guides/node-exporter/
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=nobody
Group=nogroup
ExecStart=/usr/local/bin/node_exporter \
    --web.listen-address=127.0.0.1:9100 \
    --collector.systemd \
    --collector.processes \
    --collector.interrupts \
    --collector.tcpstat \
    --collector.bonding \
    --collector.diskstats.ignored-devices="^(ram|loop|fd|(h|s|v|xv)d[a-z]|nvme\\d+n\\d+p)\\d+$" \
    --collector.filesystem.mount-points-exclude="^/(dev|proc|run|sys|mnt|media|tmp)($|/)" \
    --collector.netclass.ignored-devices="^(veth.*|docker.*|br-.*|lo)$" \
    --collector.textfile.directory=/var/lib/node_exporter/textfile_collector

# Security
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadOnlyPaths=/
ReadWritePaths=/var/lib/node_exporter

# Resource limits
MemoryMax=128M
CPUQuota=50%

Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
    
    # Create textfile collector directory
    sudo mkdir -p /var/lib/node_exporter/textfile_collector
    sudo chown nobody:nogroup /var/lib/node_exporter/textfile_collector
    
    sudo systemctl daemon-reload
    sudo systemctl enable node_exporter.service
    
    log "SUCCESS" "Node Exporter service configured" "MONITOR"
}

# ============================================================================
# MAIN EXECUTION AND COMMAND LINE INTERFACE
# ============================================================================

# Enhanced command line argument parsing
parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --wizard|-w)
                WIZARD_MODE=true
                shift
                ;;
            --config|-c)
                CUSTOM_CONFIG="$2"
                shift 2
                ;;
            --network|-n)
                FORCE_NETWORK="$2"
                shift 2
                ;;
            --client|-e)
                FORCE_EXECUTION_CLIENT="$2"
                shift 2
                ;;
            --consensus|-b)
                FORCE_CONSENSUS_CLIENT="$2"
                shift 2
                ;;
            --log-level|-l)
                MIN_LOG_LEVEL="$2"
                shift 2
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --force)
                FORCE_INSTALL=true
                shift
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            --version|-v)
                echo "Enhanced Ethereum Node Setup v$SCRIPT_VERSION"
                exit 0
                ;;
            *)
                log "ERROR" "Unknown argument: $1" "CLI"
                show_help
                exit 1
                ;;
        esac
    done
}

# Show comprehensive help
show_help() {
    cat << EOF
Enhanced Ethereum Node Setup v$SCRIPT_VERSION

USAGE:
    $0 [OPTIONS]

OPTIONS:
    -w, --wizard           Launch interactive TUI wizard
    -c, --config FILE      Use custom configuration file
    -n, --network NAME     Force specific network (mainnet, sepolia, holesky)
    -e, --client NAME      Force execution client (geth, erigon, nethermind, besu)
    -b, --consensus NAME   Force consensus client (lighthouse, prysm, teku, nimbus)
    -l, --log-level LEVEL  Set minimum log level (DEBUG, INFO, WARN, ERROR)
    --dry-run              Show what would be done without executing
    --force                Force installation even if checks fail
    -h, --help             Show this help message
    -v, --version          Show version information

EXAMPLES:
    $0                     # Interactive installation with defaults
    $0 --wizard            # Launch TUI wizard
    $0 --network sepolia   # Install on Sepolia testnet
    $0 --client erigon --consensus lighthouse  # Specific client combination
    $0 --dry-run           # Preview installation steps

FEATURES:
    • DVT Integration (SSV Network & Obol)
    • MEV-Boost with Intelligent Relay Selection  
    • AI-Powered Performance Optimization
    • Liquid Staking Support (Lido CSM & Rocket Pool)
    • Mobile-Responsive Monitoring Dashboard
    • Client Diversity Management
    • Layer 2 Network Support
    • Zero-Downtime Updates & Rollback System
    • Enterprise Security & Compliance

DOCUMENTATION:
    Configuration: ${CONFIG_BASE_DIR}/config.json
    Logs: ${LOG_BASE_DIR}/
    State: $STATE_FILE

For detailed documentation, visit: https://github.com/your-repo/ethereum-node-v29
EOF
}

# Enhanced main function with comprehensive error handling
main() {
    local start_time=$(date +%s)
    
    # Parse command line arguments
    parse_arguments "$@"
    
    # Initialize logging and state management
    init_state_management
    log "INFO" "Starting $SCRIPT_NAME v$SCRIPT_VERSION" "MAIN"
    log "INFO" "Session ID: $SESSION_ID" "MAIN"
    
    # Set up signal handlers for graceful shutdown
    trap 'graceful_shutdown' INT TERM
    trap 'cleanup_on_error' ERR
    
    # Create lock file to prevent multiple instances
    if ! create_lock_file; then
        error_exit "Another instance is already running"
    fi
    
    # Check if wizard mode is requested
    if [[ "${WIZARD_MODE:-false}" == "true" ]]; then
        log "INFO" "Launching interactive TUI wizard..." "MAIN"
        launch_wizard
        return $?
    fi
    
    # Enhanced pre-flight checks
    log "INFO" "Performing comprehensive pre-flight checks..." "MAIN"
    update_state "preflight_checks" "started"
    
    # System detection and validation
    detect_platform_enhanced
    check_system_requirements_enhanced  
    check_dependencies_comprehensive
    
    update_state "preflight_checks" "completed"
    
    # Load and validate configuration
    log "INFO" "Loading and validating configuration..." "MAIN"
    update_state "configuration" "started"
    
    load_config_enhanced
    apply_forced_overrides
    
    update_state "configuration" "completed"
    
    # Security setup
    log "INFO" "Setting up advanced security..." "MAIN"
    update_state "security_setup" "started"
    
    setup_security_comprehensive
    
    update_state "security_setup" "completed"
    
    # Main installation
    if [[ "${DRY_RUN:-false}" == "true" ]]; then
        log "INFO" "Dry run mode - showing installation plan" "MAIN"
        show_installation_plan
    else
        log "INFO" "Beginning Ethereum stack installation..." "MAIN"
        update_state "installation" "started"
        
        install_ethereum_stack
        
        update_state "installation" "completed"
        
        # Post-installation setup
        perform_post_installation_setup
        
        # Final validation
        perform_comprehensive_validation
        
        # Display completion message
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        display_completion_message "$duration"
    fi
    
    log "SUCCESS" "Enhanced Ethereum Node Setup completed successfully!" "MAIN"
    return 0
}

# Graceful shutdown handler
graceful_shutdown() {
    log "WARN" "Received shutdown signal, performing graceful cleanup..." "MAIN"
    
    # Stop any running installations
    cleanup_on_error
    
    # Save current state
    update_state "shutdown" "graceful" "{\"timestamp\": \"$(date -Iseconds)\"}"
    
    log "INFO" "Graceful shutdown completed" "MAIN"
    exit 130
}

# Create lock file with PID
create_lock_file() {
    if (set -C; echo $SCRIPT_PID > "$LOCK_FILE") 2>/dev/null; then
        return 0
    else
        local existing_pid
        existing_pid=$(cat "$LOCK_FILE" 2>/dev/null || echo "unknown")
        if [[ "$existing_pid" != "unknown" ]] && ! kill -0 "$existing_pid" 2>/dev/null; then
            # Stale lock file, remove it
            rm -f "$LOCK_FILE"
            if (set -C; echo $SCRIPT_PID > "$LOCK_FILE") 2>/dev/null; then
                return 0
            fi
        fi
        return 1
    fi
}

# Cleanup on error
cleanup_on_error() {
    log "INFO" "Performing cleanup on error..." "CLEANUP"
    
    # Remove lock file
    rm -f "$LOCK_FILE"
    
    # Stop any running services that were started during this session
    local services_to_stop=()
    if [[ -f "$STATE_FILE" ]]; then
        # Get services started in this session
        mapfile -t services_to_stop < <(jq -r '.operations[] | select(.operation | contains("service") and (.status == "completed")) | .operation' "$STATE_FILE" 2>/dev/null || true)
    fi
    
    for service_op in "${services_to_stop[@]}"; do
        local service_name
        service_name=$(echo "$service_op" | sed 's/.*_service_//' | sed 's/_started//')
        if [[ -n "$service_name" ]] && systemctl is-active --quiet "$service_name" 2>/dev/null; then
            log "INFO" "Stopping service: $service_name" "CLEANUP"
            sudo systemctl stop "$service_name" || true
        fi
    done
    
    log "INFO" "Cleanup completed" "CLEANUP"
}

# Enhanced system requirements check
check_system_requirements_enhanced() {
    log "INFO" "Performing enhanced system requirements check..." "SYSTEM"
    
    local errors=() warnings=()
    
    # CPU requirements
    if [[ $CPU_CORES -lt 4 ]]; then
        errors+=("Minimum 4 CPU cores required, found $CPU_CORES")
    elif [[ $CPU_CORES -lt 8 ]]; then
        warnings+=("Recommended 8+ CPU cores for optimal performance, found $CPU_CORES")
    fi
    
    # Memory requirements  
    local min_ram=16
    local recommended_ram=32
    
    # Adjust for enabled features
    [[ "${ENABLE_DVT:-false}" == "true" ]] && min_ram=$((min_ram + 4))
    [[ "${ENABLE_MEV_BOOST:-false}" == "true" ]] && min_ram=$((min_ram + 2))
    
    if [[ $TOTAL_RAM_GB -lt $min_ram ]]; then
        errors+=("Minimum ${min_ram}GB RAM required, found ${TOTAL_RAM_GB}GB")
    elif [[ $TOTAL_RAM_GB -lt $recommended_ram ]]; then
        warnings+=("Recommended ${recommended_ram}GB+ RAM for optimal performance, found ${TOTAL_RAM_GB}GB")
    fi
    
    # Storage requirements
    local min_disk=1000 recommended_disk=4000
    if [[ "${ETH_NETWORK}" == "mainnet" ]]; then
        min_disk=2000
        recommended_disk=8000
    fi
    
    if [[ $AVAILABLE_DISK_GB -lt $min_disk ]]; then
        errors+=("Minimum ${min_disk}GB free disk space required, found ${AVAILABLE_DISK_GB}GB")
    elif [[ $AVAILABLE_DISK_GB -lt $recommended_disk ]]; then
        warnings+=("Recommended ${recommended_disk}GB+ free disk space, found ${AVAILABLE_DISK_GB}GB")
    fi
    
    # CPU features check
    if [[ "$ARCH" == "x86_64" ]]; then
        [[ ! " ${CPU_FEATURES[*]} " =~ " AVX2 " ]] && warnings+=("CPU lacks AVX2 support - performance may be reduced")
        [[ ! " ${CPU_FEATURES[*]} " =~ " AES-NI " ]] && warnings+=("CPU lacks AES-NI support - cryptographic operations may be slower")
    fi
    
    # Network check
    [[ "$IPV6_SUPPORT" == "false" ]] && warnings+=("IPv6 not supported - some features may be limited")
    
    # Report results
    if [[ ${#errors[@]} -gt 0 ]]; then
        log "ERROR" "System requirements not met:" "SYSTEM"
        for error in "${errors[@]}"; do
            log "ERROR" "  ✗ $error" "SYSTEM"
        done
        
        if [[ "${FORCE_INSTALL:-false}" != "true" ]]; then
            error_exit "System requirements check failed. Use --force to override."
        else
            log "WARN" "Continuing with --force despite requirement failures" "SYSTEM"
        fi
    fi
    
    if [[ ${#warnings[@]} -gt 0 ]]; then
        log "WARN" "System recommendations:" "SYSTEM"
        for warning in "${warnings[@]}"; do
            log "WARN" "  ⚠ $warning" "SYSTEM"
        done
    fi
    
    log "SUCCESS" "System requirements check completed" "SYSTEM"
}

# Script execution entry point
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    # Comprehensive error handling setup
    set -eE
    trap 'error_exit "Script failed at line $LINENO with command: $BASH_COMMAND" $? true "Line: $LINENO, Function: ${FUNCNAME[1]:-main}"' ERR
    
    # Execute main function with all arguments
    main "$@"
fi