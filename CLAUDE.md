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
- **Never create a file longer than 500 lines of code.** If a file approaches this limit, refactor by splitting it into modules or helper files.
- **Organize code into clearly separated modules**, grouped by feature or responsibility.
- **Use clear, consistent imports** (prefer relative imports within packages).

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
- **Use YAML anchors and aliases** to reduce duplication
- **Implement proper error handling** with `failed_when` and `ignore_errors`
- **Use Infisical for sensitive data** Infisical for runtime secrets
- **Follow collection namespace conventions**: `homelab.nexus.role_name`
- **Test all roles with molecule** before deployment
- **Use meaningful task names** that describe the action
- **Implement idempotency** - tasks should be safe to run multiple times

### 🏗️ Code Structure & Modularity
- **Roles**: Single-purpose, reusable components in collection
- **Variables**: Use `defaults/main.yml` for overridable defaults, `vars/main.yml` for constants
- **Templates**: Jinja2 templates in `templates/` directory
- **Handlers**: Service restarts and notifications in `handlers/main.yml`
- **Testing**: Molecule scenarios for each role with proper isolation
- **Avoid bash scripts**: use structured Ansible configuration blocks
- **Newlines**: always have newlines at the end of files

### 🧪 Testing with Molecule
- **Use the test.sh script**: `./test.sh` handles environment setup, virtual environment, and directory navigation automatically
- **List All Tests**: `./test.sh list` or just `./test.sh`
- **Run full test**: `./test.sh test <test-name>` (e.g., `./test.sh test nexus.vyos.setup`)
- **Syntax check only**: `./test.sh syntax <test-name>`
- **Converge (setup test environment)**: `./test.sh converge <test-name>`
- **Verify tests**: `./test.sh verify <test-name>`
- **Destroy test environment**: `./test.sh destroy <test-name>`
- **Environment variables**: Copy `.env.example` to `.env` and fill in any required secrets for testing
- **Manual execution**: If needed, use full paths: `/home/user/ansible-venv/bin/molecule` from `collections/ansible_collections/homelab/nexus/extensions/`
- **Similar To Prod**: all tests should be as similar as possible to deploying on prod

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

### Bash Notes
- **Always check `pwd`** if you get file/directory not found errors
- **Use Ripgrep** always use ripgrep instead of grep (rg)
