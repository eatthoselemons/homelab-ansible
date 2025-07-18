# Infisical Setup Guide

This guide walks you through setting up Infisical for secret management in the homelab-ansible project.

## Overview

Infisical is used to securely manage secrets like passwords, SSH keys, and API tokens. The project uses Infisical's Universal Auth (machine identity) for automated secret retrieval during Ansible playbook execution.

## Prerequisites

- An Infisical account (free tier works fine)
- The `infisical.vault` Ansible collection (installed via requirements.yml)

## Setup Steps

### 1. Create an Infisical Account

1. Go to [https://infisical.com](https://infisical.com) and sign up
2. Create a new project for your homelab

### 2. Create Required Secrets

In your Infisical project, create the following secrets in the root path (`/`) of the `prod` environment:

| Secret Name | Description | Example Value |
|------------|-------------|---------------|
| `systemSudoPassword` | Admin password for VyOS and other systems | `SecurePass123!` |
| `nexusAnsiblePublicSshKey` | SSH public key for Ansible automation | `ssh-rsa AAAAB3...` |
| `nexusAnsiblePrivateSshKey` | SSH private key for Ansible automation | `-----BEGIN RSA PRIVATE KEY-----...` |

**Important**: 
- Store the complete SSH keys including headers
- Use strong passwords (min 12 characters, mixed case, numbers, symbols)
- Keep the private key secure and never commit it to git

### 3. Set Up Universal Auth (Machine Identity)

1. In your Infisical project, go to **Project Settings** → **Machine Identities**
2. Click **Create machine identity**
3. Give it a name like `homelab-ansible`
4. Set the access level to **Read** for the `prod` environment
5. Copy the **Client ID** and **Client Secret** - you'll need these

### 4. Configure Environment Variables

Create a `.env` file in the project root (copy from `.env.example`):

```bash
cp .env.example .env
```

Update the `.env` file with your Infisical credentials:

```bash
# Infisical Configuration
INFISICAL_CLIENT_ID=your_client_id_here
INFISICAL_CLIENT_SECRET=your_client_secret_here
INFISICAL_PROJECT_ID=your_project_id_here
INFISICAL_ENVIRONMENT=prod
INFISICAL_URL=https://app.infisical.com  # Optional, defaults to Infisical cloud

# Legacy variable (not used in current code)
# INFISICAL_TOKEN=deprecated_do_not_use
```

**Finding your Project ID**: 
- Go to your project in Infisical
- Click on **Project Settings**
- Copy the **Project ID**

### 5. Export Environment Variables

The `test.sh` script automatically loads the `.env` file, so for testing you just need to:

```bash
# Run tests - .env will be loaded automatically
./test.sh test nexus.vyos.setup
```

For running Ansible playbooks directly, export the variables:

```bash
# Load from .env file
export $(grep -v '^#' .env | xargs)

# Or manually export
export INFISICAL_CLIENT_ID="your_client_id"
export INFISICAL_CLIENT_SECRET="your_client_secret"
export INFISICAL_PROJECT_ID="your_project_id"
```

## Verifying Your Setup

### Test Secret Retrieval

Run this Ansible ad-hoc command to verify Infisical is working:

```bash
ansible localhost -m debug -a "msg={{ lookup('infisical.vault.read_secrets', 
  universal_auth_client_id=lookup('env', 'INFISICAL_CLIENT_ID'),
  universal_auth_client_secret=lookup('env', 'INFISICAL_CLIENT_SECRET'),
  project_id=lookup('env', 'INFISICAL_PROJECT_ID'),
  path='/',
  env_slug='prod',
  secret_name='systemSudoPassword'
) }}"
```

### Run Tests

```bash
# Ensure environment variables are set
./test.sh test nexus.vyos.setup
```

## Troubleshooting

### "Failed to retrieve secrets from Infisical"

This error means Ansible couldn't connect to Infisical. Check:

1. **Environment variables are set**: Run `env | grep INFISICAL` to verify
2. **Client ID/Secret are correct**: Double-check in Infisical dashboard
3. **Project ID is correct**: Verify in Project Settings
4. **Machine identity has access**: Check it has read access to `prod` environment
5. **Secrets exist**: Ensure all required secrets are created in Infisical

### "INFISICAL_PROJECT_ID environment variable must be set"

Export the environment variable:
```bash
export INFISICAL_PROJECT_ID="your_project_id"
```

### "Authentication failed"

Your Client ID or Client Secret is incorrect. Regenerate them in Infisical if needed.

### Missing infisical.vault collection

Install the required Ansible collections:
```bash
ansible-galaxy collection install -r collections/ansible_collections/homelab/nexus/requirements.yml
```

## Security Best Practices

1. **Never commit secrets**: Keep `.env` in `.gitignore`
2. **Use strong passwords**: Follow password complexity requirements
3. **Rotate credentials regularly**: Update machine identity credentials periodically
4. **Limit access**: Give machine identities only the minimum required permissions
5. **Use different environments**: Consider using `dev`, `staging`, and `prod` environments in Infisical

## Additional Resources

- [Infisical Documentation](https://infisical.com/docs)
- [Infisical Ansible Collection](https://github.com/Infisical/ansible-collection)
- [Universal Auth Guide](https://infisical.com/docs/documentation/platform/identities/universal-auth)