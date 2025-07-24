## FEATURE:

The goal of this feature is to setup the ansible to deploy authentik to a container in harvester. One in the dmz and one in the secure vlan. Then there is 

## EXAMPLES:

The current vyos setup has quite a few building blocks in `collections/ansible_collections/homelab/nexus/roles/vyos_setup`

You can see how to pull secrets from Infisical by checking the `server-inventory.yaml`

## DOCUMENTATION:

You can find the molecule documentation in `references/molecule/docs`

The architecture of the entire homelab is in `docs/llms/design/architecture.md`

You can see the authentik best practices at `docs/llms/best-practices/authentik.md`

## OTHER CONSIDERATIONS:

all tests and roles should be impotent
tests should be prefixed and named with whatever their location is ie `nexus.vyos.setup`, `nexus.vyos.security_hardening` or `epyc.harvester.setup`

There are scripts to run that do the build process, you should use them to verify that your tests will work they are in `scripts/testing/`

make sure to include a desired folder structure in your resulting PRP
