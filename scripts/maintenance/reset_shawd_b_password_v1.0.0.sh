#!/bin/bash

# Password reset script for shawd_b
echo "Password Reset for user: shawd_b"
echo "================================"
echo ""
echo "You will be prompted to enter the new password twice."
echo ""

# Reset the password
sudo passwd shawd_b

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Password successfully reset for shawd_b"
else
    echo ""
    echo "❌ Password reset failed"
fi