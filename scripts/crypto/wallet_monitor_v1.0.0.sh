#!/bin/bash
# Wallet Monitor v1.0.0
# Quick check of all tracked ENS wallets via Etherscan
#
# Usage: wallet_monitor_v1.0.0.sh [--json]
#
# Created: 2026-01-24

set -euo pipefail

# Wallet configuration
declare -A WALLETS=(
    ["gti-inc.eth"]="0x19C3136369bb33cDFa409b3Adbf962BA97Ec1985"
    ["ebon.eth"]="0x34C761EDAfCBA14e7D921C3b1C38bD267498498d"
    ["paperwerk.eth"]="0x73732CC83a75FeC009D646A777993959d769E21f"
    ["biggers.eth"]="0xCA4cac9A3190aC5A863cb0E174d420E616Dd55Bc"
    ["parkfield.eth"]="0x46A15b9002291d619D86164C6606185B6d6e27a0"
    ["pennybrooke.eth"]="0x9D552E0D404e20ef7480535CF42813ecFEdC0feF"
    ["ebon-link.eth"]="0x8e7F9112D44e122b2Ae0f2f8c0A255dD60E78798"
)

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo ""
echo "==========================================="
echo "  Wallet Monitor - $(date '+%Y-%m-%d %H:%M')"
echo "==========================================="
echo ""

printf "%-18s %-44s %s\n" "ENS" "Address" "Etherscan"
printf "%-18s %-44s %s\n" "---" "-------" "---------"

for ens in "${!WALLETS[@]}"; do
    addr="${WALLETS[$ens]}"
    short_addr="${addr:0:10}...${addr: -8}"
    link="https://etherscan.io/address/${addr}"
    printf "%-18s %-44s %s\n" "$ens" "$short_addr" "$link"
done

echo ""
echo "==========================================="
echo "  Quick Links"
echo "==========================================="
echo ""
echo "DeBank Portfolio (all wallets):"
for ens in "${!WALLETS[@]}"; do
    addr="${WALLETS[$ens]}"
    echo "  $ens: https://debank.com/profile/${addr}"
done

echo ""
echo "To get detailed balances, run:"
echo "  python3 /home/dave/skippy/projects/crypto-portfolio/onchain_tracker.py --balances"
echo ""
