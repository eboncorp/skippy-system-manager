#!/bin/bash

echo "🔧 Fixing Chrome and Firefox launch issues..."
echo ""

# Fix 1: Clear Chrome cache and profile locks
echo "1. Clearing Chrome locks and cache..."
rm -f ~/.config/google-chrome/Singleton*
rm -f ~/.config/google-chrome/Default/.org.chromium.Chromium.*
killall chrome 2>/dev/null
killall google-chrome 2>/dev/null

# Fix 2: Fix Firefox snap connections
echo "2. Fixing Firefox snap connections..."
sudo snap connect firefox:gpu-2404 :gpu-2404 2>/dev/null
sudo snap refresh firefox --stable 2>/dev/null

# Fix 3: Clear Firefox locks
echo "3. Clearing Firefox locks..."
rm -f ~/.mozilla/firefox/*.default*/.parentlock 2>/dev/null
rm -f ~/.mozilla/firefox/*.default*/lock 2>/dev/null
killall firefox 2>/dev/null

# Fix 4: Reset desktop database
echo "4. Refreshing desktop entries..."
update-desktop-database ~/.local/share/applications 2>/dev/null

# Fix 5: Create launcher scripts
echo "5. Creating launcher scripts..."

# Chrome launcher
cat > ~/chrome_launcher.sh << 'EOF'
#!/bin/bash
google-chrome --disable-gpu-sandbox --disable-software-rasterizer %U &
EOF
chmod +x ~/chrome_launcher.sh

# Firefox launcher
cat > ~/firefox_launcher.sh << 'EOF'
#!/bin/bash
firefox %U &
EOF
chmod +x ~/firefox_launcher.sh

echo ""
echo "✅ Browser fixes applied!"
echo ""
echo "Try launching browsers now. If clicking icons still doesn't work, use:"
echo "  Chrome:  ~/chrome_launcher.sh"
echo "  Firefox: ~/firefox_launcher.sh"
echo ""
echo "You may need to log out and back in for all changes to take effect."