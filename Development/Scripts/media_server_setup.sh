#!/bin/bash
# Media Server Setup for HP Z4 G4 "ebon"
# Jellyfin + PhotoPrism + File organization

echo "🎬 Setting up Media Server on HP Z4 G4"
echo "======================================"

# Create media directory structure
mkdir -p ~/media/{movies,tv-shows,music,photos,home-videos}
mkdir -p ~/media-import/{ripping,processing,completed}

# Install Jellyfin
echo "📺 Installing Jellyfin..."
docker run -d --name jellyfin \
  --restart=unless-stopped \
  -p 8096:8096 \
  -p 8920:8920 \
  -p 7359:7359/udp \
  -p 1900:1900/udp \
  -v ~/jellyfin-config:/config \
  -v ~/jellyfin-cache:/cache \
  -v ~/media:/media:ro \
  --device /dev/dri:/dev/dri \
  jellyfin/jellyfin

# Install PhotoPrism for photos
echo "📸 Installing PhotoPrism..."
docker run -d --name photoprism \
  --restart=unless-stopped \
  -p 2342:2342 \
  -v ~/media/photos:/photoprism/originals:ro \
  -v ~/photoprism-import:/photoprism/import \
  -v ~/photoprism-storage:/photoprism/storage \
  -e PHOTOPRISM_UPLOAD_NSFW="true" \
  -e PHOTOPRISM_ADMIN_PASSWORD="changeme123" \
  photoprism/photoprism

# Install File Browser for easy uploads
echo "📁 Installing File Browser..."
docker run -d --name filebrowser \
  --restart=unless-stopped \
  -p 8083:80 \
  -v ~/media:/srv \
  -v ~/filebrowser.db:/database.db \
  filebrowser/filebrowser

# Install Duplicati for backups
echo "💾 Installing Duplicati for backups..."
docker run -d --name duplicati \
  --restart=unless-stopped \
  -p 8200:8200 \
  -v ~/duplicati-config:/config \
  -v ~/media:/source:ro \
  -v ~/backups:/backups \
  duplicati/duplicati

echo "✅ Media server setup complete!"
echo
echo "🌐 Access your services:"
echo "• Jellyfin (Media): http://10.0.0.29:8096"
echo "• PhotoPrism (Photos): http://10.0.0.29:2342"
echo "• File Browser (Upload): http://10.0.0.29:8083"
echo "• Duplicati (Backup): http://10.0.0.29:8200"
echo
echo "📁 Media folders created at:"
echo "• ~/media/movies"
echo "• ~/media/tv-shows" 
echo "• ~/media/music"
echo "• ~/media/photos"
echo "• ~/media/home-videos"