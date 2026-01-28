#!/bin/bash
# Daily Crypto Automation
# Runs at 9 AM via cron
# Logs paper trades + sends email summary

set -e

LOG_DIR="/home/dave/skippy/work/crypto/daily_runs"
DATE=$(date +%Y%m%d)
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="$LOG_DIR/${DATE}_automation.log"

mkdir -p "$LOG_DIR"

echo "========================================" >> "$LOG_FILE"
echo "Daily Crypto Automation - $(date)" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"

# Run integrated portfolio manager with trading cycle
echo "Running portfolio analysis..." >> "$LOG_FILE"
python3 /home/dave/skippy/scripts/crypto/integrated_portfolio_manager.py --trade >> "$LOG_FILE" 2>&1

echo "" >> "$LOG_FILE"
echo "Running full dashboard..." >> "$LOG_FILE"
python3 /home/dave/skippy/scripts/crypto/integrated_portfolio_manager.py >> "$LOG_FILE" 2>&1

# Create email content
EMAIL_FILE="/tmp/crypto_daily_${TIMESTAMP}.txt"

cat > "$EMAIL_FILE" << EMAILEOF
DAILY CRYPTO AUTOMATION - $(date +%Y-%m-%d)
================================================

$(cat "$LOG_FILE")

------------------------------------------------
Log saved to: $LOG_FILE
Paper trades: /home/dave/skippy/work/crypto/integrated/trades_${DATE}.json

This is automated paper trading. No real trades executed.
EMAILEOF

echo "" >> "$LOG_FILE"
echo "Automation complete at $(date)" >> "$LOG_FILE"
echo "Email content saved to: $EMAIL_FILE" >> "$LOG_FILE"

# Output for cron email or manual review
cat "$EMAIL_FILE"
