#!/bin/bash
# Script Name: search_protocols
# Version: 2.0.0
# Purpose: Search protocols by keyword, tag, or category
# Created: 2025-11-10
# Upgrade from: v1.0.0 - Added category search, better formatting, scoring

# Configuration
BASE_PATH="${SKIPPY_BASE_PATH:-$(pwd)}"
DOC_PROTOCOLS="$BASE_PATH/documentation/protocols"
CONV_PROTOCOLS="$BASE_PATH/conversations"

# Colors
if [ -t 1 ]; then
    BLUE='\033[0;34m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    CYAN='\033[0;36m'
    NC='\033[0m'
else
    BLUE=''
    GREEN=''
    YELLOW=''
    CYAN=''
    NC=''
fi

# Help message
show_help() {
    cat << EOF
${BLUE}Protocol Search Tool v2.0.0${NC}

${GREEN}USAGE:${NC}
    $(basename $0) [OPTIONS] <search-term>

${GREEN}OPTIONS:${NC}
    -k, --keyword <term>     Search for keyword in protocol content
    -t, --tag <tag>          Search by tag (wordpress, security, git, etc.)
    -c, --category <cat>     Search by category (operations, development, etc.)
    -p, --priority <level>   Filter by priority (critical, high, medium, low)
    -l, --location <loc>     Search only in location (doc, conv, all)
    -v, --verbose            Show more context from matches
    -h, --help               Show this help message

${GREEN}EXAMPLES:${NC}
    # Search for "backup" keyword
    $(basename $0) backup
    $(basename $0) --keyword backup

    # Find WordPress protocols
    $(basename $0) --tag wordpress

    # Find security protocols
    $(basename $0) --category security

    # Find critical protocols
    $(basename $0) --priority critical

    # Search only in documentation/protocols
    $(basename $0) --location doc backup

    # Verbose output with context
    $(basename $0) -v deployment

${GREEN}CATEGORIES:${NC}
    - security      (Security & Access protocols)
    - operations    (Operations & Monitoring)
    - development   (Development & Git)
    - deployment    (Deployment & Publishing)
    - data          (Data & Content Management)
    - documentation (Documentation & Knowledge)
    - system        (System & Automation)
    - workflow      (Workflow & Process)

${GREEN}COMMON TAGS:${NC}
    wordpress, git, security, backup, deployment, testing,
    monitoring, documentation, emergency, critical

EOF
    exit 0
}

# Parse arguments
SEARCH_MODE="keyword"
SEARCH_TERM=""
LOCATION="all"
VERBOSE=false
PRIORITY_FILTER=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            ;;
        -k|--keyword)
            SEARCH_MODE="keyword"
            SEARCH_TERM="$2"
            shift 2
            ;;
        -t|--tag)
            SEARCH_MODE="tag"
            SEARCH_TERM="$2"
            shift 2
            ;;
        -c|--category)
            SEARCH_MODE="category"
            SEARCH_TERM="$2"
            shift 2
            ;;
        -p|--priority)
            PRIORITY_FILTER="$2"
            shift 2
            ;;
        -l|--location)
            LOCATION="$2"
            shift 2
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        *)
            if [ -z "$SEARCH_TERM" ]; then
                SEARCH_TERM="$1"
            fi
            shift
            ;;
    esac
done

# Validate search term
if [ -z "$SEARCH_TERM" ]; then
    echo -e "${YELLOW}Error: No search term provided${NC}"
    echo "Use --help for usage information"
    exit 1
fi

# Function to get protocol metadata
get_protocol_metadata() {
    local file=$1
    local name=$(basename "$file" .md)
    local version=$(grep -m1 "^\*\*Version" "$file" 2>/dev/null | sed 's/.*: *//')
    local priority=$(grep -m1 "^\*\*Priority" "$file" 2>/dev/null | sed 's/.*: *//')
    local location="conversations"

    if [[ "$file" == *"/documentation/protocols/"* ]]; then
        location="documentation"
    fi

    echo "$name|$version|$priority|$location"
}

# Function to search protocols
search_protocols() {
    local mode=$1
    local term=$2
    local results=()

    echo -e "${BLUE}═══ Searching Protocols ═══${NC}"
    echo -e "Mode: ${GREEN}$mode${NC}"
    echo -e "Term: ${GREEN}$term${NC}"
    if [ -n "$PRIORITY_FILTER" ]; then
        echo -e "Priority Filter: ${GREEN}$PRIORITY_FILTER${NC}"
    fi
    echo ""

    # Determine which directories to search
    local search_dirs=()
    if [ "$LOCATION" = "all" ] || [ "$LOCATION" = "doc" ]; then
        [ -d "$DOC_PROTOCOLS" ] && search_dirs+=("$DOC_PROTOCOLS")
    fi
    if [ "$LOCATION" = "all" ] || [ "$LOCATION" = "conv" ]; then
        [ -d "$CONV_PROTOCOLS" ] && search_dirs+=("$CONV_PROTOCOLS")
    fi

    # Search based on mode
    for dir in "${search_dirs[@]}"; do
        for file in "$dir"/*protocol*.md; do
            [ -f "$file" ] || continue
            [[ "$file" == *"/archive/"* ]] && continue
            [[ "$file" == *"/sessions/"* ]] && continue

            local match=false
            local context=""

            case $mode in
                keyword)
                    if grep -q -i "$term" "$file" 2>/dev/null; then
                        match=true
                        if [ "$VERBOSE" = true ]; then
                            context=$(grep -i -C 2 "$term" "$file" 2>/dev/null | head -10)
                        fi
                    fi
                    ;;
                tag)
                    # Search in filename and content
                    if [[ "$(basename $file)" =~ $term ]] || grep -q -i "\b$term\b" "$file" 2>/dev/null; then
                        match=true
                    fi
                    ;;
                category)
                    # Map categories to keywords
                    local category_keywords=""
                    case ${term,,} in
                        security) category_keywords="security|access|auth|credential|secret" ;;
                        operations) category_keywords="monitor|alert|incident|health|disaster" ;;
                        development) category_keywords="git|script|debug|code|test" ;;
                        deployment) category_keywords="deploy|publish|release|rollback" ;;
                        data) category_keywords="backup|data|content|migration|retention" ;;
                        documentation) category_keywords="document|knowledge|transcript|report" ;;
                        system) category_keywords="system|automation|tool|diagnostic" ;;
                        workflow) category_keywords="workflow|session|process|procedure" ;;
                    esac

                    if grep -q -iE "$category_keywords" "$file" 2>/dev/null || \
                       [[ "$(basename $file)" =~ $category_keywords ]]; then
                        match=true
                    fi
                    ;;
            esac

            # Apply priority filter if set
            if [ "$match" = true ] && [ -n "$PRIORITY_FILTER" ]; then
                if ! grep -q -i "Priority.*$PRIORITY_FILTER" "$file" 2>/dev/null; then
                    match=false
                fi
            fi

            if [ "$match" = true ]; then
                local metadata=$(get_protocol_metadata "$file")
                results+=("$file|$metadata|$context")
            fi
        done
    done

    # Display results
    if [ ${#results[@]} -eq 0 ]; then
        echo -e "${YELLOW}No protocols found matching: $term${NC}"
        exit 0
    fi

    echo -e "${GREEN}Found ${#results[@]} protocol(s):${NC}"
    echo ""

    local count=1
    for result in "${results[@]}"; do
        IFS='|' read -r file name version priority location context <<< "$result"

        echo -e "${CYAN}[$count]${NC} ${GREEN}$name${NC}"
        echo -e "    Location: $location/protocols/"
        [ -n "$version" ] && echo -e "    Version: $version"
        [ -n "$priority" ] && echo -e "    Priority: $priority"
        echo -e "    Path: $file"

        if [ "$VERBOSE" = true ] && [ -n "$context" ]; then
            echo -e "    ${YELLOW}Context:${NC}"
            echo "$context" | sed 's/^/      /'
        fi

        echo ""
        ((count++))
    done
}

# Main execution
search_protocols "$SEARCH_MODE" "$SEARCH_TERM"

exit 0
