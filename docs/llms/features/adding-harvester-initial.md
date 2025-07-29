## FEATURE:

The goal of this feature is to do initial setup of harvester
At the end of this feature harvester should be ready to create vms like the trueNas vm, and containers like authentik. It should not create those vms and containers just be ready to set those up
Harvester should be able to support PCIe passthrough for the gpu to the gpu services and the storage pcie to truenas
Ensure that harvester can use terraform for deploying the containers
add a timeserver to the services vm in the nexus to follow harvester best practices

## EXAMPLES:

The current vyos setup has quite a few building blocks in `collections/ansible_collections/homelab/nexus/roles/vyos_setup`

You can see how to pull secrets from Infisical by checking the `server-inventory.yaml`

## DOCUMENTATION:

You can find the molecule documentation in `references/molecule/docs`

The architecture of the entire homelab is in `docs/llms/design/architecture.md`

The harvester docs are in `references/harvester-docs/docs`

there is a harvester best practices at `docs/llms/best-practices/harvester-setup-best-practices.md`

## OTHER CONSIDERATIONS:

all tests and roles should be impotent
tests should be prefixed and named with whatever their location is ie `nexus.vyos.setup`, `nexus.vyos.security_hardening` or `epyc.harvester.setup`

use the `test.sh` to run molecule tests

make sure to include a desired folder structure in your resulting PRP

The epyc server has 6 nics

harvester will be deployed on epyc server, mid server, and one of the hp thin clients

truenas has its own hba

always use `.yaml` file extensions like the yaml faq recommends
