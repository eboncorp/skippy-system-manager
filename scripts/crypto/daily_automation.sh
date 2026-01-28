#!/bin/bash
# Daily Crypto Automation
# Runs at 9 AM via cron
# Logs paper trades + sends email summary

set -e

# Load environment for Gmail
if [ -f /home/dave/skippy/scripts/crypto/.env ]; then
    source /home/dave/skippy/scripts/crypto/.env
fi
export GMAIL_APP_PASSWORD="${GMAIL_APP_PASSWORD:-}"

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

# Send email via Gmail SMTP
echo "Sending email report..." >> "$LOG_FILE"
python3 /home/dave/skippy/scripts/crypto/send_notifications.py --daily "$(cat "$LOG_FILE")" >> "$LOG_FILE" 2>&1

echo "Email sent at $(date)" >> "$LOG_FILE"

# Also output for cron log
cat "$LOG_FILE"
