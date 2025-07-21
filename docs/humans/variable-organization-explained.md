# Understanding Ansible Variable Organization

## Variable Types and Where They Live

### 1. **Role Defaults** (`roles/*/defaults/main.yaml`)
- **Purpose**: Provide sensible default values that users can override
- **Example**: `vyos_vm_memory: 4096`
- **When to use**: For any variable that users might want to customize
- **Key point**: This is the RIGHT place for most role variables!

### 2. **Role Variables** (`roles/*/vars/main.yaml`)
- **Purpose**: Role constants that should NOT be overridden
- **Example**: Internal role variables like `_vyos_temp_dir: /tmp/vyos`
- **When to use**: Rarely - only for true constants

### 3. **Test Variables** (`molecule/*/group_vars/all.yaml`)
- **Purpose**: Override defaults specifically for testing
- **Example**: `vyos_test_mode: true`
- **When to use**: Test-specific values that differ from production

### 4. **Production Variables** (`site/group_vars/`, `site/host_vars/`)
- **Purpose**: Production environment settings
- **Example**: `vyos_vm_memory: 8192` (override default for production)
- **When to use**: Production deployments

## How Variables Flow (Precedence Order)

```
defaults/main.yaml (Role Defaults)
    ↓
group_vars/all.yaml (Environment/Test Overrides)  
    ↓
host_vars/hostname.yaml (Host-Specific Overrides)
    ↓
Playbook vars (Runtime Overrides)
```

## Why This Structure?

1. **Flexibility**: Users can override at any level
2. **Clarity**: Clear separation between defaults, test values, and production values
3. **Maintainability**: Changes at one level don't affect others
4. **Standard Practice**: Follows Ansible community conventions

## Common Confusion Points

### "Should I move variables out of defaults/main.yaml?"
**No!** Role defaults belong in `defaults/main.yaml`. What moves to `group_vars` are:
- Test-specific overrides (for Molecule tests)
- Production-specific overrides (for actual deployments)

### "What about molecule.yaml host_vars?"
While Molecule supports defining variables in `molecule.yaml`, it's better to use `group_vars/all.yaml` because:
- It's the standard Ansible way
- Keeps molecule.yaml focused on infrastructure
- Makes variables easier to find and maintain

## Example in Practice

```yaml
# roles/vyos_setup/defaults/main.yaml
vyos_vm_memory: 4096  # Sensible default for most users

# molecule/nexus.vyos.setup/group_vars/all.yaml
vyos_vm_memory: 2048  # Smaller for testing

# site/group_vars/routers.yaml
vyos_vm_memory: 8192  # Larger for production routers
```

Each level serves its purpose without conflicting with the others!