#!/bin/bash
# Integration Test for Skippy Ecosystem
# Tests all major components work together

echo "=================================="
echo "Skippy Integration Test"
echo "=================================="
echo ""

# Test 1: Check daemon is running
echo "[1/8] Testing file processor daemon..."
if pgrep -f file_processor_daemon > /dev/null; then
  echo "✅ Daemon running"
else
  echo "❌ Daemon not running"
  exit 1
fi

# Test 2: Check API key is loaded
echo "[2/8] Testing API key..."
if pgrep -f file_processor_daemon | xargs -I {} cat /proc/{}/environ | tr '\0' '\n' | grep -q ANTHROPIC_API_KEY; then
  echo "✅ API key loaded in daemon"
else
  echo "❌ API key not found"
fi

# Test 3: Test skippy-files CLI
echo "[3/8] Testing CLI tools..."
if python3 skippy-files stats --period 1 > /dev/null 2>&1; then
  echo "✅ CLI working"
else
  echo "❌ CLI failed"
fi

# Test 4: Check watch folders exist
echo "[4/8] Testing watch folders..."
MISSING=0
for folder in operations/downloads operations/claude/downloads operations/claude/uploads operations/scans/incoming; do
  if [ ! -d "/home/dave/skippy/$folder" ]; then
    echo "❌ Missing: $folder"
    MISSING=1
  fi
done
[ $MISSING -eq 0 ] && echo "✅ All watch folders exist"

# Test 5: Check destination folders
echo "[5/8] Testing destination folders..."
MISSING=0
for folder in business/campaign business/eboncorp personal media/photos operations/quarantine; do
  if [ ! -d "/home/dave/skippy/$folder" ]; then
    echo "❌ Missing: $folder"
    MISSING=1
  fi
done
[ $MISSING -eq 0 ] && echo "✅ All destination folders exist"

# Test 6: Test file processing
echo "[6/8] Testing file processing..."
TEST_FILE="/home/dave/skippy/operations/downloads/integration_test_$(date +%s).txt"
echo "Test file for integration test - EbonCorp invoice \$100" > "$TEST_FILE"
sleep 8
if [ -f "$TEST_FILE" ]; then
  echo "⚠️  File still in downloads (may be quarantined)"
  rm -f "$TEST_FILE"
else
  echo "✅ File was processed"
fi

# Test 7: Check cron job
echo "[7/8] Testing cron integration..."
if crontab -l | grep -q "skippy/development/scripts"; then
  echo "✅ Cron jobs updated"
else
  echo "⚠️  Cron jobs may have old paths"
fi

# Test 8: Check bash aliases
echo "[8/8] Testing bash integration..."
if grep -q "skippy-status" ~/.bash_aliases 2>/dev/null; then
  echo "✅ Bash aliases configured"
else
  echo "⚠️  Bash aliases not found"
fi

echo ""
echo "=================================="
echo "Integration Test Complete"
echo "=================================="
