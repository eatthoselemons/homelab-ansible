# Ansible Variable Checklist

## Quick Reference for Variable Placement

### Where Variables Go
1. **Role Defaults** → `roles/*/defaults/main.yaml`
2. **Test Overrides** → `molecule/*/group_vars/all.yaml`
3. **Production Values** → `site/group_vars/*.yaml` or `site/host_vars/*.yaml`
4. **Never** → `molecule.yaml` host_vars section

### Variable Naming Rules
- **Always prefix** with role name: `vyos_*`, `nexus_*`, `network_*`
- **Private variables** start with underscore: `_vyos_temp_dir`
- **Document each variable** with a comment above it

### Variable Structure
```yaml
# roles/*/defaults/main.yaml
# Network configuration mode  
# Options: nat, bridge, macvtap
vyos_network_mode: bridge

# molecule/*/group_vars/all.yaml
vyos_network_mode: nat  # Override for testing
```

### Environment Variables
```yaml
# Use lookup for secrets/paths
vyos_iso_path: "{{ lookup('env', 'VYOS_ISO_PATH') | default('/opt/vyos/current.iso') }}"
```

### Quick Validation
- [ ] Variables prefixed with role name?
- [ ] Defaults in `defaults/main.yaml`?
- [ ] Test overrides in `group_vars/all.yaml`?
- [ ] No variables in `molecule.yaml` provisioner?
- [ ] Each variable has a comment?
- [ ] Secrets use environment lookups?