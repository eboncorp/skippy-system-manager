#!/bin/bash

# Script to expand LVM logical volume
# You have 1.52TB free space available

echo "==================================="
echo "LVM Volume Expansion Options"
echo "==================================="
echo ""
echo "Current Status:"
echo "---------------"
sudo vgs ubuntu-vg
echo ""
sudo lvs ubuntu-vg
echo ""
echo "Available free space: 1.52TB"
echo ""
echo "Options to expand the root volume:"
echo "1. Add 200GB (recommended for immediate needs)"
echo "2. Add 500GB (good for future growth)"
echo "3. Add 1TB (maximum headroom)"
echo "4. Custom amount"
echo "5. Exit without changes"
echo ""
read -p "Choose option (1-5): " choice

case $choice in
    1)
        SIZE="+200G"
        ;;
    2)
        SIZE="+500G"
        ;;
    3)
        SIZE="+1T"
        ;;
    4)
        read -p "Enter size (e.g., +100G): " SIZE
        ;;
    5)
        echo "Exiting without changes"
        exit 0
        ;;
    *)
        echo "Invalid option"
        exit 1
        ;;
esac

echo ""
echo "Will expand ubuntu-lv by $SIZE"
read -p "Continue? (y/n): " confirm

if [ "$confirm" != "y" ]; then
    echo "Cancelled"
    exit 0
fi

# Expand the logical volume
echo "Expanding logical volume..."
sudo lvextend -L $SIZE /dev/ubuntu-vg/ubuntu-lv

# Resize the filesystem
echo "Resizing filesystem..."
sudo resize2fs /dev/ubuntu-vg/ubuntu-lv

# Show new sizes
echo ""
echo "New sizes:"
sudo df -h /
echo ""
sudo lvs ubuntu-vg

echo ""
echo "✅ Volume expansion complete!"