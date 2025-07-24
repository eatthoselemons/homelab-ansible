#!/bin/bash
# Script to check current naming conventions and show what would be changed

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Base directory
BASE_DIR="/home/user/IdeaProjects/homelab-ansible"
cd "$BASE_DIR"

echo -e "${YELLOW}=== Naming Convention Check ===${NC}"
echo "This script shows what needs to be renamed to follow dot notation"
echo ""

# Function to check roles
check_roles() {
    echo -e "${BLUE}Checking Roles:${NC}"
    
    for collection in nexus epyc; do
        role_dir="collections/ansible_collections/homelab/$collection/roles"
        if [ -d "$role_dir" ]; then
            echo -e "\n${YELLOW}Collection: $collection${NC}"
            for role in "$role_dir"/*; do
                if [ -d "$role" ]; then
                    role_name=$(basename "$role")
                    if [[ "$role_name" == *"_"* ]]; then
                        new_name=$(echo "$role_name" | tr '_' '.')
                        echo -e "  ${RED}✗${NC} $role_name → ${GREEN}$new_name${NC}"
                    else
                        echo -e "  ${GREEN}✓${NC} $role_name"
                    fi
                fi
            done
        fi
    done
}

# Function to check tests
check_tests() {
    echo -e "\n${BLUE}Checking Molecule Tests:${NC}"
    
    test_dir="collections/ansible_collections/homelab/nexus/extensions/molecule"
    if [ -d "$test_dir" ]; then
        for test in "$test_dir"/*; do
            if [ -d "$test" ]; then
                test_name=$(basename "$test")
                if [[ "$test_name" == *"_"* ]] || [[ "$test_name" == *"-"* ]]; then
                    new_name=$(echo "$test_name" | tr '_-' '..')
                    echo -e "  ${RED}✗${NC} $test_name → ${GREEN}$new_name${NC}"
                else
                    echo -e "  ${GREEN}✓${NC} $test_name"
                fi
            fi
        done
    fi
}

# Function to find references
find_references() {
    echo -e "\n${BLUE}Checking for references that would need updating:${NC}"
    
    # Common patterns to check
    patterns=(
        "vyos_setup"
        "vyos_image_builder"
        "harvester_setup"
        "harvester_image_builder"
        "ntp_server"
        "services_vm_setup"
        "security_hardening"
        "system_setup"
        "network_services"
        "ipxe_server"
        "argocd_setup"
    )
    
    for pattern in "${patterns[@]}"; do
        count=$(find . -type f \( -name "*.yaml" -o -name "*.yml" -o -name "*.md" \) \
            -not -path "./backup-*" \
            -not -path "./.git/*" \
            -exec grep -l "$pattern" {} \; 2>/dev/null | wc -l)
        
        if [ "$count" -gt 0 ]; then
            new_name=$(echo "$pattern" | tr '_' '.')
            echo -e "  Found ${RED}$count${NC} references to '$pattern' that would change to '${GREEN}$new_name${NC}'"
        fi
    done
}

# Main execution
check_roles
check_tests
find_references

echo -e "\n${YELLOW}Summary:${NC}"
echo "Run ./scripts/migrate-to-dot-notation.sh to apply these changes"
echo "The script will create a backup before making any changes"