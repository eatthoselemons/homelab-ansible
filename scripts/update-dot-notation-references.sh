#!/bin/bash
# Script to update all references to use dot notation

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

cd /home/user/IdeaProjects/homelab-ansible

echo -e "${YELLOW}=== Updating References to Dot Notation ===${NC}"

# Define all the replacements needed
declare -A replacements=(
    # Nexus roles
    ["vyos_setup"]="vyos.setup"
    ["vyos_image_builder"]="vyos.image.builder"
    ["ntp_server"]="ntp.server"
    ["security_hardening"]="security.hardening"
    ["system_setup"]="system.setup"
    ["network_services"]="network.services"
    ["argocd_setup"]="argocd.setup"
    ["ipxe_server"]="ipxe.server"
    ["services_vm_setup"]="services.vm.setup"
    
    # Epyc roles
    ["harvester_setup"]="harvester.setup"
    ["harvester_image_builder"]="harvester.image.builder"
    
    # Test names
    ["nexus_vyos_setup"]="nexus.vyos.setup"
    ["nexus_ntp_server"]="nexus.ntp.server"
    ["nexus_vyos_full_integration"]="nexus.vyos.full.integration"
    ["nexus_vyos_image_builder"]="nexus.vyos.image.builder"
    ["nexus_vyos_security_hardening"]="nexus.vyos.security.hardening"
    ["nexus_vyos_vlans"]="nexus.vyos.vlans"
    ["services_vm_setup"]="services.vm.setup"
    ["epyc_harvester_setup"]="epyc.harvester.setup"
    ["harvester_test"]="harvester.test"
)

# Update files
total_updates=0
for old_name in "${!replacements[@]}"; do
    new_name="${replacements[$old_name]}"
    echo -e "\n${BLUE}Updating: $old_name → $new_name${NC}"
    
    # Find and update files
    files=$(find . -type f \( -name "*.yaml" -o -name "*.yml" -o -name "*.md" -o -name "*.sh" \) \
        -not -path "./backup-*" \
        -not -path "./.git/*" \
        -not -path "./scripts/update-dot-notation-references.sh" \
        -exec grep -l "$old_name" {} \; 2>/dev/null || true)
    
    if [ -n "$files" ]; then
        count=0
        while IFS= read -r file; do
            # Multiple sed patterns to catch different contexts
            sed -i "s/name: $old_name\$/name: $new_name/g" "$file"
            sed -i "s/name: \"$old_name\"/name: \"$new_name\"/g" "$file"
            sed -i "s/name: '$old_name'/name: '$new_name'/g" "$file"
            sed -i "s/homelab\.nexus\.$old_name/homelab.nexus.$new_name/g" "$file"
            sed -i "s/homelab\.epyc\.$old_name/homelab.epyc.$new_name/g" "$file"
            sed -i "s|roles/$old_name|roles/$new_name|g" "$file"
            sed -i "s/role: $old_name\$/role: $new_name/g" "$file"
            sed -i "s/test $old_name/test $new_name/g" "$file"
            sed -i "s|molecule/$old_name|molecule/$new_name|g" "$file"
            sed -i "s/${old_name}_/${new_name}_/g" "$file" # Variables like harvester_setup_complete
            ((count++))
        done <<< "$files"
        echo "  Updated $count files"
        ((total_updates+=count))
    else
        echo "  No files to update"
    fi
done

echo -e "\n${GREEN}=== Reference Update Complete ===${NC}"
echo "Total files updated: $total_updates"
echo ""
echo "Next steps:"
echo "1. Review changes with: git diff"
echo "2. Run tests to verify everything works"
echo "3. Commit the changes"