#!/bin/bash

# Script to update all .yml references to .yaml
echo "Updating all .yml references to .yaml..."

# Find all files (excluding binary files and .git) and update .yml references
find . -type f \
    -not -path "./.git/*" \
    -not -path "./ansible-venv/*" \
    -not -path "./.idea/*" \
    -not -name "*.pyc" \
    -not -name "*.so" \
    -not -name "*.exe" \
    -not -name "*.jar" \
    -not -name "*.zip" \
    -not -name "*.tar" \
    -not -name "*.gz" \
    -not -name "*.png" \
    -not -name "*.jpg" \
    -not -name "*.jpeg" \
    -not -name "*.gif" \
    -not -name "*.ico" \
    -exec grep -l "\.yml\b" {} \; 2>/dev/null | while read -r file; do
    echo "Updating: $file"
    # Use sed to replace .yml with .yaml
    # The \b ensures we only match .yml at word boundaries
    sed -i 's/\.yml\b/.yaml/g' "$file"
done

echo "Completed updating .yml references to .yaml"