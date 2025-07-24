# Universal Testing Strategy for Homelab Infrastructure

## Overview

This document defines the UNIVERSAL testing strategy that applies to ALL components in the homelab architecture:
- VyOS router configuration
- Harvester cluster deployment
- TrueNAS storage integration
- ArgoCD GitOps setup
- Infisical secrets management
- iPXE network boot
- Rancher container orchestration
- All future components

This strategy addresses common LLM testing anti-patterns and ensures comprehensive test coverage across the entire infrastructure.

## Core Principles

1. **No Separate Smoke Tests** - All tests run through the same path
2. **Progressive Validation** - Fast failures for quick feedback
3. **Full Tests by Default** - No shortcuts that LLMs can abuse
4. **Clear Completion Markers** - Obvious indicators when tests fully complete

## Anti-Patterns to Avoid

### ❌ DO NOT Create These:

```bash
# Separate test levels that LLMs will abuse
./test.sh test role-name --smoke     # LLMs will only run this
./test.sh test role-name --quick     # LLMs will prefer this
./test.sh test role-name --validate  # LLMs will stop here
```

### ❌ DO NOT Structure Tests Like This:

```yaml
# Bad: Optional stages that can be skipped
when: test_stage == 'full' or run_all_tests
```

## Correct Testing Pattern

### ✅ Single Test Path with Built-in Phases

All tests MUST follow this structure in `converge.yml`:

```yaml
---
- name: Converge
  hosts: all
  gather_facts: yes
  become: yes
  
  tasks:
    # PHASE 1: Syntax and Variable Validation (30 seconds)
    # Always runs - catches configuration errors early
    - name: "PHASE 1/4: Syntax and Variable Validation"
      block:
        - name: Validate required variables
          assert:
            that:
              - required_var is defined
              - required_var.property is defined
            fail_msg: "❌ VALIDATION FAILED - Missing required variable"
            
        - name: Validate variable formats
          assert:
            that:
              - item.ip | ansible.utils.ipaddr
            fail_msg: "❌ Invalid IP address format"
          loop: "{{ node_list }}"
      tags: [always]
    
    # PHASE 2: Dependency Validation (1 minute)
    # Always runs - ensures environment is ready
    - name: "PHASE 2/4: Dependency Validation"
      block:
        - name: Check required tools
          command: "which {{ item }}"
          loop: "{{ required_tools }}"
          changed_when: false
          
        - name: Verify Python modules
          pip:
            name: "{{ required_python_modules }}"
            state: present
          check_mode: yes
      tags: [always]
      
    # PHASE 3: Configuration Generation (2 minutes)
    # Always runs - validates templates and logic
    - name: "PHASE 3/4: Configuration Generation and Validation"
      block:
        - name: Generate configurations
          include_role:
            name: "{{ role_under_test }}"
            tasks_from: generate_configs
          vars:
            dry_run: true
            
        - name: Validate generated configurations
          include_tasks: validate_configs.yaml
      tags: [always]
      
    # PHASE 4: Full Deployment Test (5-45 minutes)
    # Always runs - this is the actual test
    - name: "PHASE 4/4: Full Deployment Test"
      block:
        - name: Run complete role
          include_role:
            name: "{{ role_under_test }}"
            
        - name: Verify deployment success
          include_tasks: verify_deployment.yaml
          
        - name: Mark test as complete
          copy:
            content: |
              ✅ FULL TEST COMPLETED SUCCESSFULLY
              Time: {{ ansible_date_time.iso8601 }}
              All 4 phases passed
            dest: /tmp/test-complete.marker
      tags: [always]
    
    # FINAL: Display results
    - name: Test Summary
      debug:
        msg: |
          ✅ ALL TESTS PASSED
          Phase 1: Validation     ✓
          Phase 2: Dependencies   ✓
          Phase 3: Configuration  ✓
          Phase 4: Deployment     ✓
          
          This confirms the role will work in production.
```

## Image Building and Caching

### Build Strategy

1. **Base Images**: Built once, cached for reuse
2. **Test Instances**: Always use fresh linked clones
3. **CI/CD**: Fresh VMs naturally force rebuilds

### Implementation

```yaml
# In tasks that use images
- name: Check for cached base images
  stat:
    path: "{{ image_path }}"
  register: image_exists

- name: Build if needed
  include_role:
    name: image_builder
  when: not image_exists.stat.exists or force_rebuild|default(false)

- name: Create test instance
  command: >
    qemu-img create -f qcow2 -F qcow2
    -b {{ base_image }}
    {{ test_instance }}
```

### Cache Behavior

| Environment | Cache Status | Build Time | Behavior |
|------------|--------------|------------|----------|
| CI/CD (fresh VM) | Empty | 45 min | Full build from ISO |
| Developer machine | Populated | 5 min | Uses cached images |
| Force rebuild | Ignored | 45 min | Rebuilds everything |

## Instructions for LLMs

### IMPORTANT RULES FOR AI ASSISTANTS:

1. **ALWAYS use the standard test command**:
   ```bash
   ./test.sh test <role-name>
   ```

2. **NEVER create shortcuts**:
   - No `--quick` or `--smoke` flags
   - No separate validation-only tests
   - No "fast" test alternatives

3. **ALWAYS wait for completion marker**:
   - Look for "✅ FULL TEST COMPLETED SUCCESSFULLY"
   - All 4 phases must complete
   - Partial completion = test failed

4. **When tests fail**:
   - Run the SAME command again after fixes
   - Do NOT create a "simpler" test
   - Do NOT skip to later phases

5. **Test duration expectations**:
   - First run: ~45 minutes (builds images)
   - Subsequent: ~5-10 minutes (uses cache)
   - This is NORMAL and REQUIRED

## Example: Correct LLM Response

```markdown
I'll test the harvester_setup role:

$ ./test.sh test epyc-harvester-setup

PHASE 1/4: Syntax and Variable Validation... ✓
PHASE 2/4: Dependency Validation... ✓  
PHASE 3/4: Configuration Generation... ✓
PHASE 4/4: Full Deployment Test... ✓

✅ FULL TEST COMPLETED SUCCESSFULLY

All phases passed. The role is ready for production deployment.
```

## Example: Incorrect LLM Response

```markdown
❌ "I'll create a quick test to validate the syntax..."
❌ "Running smoke test to save time..."
❌ "The validation passed, so the feature works!"
❌ "I'll skip the full deployment to test faster..."
```

## Enforcement

To ensure compliance:

1. **Single test entrypoint** - No alternative commands
2. **Sequential phases** - Can't skip ahead
3. **Clear failure messages** - Explain what wasn't tested
4. **Completion markers** - Obvious when fully done

## Component-Specific Examples

### VyOS Router
```yaml
Phase 1: Validate VLAN configs, IP ranges
Phase 2: Check vyos-tools, SSH access
Phase 3: Generate firewall rules, verify syntax
Phase 4: Deploy to VyOS VM, test routing
```

### TrueNAS Storage
```yaml
Phase 1: Validate pool configs, share definitions
Phase 2: Check TrueNAS API access, zfs tools
Phase 3: Generate dataset configs, validate quotas
Phase 4: Create pools, test NFS/SMB access
```

### ArgoCD GitOps
```yaml
Phase 1: Validate repo URLs, app definitions
Phase 2: Check kubectl, helm, git access
Phase 3: Generate manifests, lint YAML
Phase 4: Deploy apps, verify sync status
```

## Summary

- **Universal approach**: Same pattern for ALL components
- **One test path**: `./test.sh test <name>`
- **Four mandatory phases**: All must pass
- **No shortcuts**: Full test or nothing
- **Clear markers**: Know when testing is complete
- **Cache friendly**: Fast for developers, fresh for CI

This strategy ensures:
1. LLMs cannot take shortcuts while still providing fast feedback
2. Consistent testing across all infrastructure components
3. Confidence that what works in test will work in production