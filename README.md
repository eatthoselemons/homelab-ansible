# Homelab Ansible

Ansible collection for managing homelab infrastructure including VyOS routers, services, and server configurations.

## Documentation

### For Developers
- **[Variable Organization Guide](docs/humans/variable-organization-explained.md)** - Understanding how variables work in Ansible
- **[Task Management](docs/humans/tasks/)** - How to track work and create PR descriptions
- **[Naming Conventions](docs/llms/best-practices/naming-conventions.md)** - Project naming standards and conventions

## Setup Router
### Put in Infisical

You then need to put the `key` and `secret` into infisical, to do that follow this documentation for adding the keys to a new project (infisical documentation)[https://infisical.com/docs/documentation/platform/project]

Once you add the secrets to infisical then you need to get a client machine setup you can follow this documentation to get the client id and secret created (infisical documentation)[https://infisical.com/docs/documentation/platform/identities/universal-auth]

### Get Keys From Infisical Onto Machine

Clone this repo and then you need to edit `router/default.yaml` to have the infisical `client-id`. Then you need to run `export INFISICAL_CLIENT_SECRET=<infiscal-client-secret>`


### Running Setup

You then need to run `bootstrap-system.sh $HOME` as `sudo` which will install the various dependencies and the python venv where ansible is installed.

Once that finishes you need to run `source ~/ansible-venv/bin/activate` to enter the python venv and you can then push the changes to the router with `ansible-playbook -u user router/default.yaml`

### Running Tests

For comprehensive testing documentation, see [VyOS Testing Guide](docs/testing/vyos-testing.md).

Quick test commands:
```bash
# Verify VyOS image
./scripts/testing/verify-vyos-image.sh

# Run full test suite
export ANSIBLE_BECOME_PASSWORD='your_sudo_password'
./scripts/testing/test-vyos-end-to-end.sh

# Run with options (skip build, show help, etc.)
./scripts/testing/test-vyos-end-to-end.sh --help
```

### Done

Then Opnsense should be setup!

