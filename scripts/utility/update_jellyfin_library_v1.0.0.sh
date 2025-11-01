#!/bin/bash

echo "=== Updating Jellyfin Music Library ==="

# First, check if the organized music is accessible from container
echo "Checking if music_organized is accessible in container..."
sudo docker exec jellyfin ls -la /mnt/media/music_organized 2>/dev/null | head -5

if [ $? -ne 0 ]; then
    echo "Need to restart Jellyfin with proper mount..."
    
    # Stop current container
    sudo docker stop jellyfin
    
    # Get current container config
    JELLYFIN_IMAGE=$(sudo docker inspect jellyfin --format='{{.Config.Image}}')
    
    # Start with updated mount including music_organized
    sudo docker run -d \
        --name jellyfin \
        --rm \
        -p 8096:8096 \
        -p 8920:8920 \
        -p 1900:1900/udp \
        -p 7359:7359/udp \
        -v /home/ebon/jellyfin-config:/config \
        -v /home/ebon/jellyfin-cache:/cache \
        -v /mnt/media:/mnt/media:ro \
        --restart unless-stopped \
        $JELLYFIN_IMAGE
    
    echo "Jellyfin restarted with proper mounts"
    sleep 10
fi

# Now trigger library scan via API
echo "Triggering library scan..."

# Get library info
curl -X GET "http://localhost:8096/Library/VirtualFolders" \
    -H "Accept: application/json" 2>/dev/null | python3 -m json.tool

echo ""
echo "To complete setup:"
echo "1. Access Jellyfin at http://10.0.0.29:8096"
echo "2. Go to Dashboard -> Libraries"
echo "3. Edit your Music library"
echo "4. Change path from /mnt/media/music to /mnt/media/music_organized"
echo "5. Click 'Scan Library'"
echo ""
echo "Or add a new Music library pointing to /mnt/media/music_organized"
