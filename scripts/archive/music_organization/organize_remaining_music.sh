#!/bin/bash

# Move converted MP3s back to main directory for organization
echo "Moving converted MP3 files from rejects to main music directory..."

# Count files before
BEFORE=$(find /mnt/media/music -maxdepth 1 -type f \( -name '*.mp3' -o -name '*.m4a' \) | wc -l)
echo "Files in main directory before: $BEFORE"

# Move all MP3 files from rejects to main music directory
find /mnt/media/music/rejects -name '*.mp3' -type f -exec mv {} /mnt/media/music/ \; 2>/dev/null

# Count files after
AFTER=$(find /mnt/media/music -maxdepth 1 -type f \( -name '*.mp3' -o -name '*.m4a' \) | wc -l)
echo "Files in main directory after: $AFTER"
echo "Files moved: $((AFTER - BEFORE))"

# Now restart the organizer to process these files
echo "Restarting music organizer for remaining files..."
# Clear the previous state to process new files
mv /home/ebon/music_org_state.json /home/ebon/music_org_state_batch1.json 2>/dev/null
mv /home/ebon/music_org_summary.json /home/ebon/music_org_summary_batch1.json 2>/dev/null

# Start the organizer again
python3 /home/ebon/robust_music_organizer.py
