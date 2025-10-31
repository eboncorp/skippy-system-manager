#!/bin/bash
# Rename all files throughout key directories to lowercase with underscores

total_renamed=0

# Function to rename files in a directory
rename_files_in_dir() {
    local dir="$1"
    local depth="${2:-999}"  # Default to deep search
    local count=0

    echo "Processing: $dir"

    find "$dir" -maxdepth "$depth" -type f 2>/dev/null | while read -r file; do
        filename=$(basename "$file")
        dirpath=$(dirname "$file")

        # Convert to lowercase and replace spaces with underscores
        newname=$(echo "$filename" | tr '[:upper:]' '[:lower:]' | sed 's/ /_/g')

        if [ "$filename" != "$newname" ]; then
            mv "$dirpath/$filename" "$dirpath/$newname" 2>/dev/null
            if [ $? -eq 0 ]; then
                echo "  ✓ $filename → $newname"
                ((count++))
            fi
        fi
    done

    return $count
}

# Rename files in key directories
echo "=== Renaming Files in Key Directories ==="
echo ""

# Scripts directory
rename_files_in_dir "/home/dave/scripts" 999

# Documents (depth 2 to avoid too many)
rename_files_in_dir "/home/dave/Documents" 2

# Desktop
rename_files_in_dir "/home/dave/Desktop" 1

# Downloads
rename_files_in_dir "/home/dave/Downloads" 2

# Music
rename_files_in_dir "/home/dave/Music" 2

# scans
rename_files_in_dir "/home/dave/scans" 999

# scanned_documents
rename_files_in_dir "/home/dave/scanned_documents" 2

# skippy subdirectories
rename_files_in_dir "/home/dave/skippy/claude" 999
rename_files_in_dir "/home/dave/skippy/documentation" 999
rename_files_in_dir "/home/dave/skippy/development" 999

echo ""
echo "=== File Renaming Complete ==="
