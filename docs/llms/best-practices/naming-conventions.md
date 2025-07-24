# Naming Conventions

## Overview
This document defines the naming conventions used throughout the homelab-ansible project to ensure consistency and maintainability.

## File Extensions
- **General Rule**: Always use `.yaml` extension for all YAML files
- **Exception**: Molecule framework files must use `.yml` extension
  - `molecule.yml`
  - `converge.yml`
  - `verify.yml`
  - `requirements.yml` (in Molecule directories)

## Role Naming
- **Format**: Use dot notation (e.g., `vyos.setup`, `ntp.server`)
- **No underscores or hyphens** in role names
- **Examples**:
  - ✅ `nexus.vyos.setup`
  - ✅ `epyc.harvester.setup`
  - ❌ `vyos_setup`
  - ❌ `vyos-setup`

## Variable Naming
- **Always prefix** with the main component name
- **Format**: `<component>_<description>` (e.g., `vyos_network_mode`)
- **Use the primary component name** from the role (e.g., for `vyos.setup` use `vyos_*`)
- **Private variables** start with underscore: `_vyos_temp_dir`
- **Document each variable** with a comment above it
- **Examples**:
  - Role `vyos.setup`:
    - ✅ `vyos_iso_path`
    - ✅ `vyos_network_mode`
  - Role `harvester.setup`:
    - ✅ `harvester_cluster_size`
    - ✅ `harvester_node_count`
  - Role `ntp.server`:
    - ✅ `ntp_timezone`
    - ✅ `ntp_pools`
  - ❌ `network_mode` (missing prefix)
  - ❌ `vyos-iso-path` (using hyphens)

## Variable Placement
- **Role Defaults** → `roles/*/defaults/main.yaml`
- **Test Overrides** → `molecule/*/group_vars/all.yaml`
- **Production Values** → `site/group_vars/*.yaml` or `site/host_vars/*.yaml`
- **Never** → `molecule.yaml` host_vars section (use group_vars instead)

## Variable Structure Example
```yaml
# roles/*/defaults/main.yaml
# Network configuration mode  
# Options: nat, bridge, macvtap
vyos_network_mode: bridge

# molecule/*/group_vars/all.yaml
vyos_network_mode: nat  # Override for testing
```

## Environment Variables
```yaml
# Use lookup for secrets/paths
vyos_iso_path: "{{ lookup('env', 'VYOS_ISO_PATH') | default('/opt/vyos/current.iso') }}"
```

## Test Naming (Molecule)
- **Format**: Use dot notation matching the role being tested
- **Pattern**: `<collection>.<role>` (e.g., `nexus.vyos.setup`)
- **Examples**:
  - ✅ `nexus.vyos.setup`
  - ✅ `epyc.harvester.setup`
  - ❌ `vyos-setup-test`
  - ❌ `test_vyos_setup`

## Task Names
- **Use clear, descriptive names** starting with a capital letter
- **Format**: Action-oriented description of what the task does
- **Examples**:
  - ✅ `Create VyOS configuration directory`
  - ✅ `Install required packages`
  - ❌ `vyos config` (too vague)
  - ❌ `create-directory` (wrong format)

## File and Directory Structure
- **Collections**: `collections/ansible_collections/homelab/<host>/`
- **Roles**: `collections/ansible_collections/homelab/<host>/roles/<role.name>/`
- **Tests**: `collections/ansible_collections/homelab/nexus/extensions/molecule/<test.name>/`
- **Use lowercase** for all directory names

## Template Files
- **Extension**: `.j2` for Jinja2 templates
- **Naming**: Match the target file name with `.j2` extension
- **Examples**:
  - ✅ `config.yaml.j2`
  - ✅ `vyos.conf.j2`
  - ❌ `config-template.j2` (unnecessary suffix)

## Handler Names
- **Format**: Service action description
- **Examples**:
  - ✅ `restart ntp service`
  - ✅ `reload vyos configuration`
  - ❌ `ntp-restart` (wrong format)

## Playbook Names
- **Use descriptive names** with hyphens for word separation
- **Extension**: Always `.yaml`, never `.yml`
- **Examples**:
  - ✅ `setup-nexus.yaml`
  - ✅ `deploy-services.yaml`
  - ❌ `setup_nexus.yaml` (use hyphens)
  - ❌ `setup.yml` (wrong extension)

## Quick Reference Checklist

### Naming Conventions
- [ ] All YAML files use `.yaml` extension (except Molecule files)
- [ ] Roles use dot notation (e.g., `vyos.setup`)
- [ ] Variables prefixed with component name using underscores
- [ ] Test names match role names with dots
- [ ] Task names are descriptive and start with capital letter
- [ ] Templates end with `.j2`
- [ ] Playbooks use hyphens for word separation

### Variable Validation
- [ ] Variables prefixed with component name?
- [ ] Defaults in `defaults/main.yaml`?
- [ ] Test overrides in `group_vars/all.yaml`?
- [ ] No variables in `molecule.yaml` provisioner?
- [ ] Each variable has a comment?
- [ ] Secrets use environment lookups?