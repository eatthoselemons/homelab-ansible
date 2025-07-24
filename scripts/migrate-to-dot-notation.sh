#!/bin/bash
# Script to migrate all role and test names from underscore/hyphen to dot notation
# This ensures consistency across the entire codebase

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

# Parse command line arguments
DRY_RUN=false
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run|--check|-n)
            DRY_RUN=true
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --dry-run, --check, -n    Show what would be changed without making changes"
            echo "  --verbose, -v             Show detailed output"
            echo "  --help, -h                Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0 --dry-run            # Check what would be changed"
            echo "  $0                      # Apply the changes"
            echo "  $0 --dry-run --verbose  # See detailed check output"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Backup directory
BACKUP_DIR="$BASE_DIR/backup-before-dot-notation-$(date +%Y%m%d-%H%M%S)"

echo -e "${YELLOW}=== Ansible Role and Test Name Migration Script ===${NC}"
if [ "$DRY_RUN" = true ]; then
    echo -e "${CYAN}Running in DRY-RUN mode - no changes will be made${NC}"
else
    echo "This script will convert all role and test names to dot notation"
fi
echo ""

# Function to convert name to dot notation
convert_to_dot_notation() {
    local name="$1"
    # Replace both underscores and hyphens with dots
    echo "$name" | tr '_-' '..'
}

# Arrays to track what needs to be changed
declare -a ROLES_TO_RENAME=()
declare -a TESTS_TO_RENAME=()
declare -A ROLE_MAPPINGS=()
declare -A TEST_MAPPINGS=()

# Function to scan for items to rename
scan_for_renames() {
    echo -e "${YELLOW}Scanning for items to rename...${NC}\n"
    
    # Scan roles
    echo -e "${BLUE}Roles:${NC}"
    for collection in nexus epyc; do
        role_dir="collections/ansible_collections/homelab/$collection/roles"
        if [ -d "$role_dir" ]; then
            [ "$VERBOSE" = true ] && echo -e "${CYAN}  Collection: $collection${NC}"
            for role_path in "$role_dir"/*; do
                if [ -d "$role_path" ]; then
                    role_name=$(basename "$role_path")
                    if [[ "$role_name" =~ [_-] ]]; then
                        new_name=$(convert_to_dot_notation "$role_name")
                        ROLES_TO_RENAME+=("$collection|$role_name|$new_name")
                        ROLE_MAPPINGS["$role_name"]="$new_name"
                        echo -e "  ${RED}✗${NC} $collection/$role_name → ${GREEN}$new_name${NC}"
                    elif [ "$VERBOSE" = true ]; then
                        echo -e "  ${GREEN}✓${NC} $collection/$role_name"
                    fi
                fi
            done
        fi
    done
    
    # Scan molecule tests
    echo -e "\n${BLUE}Molecule Tests:${NC}"
    test_dir="collections/ansible_collections/homelab/nexus/extensions/molecule"
    if [ -d "$test_dir" ]; then
        for test_path in "$test_dir"/*; do
            if [ -d "$test_path" ]; then
                test_name=$(basename "$test_path")
                if [[ "$test_name" =~ [_-] ]] && [ "$test_name" != "default" ]; then
                    new_name=$(convert_to_dot_notation "$test_name")
                    TESTS_TO_RENAME+=("$test_name|$new_name")
                    TEST_MAPPINGS["$test_name"]="$new_name"
                    echo -e "  ${RED}✗${NC} $test_name → ${GREEN}$new_name${NC}"
                elif [ "$VERBOSE" = true ]; then
                    echo -e "  ${GREEN}✓${NC} $test_name"
                fi
            fi
        done
    fi
}

# Function to find references that need updating
find_references() {
    echo -e "\n${BLUE}References to update:${NC}"
    
    local total_refs=0
    
    # Check each role mapping
    for old_name in "${!ROLE_MAPPINGS[@]}"; do
        local count=$(find . -type f \( -name "*.yaml" -o -name "*.yml" -o -name "*.md" -o -name "*.py" -o -name "*.sh" \) \
            -not -path "./backup-*" \
            -not -path "./.git/*" \
            -not -path "./scripts/migrate-to-dot-notation.sh" \
            -exec grep -l "$old_name" {} \; 2>/dev/null | wc -l)
        
        if [ "$count" -gt 0 ]; then
            echo -e "  Found ${YELLOW}$count${NC} files with references to '${RED}$old_name${NC}' → '${GREEN}${ROLE_MAPPINGS[$old_name]}${NC}'"
            ((total_refs+=count))
            
            if [ "$VERBOSE" = true ]; then
                find . -type f \( -name "*.yaml" -o -name "*.yml" -o -name "*.md" -o -name "*.py" -o -name "*.sh" \) \
                    -not -path "./backup-*" \
                    -not -path "./.git/*" \
                    -not -path "./scripts/migrate-to-dot-notation.sh" \
                    -exec grep -l "$old_name" {} \; 2>/dev/null | head -5 | while read -r file; do
                    echo "    - $file"
                done
            fi
        fi
    done
    
    # Check each test mapping
    for old_name in "${!TEST_MAPPINGS[@]}"; do
        local count=$(find . -type f \( -name "*.yaml" -o -name "*.yml" -o -name "*.md" -o -name "*.sh" \) \
            -not -path "./backup-*" \
            -not -path "./.git/*" \
            -not -path "./scripts/migrate-to-dot-notation.sh" \
            -exec grep -l "test $old_name" {} \; 2>/dev/null | wc -l)
        
        if [ "$count" -gt 0 ]; then
            echo -e "  Found ${YELLOW}$count${NC} files with test references to '${RED}$old_name${NC}' → '${GREEN}${TEST_MAPPINGS[$old_name]}${NC}'"
            ((total_refs+=count))
        fi
    done
    
    echo -e "\n  Total files to update: ${YELLOW}$total_refs${NC}"
}

# Function to create backup
create_backup() {
    if [ "$DRY_RUN" = true ]; then
        echo -e "\n${CYAN}[DRY-RUN] Would create backup at: $BACKUP_DIR${NC}"
        return
    fi
    
    echo -e "\n${GREEN}Creating backup at: $BACKUP_DIR${NC}"
    mkdir -p "$BACKUP_DIR"
    cp -r collections "$BACKUP_DIR/" 2>/dev/null || true
    cp -r docs "$BACKUP_DIR/" 2>/dev/null || true
    cp -r site "$BACKUP_DIR/" 2>/dev/null || true
    echo "Backup created successfully"
}

# Function to rename directories
rename_directories() {
    echo -e "\n${YELLOW}Step 1: Renaming directories...${NC}"
    
    # Rename roles
    for rename_info in "${ROLES_TO_RENAME[@]}"; do
        IFS='|' read -r collection old_name new_name <<< "$rename_info"
        old_path="collections/ansible_collections/homelab/$collection/roles/$old_name"
        new_path="collections/ansible_collections/homelab/$collection/roles/$new_name"
        
        if [ "$DRY_RUN" = true ]; then
            echo -e "${CYAN}[DRY-RUN]${NC} Would rename: $old_path → $new_path"
        else
            if [ -d "$old_path" ]; then
                mv "$old_path" "$new_path"
                echo -e "${GREEN}✓${NC} Renamed: $collection/$old_name → $new_name"
            fi
        fi
    done
    
    # Rename tests
    for rename_info in "${TESTS_TO_RENAME[@]}"; do
        IFS='|' read -r old_name new_name <<< "$rename_info"
        old_path="collections/ansible_collections/homelab/nexus/extensions/molecule/$old_name"
        new_path="collections/ansible_collections/homelab/nexus/extensions/molecule/$new_name"
        
        if [ "$DRY_RUN" = true ]; then
            echo -e "${CYAN}[DRY-RUN]${NC} Would rename: $old_path → $new_path"
        else
            if [ -d "$old_path" ]; then
                mv "$old_path" "$new_path"
                echo -e "${GREEN}✓${NC} Renamed test: $old_name → $new_name"
            fi
        fi
    done
}

# Function to update references in files
update_references() {
    echo -e "\n${YELLOW}Step 2: Updating references in files...${NC}"
    
    local files_updated=0
    
    # Find all relevant files
    find . -type f \( -name "*.yaml" -o -name "*.yml" -o -name "*.md" -o -name "*.py" -o -name "*.sh" \) \
        -not -path "./backup-*" \
        -not -path "./.git/*" \
        -not -path "./scripts/migrate-to-dot-notation.sh" | while read -r file; do
        
        # Create temporary file
        temp_file=$(mktemp)
        changed=false
        
        # Copy original file to temp
        cp "$file" "$temp_file"
        
        # Update role references
        for old_name in "${!ROLE_MAPPINGS[@]}"; do
            new_name="${ROLE_MAPPINGS[$old_name]}"
            
            # Various patterns to replace
            patterns=(
                "s/name: $old_name\$/name: $new_name/g"
                "s/name: \"$old_name\"/name: \"$new_name\"/g"
                "s/name: '$old_name'/name: '$new_name'/g"
                "s/homelab\.nexus\.$old_name/homelab.nexus.$new_name/g"
                "s/homelab\.epyc\.$old_name/homelab.epyc.$new_name/g"
                "s|roles/$old_name|roles/$new_name|g"
                "s/role: $old_name\$/role: $new_name/g"
                "s/include_role:.*$old_name/include_role: name: $new_name/g"
            )
            
            for pattern in "${patterns[@]}"; do
                if grep -q "${pattern%%/g}" "$temp_file" 2>/dev/null; then
                    sed -i "$pattern" "$temp_file"
                    changed=true
                fi
            done
        done
        
        # Update test references
        for old_name in "${!TEST_MAPPINGS[@]}"; do
            new_name="${TEST_MAPPINGS[$old_name]}"
            
            # Update test.sh commands and paths
            sed -i "s/test $old_name/test $new_name/g" "$temp_file"
            sed -i "s|molecule/$old_name|molecule/$new_name|g" "$temp_file"
            
            if grep -q "$old_name" "$temp_file" 2>/dev/null; then
                changed=true
            fi
        done
        
        # If file was changed, handle it
        if [ "$changed" = true ]; then
            if [ "$DRY_RUN" = true ]; then
                echo -e "${CYAN}[DRY-RUN]${NC} Would update: $file"
                [ "$VERBOSE" = true ] && diff -u "$file" "$temp_file" | head -20
            else
                cp "$temp_file" "$file"
                echo -e "${GREEN}✓${NC} Updated: $file"
                ((files_updated++))
            fi
        fi
        
        # Clean up temp file
        rm "$temp_file"
    done
    
    if [ "$DRY_RUN" = false ]; then
        echo -e "\n  Total files updated: ${GREEN}$files_updated${NC}"
    fi
}

# Main execution
echo -e "${YELLOW}Starting analysis...${NC}\n"

# Check if we're in the right directory
if [ ! -d "collections/ansible_collections/homelab" ]; then
    echo -e "${RED}Error: Must run from the homelab-ansible root directory${NC}"
    exit 1
fi

# Scan for what needs to be changed
scan_for_renames

# Show statistics
echo -e "\n${YELLOW}Summary:${NC}"
echo -e "  Roles to rename: ${YELLOW}${#ROLES_TO_RENAME[@]}${NC}"
echo -e "  Tests to rename: ${YELLOW}${#TESTS_TO_RENAME[@]}${NC}"

# Find references
find_references

# If dry run, show next steps and exit
if [ "$DRY_RUN" = true ]; then
    echo -e "\n${CYAN}This was a dry run. No changes were made.${NC}"
    echo -e "\nTo apply these changes, run:"
    echo -e "  ${GREEN}$0${NC}"
    echo -e "\nThe script will create a backup before making changes."
    exit 0
fi

# If no changes needed
if [ ${#ROLES_TO_RENAME[@]} -eq 0 ] && [ ${#TESTS_TO_RENAME[@]} -eq 0 ]; then
    echo -e "\n${GREEN}Everything already follows dot notation! No changes needed.${NC}"
    exit 0
fi

# Ask for confirmation
echo -e "\n${YELLOW}Ready to apply changes${NC}"
read -p "Do you want to proceed? A backup will be created first. [y/N]: " -n 1 -r
echo

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 0
fi

# Execute migration
create_backup
rename_directories
update_references

echo -e "\n${GREEN}=== Migration Complete ===${NC}"
echo "Backup saved at: $BACKUP_DIR"
echo ""
echo "To test a migrated role:"
echo "  ./test.sh test nexus.vyos.setup"
echo ""
echo "If you need to rollback:"
echo "  rm -rf collections docs site"
echo "  cp -r $BACKUP_DIR/* ."