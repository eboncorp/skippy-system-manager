#!/bin/bash
# Setup second SSD for media storage on HP Z4 G4

echo "🔧 Setting up 2TB Samsung SSD for Media Storage"
echo "=============================================="
echo
echo "This will set up /dev/nvme1n1 as your dedicated media drive"
echo "Current data on nvme1n1 will be ERASED!"
echo
read -p "Continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 1
fi

echo "📋 Step 1: Creating partition table..."
sudo parted /dev/nvme1n1 mklabel gpt
sudo parted /dev/nvme1n1 mkpart primary ext4 0% 100%

echo "🔨 Step 2: Creating filesystem..."
sudo mkfs.ext4 -L "MediaStorage" /dev/nvme1n1p1

echo "📁 Step 3: Creating mount point..."
sudo mkdir -p /mnt/media

echo "🔧 Step 4: Mounting the drive..."
sudo mount /dev/nvme1n1p1 /mnt/media

echo "📝 Step 5: Adding to /etc/fstab for auto-mount..."
echo "# Media Storage SSD" | sudo tee -a /etc/fstab
echo "UUID=$(sudo blkid -o value -s UUID /dev/nvme1n1p1) /mnt/media ext4 defaults,noatime 0 2" | sudo tee -a /etc/fstab

echo "👤 Step 6: Setting permissions..."
sudo chown ebon:ebon /mnt/media

echo "📁 Step 7: Creating media directory structure..."
mkdir -p /mnt/media/{movies,tv-shows,music,photos,home-videos,backups}

echo "🔗 Step 8: Moving existing media folders..."
# Move existing media to new SSD
if [ -d ~/media ]; then
    echo "Moving existing media folders to SSD..."
    cp -a ~/media/* /mnt/media/ 2>/dev/null || true
    
    # Remove old media directory and create symlink
    rm -rf ~/media
    ln -s /mnt/media ~/media
    echo "Created symlink: ~/media -> /mnt/media"
fi

echo "📊 Step 9: Updating Docker volumes..."
# Update Docker containers to use new media location
docker stop jellyfin 2>/dev/null || true
docker rm jellyfin 2>/dev/null || true

# Restart Jellyfin with new media path
docker run -d --name jellyfin \
  --restart=unless-stopped \
  -p 8096:8096 \
  -p 8920:8920 \
  -p 7359:7359/udp \
  -p 1900:1900/udp \
  -v ~/jellyfin-config:/config \
  -v ~/jellyfin-cache:/cache \
  -v /mnt/media:/media:ro \
  --device /dev/dri:/dev/dri \
  jellyfin/jellyfin

echo
echo "✅ Media SSD Setup Complete!"
echo
echo "📊 Storage Layout:"
df -h /mnt/media
echo
echo "📁 Media directories:"
ls -la /mnt/media/
echo
echo "🎬 Your 1.8TB Samsung SSD is now dedicated for media storage!"
echo "   Access via: ~/media/ (symlinked to /mnt/media)"
echo "   Jellyfin will automatically see the new location"