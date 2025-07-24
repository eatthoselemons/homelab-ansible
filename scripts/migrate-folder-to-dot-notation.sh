#!/bin/bash
# Script to migrate a single folder's contents to dot notation
# This allows for controlled, incremental migration

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Base directory
BASE_DIR="/home/user/IdeaProjects/homelab-ansible"
cd "$BASE_DIR"

# Function to display usage
usage() {
    echo "Usage: $0 <target-folder> [--dry-run]"
    echo ""
    echo "Target folders:"
    echo "  nexus-tests    - Migrate nexus molecule tests"
    echo "  nexus-roles    - Migrate nexus roles"
    echo "  epyc-tests     - Migrate epyc molecule tests"
    echo "  epyc-roles     - Migrate epyc roles"
    echo ""
    echo "Options:"
    echo "  --dry-run      - Show what would be changed without making changes"
    echo ""
    echo "Examples:"
    echo "  $0 nexus-tests --dry-run    # Preview nexus test changes"
    echo "  $0 nexus-roles              # Migrate nexus roles"
    exit 1
}

# Check arguments
if [ $# -lt 1 ]; then
    usage
fi

TARGET="$1"
DRY_RUN=false

if [ "${2}" = "--dry-run" ]; then
    DRY_RUN=true
fi

# Function to convert name to dot notation
convert_to_dot_notation() {
    local name="$1"
    echo "$name" | tr '_-' '..'
}

# Function to process a directory
process_directory() {
    local dir="$1"
    local type="$2"  # "role" or "test"
    local changed_count=0
    
    echo -e "${BLUE}Processing $type directory: $dir${NC}"
    
    if [ ! -d "$dir" ]; then
        echo -e "${RED}Directory not found: $dir${NC}"
        return 1
    fi
    
    # Find all directories with underscores or hyphens
    for item in "$dir"/*; do
        if [ -d "$item" ]; then
            basename_item=$(basename "$item")
            if [[ "$basename_item" =~ [_-] ]] && [ "$basename_item" != "default" ]; then
                new_name=$(convert_to_dot_notation "$basename_item")
                
                if [ "$DRY_RUN" = true ]; then
                    echo -e "  ${CYAN}[DRY-RUN]${NC} Would rename: $basename_item → ${GREEN}$new_name${NC}"
                else
                    mv "$item" "$dir/$new_name" 2>/dev/null || echo -e "  ${RED}✗${NC} Failed to rename: $basename_item"
                    if [ $? -eq 0 ]; then
                        echo -e "  ${GREEN}✓${NC} Renamed: $basename_item → $new_name"
                        ((changed_count++))
                    fi
                fi
            fi
        fi
    done
    
    echo -e "  Total ${type}s renamed: ${YELLOW}$changed_count${NC}"
    return 0
}

# Function to update references in a specific scope
update_references() {
    local scope="$1"
    local old_names=()
    local new_names=()
    
    echo -e "\n${BLUE}Updating references for $scope${NC}"
    
    # Build list of what was changed
    case "$scope" in
        "nexus-tests")
            old_names=("nexus_vyos_setup" "nexus_ntp_server" "nexus_vyos_full_integration" "nexus_vyos_image_builder" "nexus_vyos_security_hardening" "nexus_vyos_vlans" "services_vm_setup")
            ;;
        "nexus-roles")
            old_names=("vyos_setup" "vyos_image_builder" "ntp_server" "security_hardening" "system_setup" "network_services" "argocd_setup" "ipxe_server" "services_vm_setup")
            ;;
        "epyc-tests")
            old_names=("epyc_harvester_setup" "harvester_test")
            ;;
        "epyc-roles")
            old_names=("harvester_setup" "harvester_image_builder")
            ;;
    esac
    
    # Convert to new names
    for old in "${old_names[@]}"; do
        new_names+=("$(convert_to_dot_notation "$old")")
    done
    
    # Update references
    local files_updated=0
    for i in "${!old_names[@]}"; do
        old="${old_names[$i]}"
        new="${new_names[$i]}"
        
        # Find files that reference this name
        files=$(find . -type f \( -name "*.yaml" -o -name "*.yml" -o -name "*.md" \) \
            -not -path "./backup-*" \
            -not -path "./.git/*" \
            -not -path "./scripts/*" \
            -exec grep -l "$old" {} \; 2>/dev/null || true)
        
        if [ -n "$files" ]; then
            echo -e "  Updating references: ${RED}$old${NC} → ${GREEN}$new${NC}"
            
            while IFS= read -r file; do
                if [ "$DRY_RUN" = true ]; then
                    echo -e "    ${CYAN}[DRY-RUN]${NC} Would update: $file"
                else
                    # Update various patterns
                    sed -i "s/name: $old\$/name: $new/g" "$file"
                    sed -i "s/name: \"$old\"/name: \"$new\"/g" "$file"
                    sed -i "s/name: '$old'/name: '$new'/g" "$file"
                    sed -i "s/homelab\.nexus\.$old/homelab.nexus.$new/g" "$file"
                    sed -i "s/homelab\.epyc\.$old/homelab.epyc.$new/g" "$file"
                    sed -i "s|roles/$old|roles/$new|g" "$file"
                    sed -i "s/role: $old\$/role: $new/g" "$file"
                    sed -i "s/test $old/test $new/g" "$file"
                    sed -i "s|molecule/$old|molecule/$new|g" "$file"
                    ((files_updated++))
                fi
            done <<< "$files"
        fi
    done
    
    echo -e "  Total files updated: ${YELLOW}$files_updated${NC}"
}

# Main execution
echo -e "${YELLOW}=== Folder-by-Folder Migration Script ===${NC}"
if [ "$DRY_RUN" = true ]; then
    echo -e "${CYAN}Running in DRY-RUN mode - no changes will be made${NC}"
fi
echo ""

case "$TARGET" in
    "nexus-tests")
        process_directory "collections/ansible_collections/homelab/nexus/extensions/molecule" "test"
        update_references "nexus-tests"
        ;;
    "nexus-roles")
        process_directory "collections/ansible_collections/homelab/nexus/roles" "role"
        update_references "nexus-roles"
        ;;
    "epyc-tests")
        process_directory "collections/ansible_collections/homelab/nexus/extensions/molecule" "test"
        update_references "epyc-tests"
        ;;
    "epyc-roles")
        process_directory "collections/ansible_collections/homelab/epyc/roles" "role"
        update_references "epyc-roles"
        ;;
    *)
        echo -e "${RED}Invalid target: $TARGET${NC}"
        usage
        ;;
esac

echo -e "\n${GREEN}=== Migration Complete ===${NC}"
if [ "$DRY_RUN" = true ]; then
    echo "This was a dry run. To apply changes, run without --dry-run"
else
    echo "Changes have been applied successfully!"
fi