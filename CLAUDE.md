### 🎯 Top Priority Rules
1. **Always run full tests** - Use `./test.sh test <name>`, never just syntax checks
2. **Never hardcode secrets** - Prefer Infisical for secrets
3. **Follow variable checklist** - Check variables comply with `docs/llms/best-practices/variable-checklist.md`
4. **Update TASK.md as you work** - Track progress with ✅, 🔄, ⏳ indicators
5. **Test changes with molecule** - Verify all modifications work correctly

### 🔄 Project Awareness & Context
- **Always read `docs/llm/design/architecture.md`** at the start of a new conversation to understand the project's architecture, goals, style, and constraints.
- **Task Management with `TASK.md`**:
  - Check if `TASK.md` exists before starting work
  - If working on a multi-step task, create/update `TASK.md` with:
    - Task name and date started
    - List of subtasks to complete
    - Progress indicators (✅ completed, 🔄 in progress, ⏳ pending)
  - Update task status as you work
  - Add a "Discovered During Work" section for new issues found
- **Use consistent naming conventions, file structure, and architecture patterns** as described in `PLANNING.md`.

### 🧱 Code Structure & Modularity
- **Never create a file longer than 500 lines of code** - Refactor into modules or helper files
- **Organize code into clearly separated modules** - Group by feature or responsibility
- **Roles**: Single-purpose, reusable components in collection
- **Variables**: Use `defaults/main.yml` for overridable defaults, `vars/main.yml` for constants
- **Templates**: Jinja2 templates in `templates/` directory
- **Handlers**: Service restarts and notifications in `handlers/main.yml`
- **Avoid bash scripts**: Use structured Ansible configuration blocks
- **Newlines**: Always have newlines at the end of files

### 🧪 Testing & Reliability
- **Always create molecule unit tests for new features** (functions, classes, routes, etc).
- **After updating any logic**, check whether existing unit tests need to be updated. If so, do it.
- **Run FULL tests, not just syntax checks** - When verifying that tests work, always run the complete test suite using `./test.sh test <test-name>`. Time is not an issue; the preference is that tests fully work.
- **Test verification priority**: Full functionality over speed. Always run complete test cycles to ensure proper validation.

### ✅ Task Completion
- **Update `TASK.md` immediately** when completing tasks (mark with ✅)
- **Document discovered issues** in the "Discovered During Work" section
- **Include what was changed** in a brief summary for each completed task

### 📚 Documentation & Explainability
- **Update `README.md`** when new features are added, dependencies change, or setup steps are modified.
- **Comment non-obvious code** and ensure everything confusing to a mid-level developer is commented
- When writing complex logic, **add an inline `# Reason:` comment** explaining the why, not just the what.

### 🧠 AI Behavior Rules
- **Never assume missing context. Ask questions if uncertain.**
- **Never hallucinate libraries or functions** – only use known, verified ansible packages.
- **Always confirm file paths and module names** exist before referencing them in code or tests.
- **Never delete or overwrite existing code** unless explicitly instructed to or if part of a task from `TASK.md`.

### 📋 Ansible Best Practices
- **Always follow the variable checklist** at `docs/llms/best-practices/variable-checklist.md` when creating or modifying variables
- **Use YAML anchors and aliases** to reduce duplication
- **Implement proper error handling** with `failed_when` and `ignore_errors`
- **Use Infisical for sensitive data** Infisical for runtime secrets
- **Follow collection namespace conventions**: `homelab.nexus.role_name`
- **Test all roles with molecule** before deployment
- **Use meaningful task names** that describe the action
- **Implement idempotency** - tasks should be safe to run multiple times


### 🧪 Testing with Molecule
- **Always use test.sh**: `./test.sh test <name>` for full tests (handles environment setup automatically)
- **Available commands**: list, test, syntax, converge, verify, destroy
- **Environment setup**: Copy `.env.example` to `.env` for secrets
- **Priority**: Full tests over speed - always run complete test cycles
- **Production similarity**: Tests should mirror production deployment as closely as possible

### 🔒 Security & Secrets
- **Never hardcode sensitive values** in playbooks or roles
- **Use Infisical for dynamic secret retrieval** during playbook execution
- **Use Security Best Practices**: Ensure that best practices in `docs/examples/best-practices.md` are followed for every change
- **Use `become: yes` carefully** - consider security implications

### 📁 Repository Structure
- **Ansible Galaxy Collection**: `collections/ansible_collections/homelab/` - collection for all hardware
- **Hosts**: `collections/ansible_collections/homelab/<host>` - where every individual host deployment lives, ie nexus, epyc-server
- **Site**: `site/` - ansible for deploying to prod - ie physical hardware
- **Testing**: `collections/ansible_collections/homelab/nexus/extensions/molecule/` - testing scenarios for all roles
- **Architecture**: `docs/design/ai-prompt.md` has the entire system architecture 

### ⚠️ Common Gotchas to Avoid
- **Path issues**: Use environment variables or Ansible lookups instead of complex relative paths like `../../../`. For paths within the project, use `{{ playbook_dir }}`, `{{ role_path }}`, or `{{ inventory_dir }}`
- **Variable precedence**: Remember that host_vars override group_vars which override defaults
- **Module namespace**: Use `homelab.nexus.role_name`, not relative paths in include_role
- **File permissions**: Set appropriate modes (0644 for configs, 0755 for scripts)
- **YAML formatting**: Ensure proper indentation and always add newlines at end of files

### Bash Notes
- **Always check `pwd`** if you get file/directory not found errors
- **Use Ripgrep** always use ripgrep instead of grep (rg)
