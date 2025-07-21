name: "VyOS Image Builder Testing Implementation"
description: |

## Purpose
Complete the VyOS image builder implementation by adding comprehensive tests that verify the image building process actually creates a valid, bootable VyOS ISO image. This ensures the automated infrastructure deployment has a reliable router image creation process.

## Core Principles
1. **Context is Complete but Focused**: Include ALL necessary documentation sections, specific examples, and discovered caveats
2. **Validation Loops**: Provide executable tests/lints the AI can run and fix
3. **Information Dense**: Use keywords and patterns from the codebase
4. **Progressive Success**: Start simple, validate, then enhance
5. **Global rules**: Be sure to follow all rules in CLAUDE.md

---

## Goal
Finish the VyOS image builder by creating molecule tests that validate the image building process actually creates a valid VyOS ISO. The existing role has the build logic but lacks proper testing to ensure the built image is functional.

## Why
- **Reliability**: Automated infrastructure requires a working router image
- **CI/CD Integration**: Tests enable continuous validation of image builds
- **Version Control**: Tests ensure specific VyOS versions (1.4/sagitta) build correctly
- **Idempotency**: Verify the build process can run multiple times without issues

## What
Create comprehensive molecule tests for the `vyos_image_builder` role that:
- Verify Docker-based build process completes successfully
- Validate the output ISO exists and has correct properties
- Ensure idempotency (can run multiple times)
- Test with actual VyOS 1.4 (sagitta) branch
- Follow existing test naming patterns: `nexus.vyos.image_builder`

### Success Criteria
- [ ] Molecule test scenario `nexus.vyos.image_builder` passes completely
- [ ] ISO file is created in the correct location with proper size
- [ ] Build process is idempotent (second run detects existing image)
- [ ] Tests can run in CI/CD environment
- [ ] Image location is properly gitignored

## All Needed Context

### Documentation & References
```yaml
# MUST READ - Include these specific sections in your context window

- url: https://docs.vyos.io/en/latest/contributing/build-vyos.html
  sections: ["Native Build", "Docker Build"]
  why: Official build documentation with Docker commands
  discovered_caveat: Must use vyos/vyos-build:sagitta image for 1.4 builds
  
- url: https://github.com/vyos/vyos-build
  sections: ["README", "Branch Information"]
  why: Shows branch mapping - sagitta = 1.4 LTS
  gotcha: Default branch is 'current', must checkout 'sagitta' for 1.4
  
- file: collections/ansible_collections/homelab/nexus/roles/vyos_image_builder/tasks/main.yaml
  why: Existing implementation to test
  gotcha: Uses docker_container module which may need privileged mode in tests
  
- file: collections/ansible_collections/homelab/nexus/extensions/molecule/nexus.vyos.setup/molecule.yaml
  why: Reference test pattern for VyOS-related tests
  critical: Shows Docker driver config with privileged mode and /dev/kvm access
  
- doc: references/molecule/docs
  section: ["Testing with Docker", "Verifiers"]
  critical: Tests must handle Docker-in-Docker for image building

- docfile: CLAUDE.md
  include_sections: ["Testing with Molecule", "Repository Structure"]
  skip_sections: ["Commit Guidelines"]
```

### Current Codebase Structure
```bash
collections/ansible_collections/homelab/nexus/
├── roles/
│   ├── vyos_image_builder/
│   │   ├── defaults/main.yaml         # Has vyos_images_dir: "../images/vyos"
│   │   ├── handlers/main.yaml         # Cleanup handler
│   │   ├── tasks/main.yaml           # Build logic to test
│   │   └── README.md
│   └── vyos_setup/
│       └── tasks/main.yaml          # Includes vyos_image_builder role
└── extensions/
    └── molecule/
        ├── nexus.vyos.setup/        # Reference test pattern
        └── [other test scenarios]
```

### Desired Codebase Structure with New Files
```bash
collections/ansible_collections/homelab/nexus/
├── roles/
│   └── vyos_image_builder/          # Existing role to test
└── extensions/
    └── molecule/
        └── nexus.vyos.image_builder/  # NEW test scenario
            ├── molecule.yaml            # Test configuration
            ├── converge.yaml           # Run the role
            ├── verify.yaml             # Validate ISO creation
            └── requirements.yaml       # Galaxy dependencies
```

### Known Gotchas & Library Quirks
```yaml
# CRITICAL: Docker-in-Docker requires privileged mode
# CRITICAL: VyOS build needs ~10GB disk space
# CRITICAL: Build process takes 20-30 minutes first time
# CRITICAL: Must use 'sagitta' branch for VyOS 1.4
# CRITICAL: ISO location must be in .gitignore
# GOTCHA: docker_container module needs reset_connection after group changes
# GOTCHA: Built ISO name pattern varies, use find module to locate
```

## Implementation Blueprint

### Task List (in order)

```yaml
Task 1: Add images directory to .gitignore
MODIFY .gitignore:
  - ADD line: "images/"
  - ADD line: "*.iso"
  - REASON: Prevent large ISO files from being committed

Task 2: Create molecule test directory structure
CREATE collections/ansible_collections/homelab/nexus/extensions/molecule/nexus.vyos.image_builder/:
  - MIRROR structure from: nexus.vyos.setup test scenario
  - KEEP naming pattern consistent

Task 3: Create molecule.yaml configuration
CREATE molecule.yaml:
  - USE Docker driver with privileged mode
  - MOUNT /var/run/docker.sock for Docker-in-Docker
  - SET longer timeout for build process (45 minutes)
  - CONFIGURE test-specific variables

Task 4: Create converge.yaml to run the role
CREATE converge.yaml:
  - INCLUDE vyos_image_builder role
  - SET test-specific paths for ISO storage
  - OVERRIDE vyos_version to 'sagitta' for 1.4

Task 5: Create comprehensive verify.yaml
CREATE verify.yaml:
  - CHECK Docker is running
  - VERIFY ISO file exists and size > 400MB
  - VALIDATE ISO is bootable format
  - TEST idempotency markers

Task 6: Create requirements.yaml for dependencies
CREATE requirements.yaml:
  - INCLUDE community.docker collection
  - ADD any other required collections

Task 7: Update role to handle test environment
MODIFY vyos_image_builder/tasks/main.yaml if needed:
  - ENSURE paths work in test container
  - ADD conditional logic for test mode if required
```

### Integration Points
```yaml
STORAGE:
  - images_dir: Create in test container at /tmp/vyos-images
  - gitignore: Add images/ and *.iso patterns
  
DOCKER:
  - mount: /var/run/docker.sock:/var/run/docker.sock
  - privileges: --privileged flag required
  
NETWORK:
  - github: Access to clone vyos-build repo
  - dockerhub: Pull vyos/vyos-build:sagitta image
```

## Validation Loop

### Level 1: Syntax Check
```bash
# Navigate to test directory
cd collections/ansible_collections/homelab/nexus/extensions/
source ~/ansible-venv/bin/activate

# Check syntax
molecule syntax -s nexus.vyos.image_builder

# Expected: No errors
```

### Level 2: Test Execution
```bash
# Run the full test scenario
molecule test -s nexus.vyos.image_builder

# For debugging, run steps individually:
molecule create -s nexus.vyos.image_builder
molecule converge -s nexus.vyos.image_builder
molecule verify -s nexus.vyos.image_builder
```

### Level 3: Verify ISO Creation
```python
# In verify.yaml, test cases should include:

- name: Check ISO exists
  stat:
    path: "/tmp/vyos-images/vyos-sagitta.iso"
  register: iso_file
  
- name: Verify ISO is valid size
  assert:
    that:
      - iso_file.stat.exists
      - iso_file.stat.size > 400000000  # 400MB minimum
    fail_msg: "VyOS ISO not created or too small"

- name: Verify ISO is bootable format
  command: file /tmp/vyos-images/vyos-sagitta.iso
  register: iso_type
  failed_when: "'boot' not in iso_type.stdout"

- name: Test idempotency - second run
  include_role:
    name: vyos_image_builder
  vars:
    vyos_images_dir: /tmp/vyos-images
    
- name: Verify no duplicate build
  find:
    paths: /tmp/vyos-images
    patterns: "vyos-*.iso"
  register: iso_count
  failed_when: iso_count.files | length > 1
```

## Final Validation Checklist
- [ ] Test runs successfully: `molecule test -s nexus.vyos.image_builder`
- [ ] ISO file created with size > 400MB
- [ ] Second run detects existing image (idempotent)
- [ ] Build uses sagitta branch for VyOS 1.4
- [ ] Images directory is gitignored
- [ ] Test can run in CI/CD environment
- [ ] Cleanup works properly after test

## Anti-Patterns to Avoid
- ❌ Don't skip the actual Docker build in tests
- ❌ Don't use pre-built test ISOs - test the actual build
- ❌ Don't hardcode paths - use variables
- ❌ Don't ignore disk space requirements
- ❌ Don't timeout too quickly - builds take time
- ❌ Don't forget to cleanup large ISO files after tests

## Confidence Score: 8/10

The PRP provides comprehensive context for implementing VyOS image builder tests. Points deducted for:
- Build time complexity (20-30 min) may require CI/CD adjustments
- Docker-in-Docker can have environment-specific issues

The AI agent has all necessary context to implement working tests that validate the VyOS image building process.