## FEATURE:

The goal of this feature is to fix the vyos setup and testing. This will be a three step process:

1. Fix the setup of the vyos vm to use the stafwag/ansible-role-delegated_vm_install ansible role correctly
- This fixes the current issue where the vm doesn't have an actual os, since the os never boots you can never do any other commands or start vyos
2. The vyos-setup needs to be adjusted to follow security best practices for vyos'
- much of this should already be setup in `homelab/nexus/roles/vyos_setup/defaults/main.yaml`
3. The setup needs to be tested, the tests should be done in molecule with as close to a fully simulated environment as possible to ensure that when it is deployed to prod it goes smoothly

## EXAMPLES:

The current vyos setup has quite a few building blocks in `collections/ansible_collections/homelab/nexus/roles/vyos_setup`

## DOCUMENTATION:

You can find the molecule documentation in `references/molecule/docs`

You can find the documentation for the delegated_vm_install in `references/ansible-role-delegated_vm_install`
There is a lot covered in the Readme. Many of what you will need is in the code, however use the github links in the readme if you need more information than what is in the repo

The architecture of the entire homelab is in `docs/llms/design/architecture.md`

## OTHER CONSIDERATIONS:

The vyos-setup should be able to run multiple times without issue
tests should be prefixed and named with whatever their location is ie `nexus.vyos.setup`, `nexus.vyos.security_hardening` or `epyc.harvester.setup`
You might need to move some files around to fit the new format
