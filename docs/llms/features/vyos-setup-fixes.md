## FEATURE:

The goal of this feature is to fix the vyos setup and testing. There are a list of small things that need to be fixed:

2. Use the image now created via the "vyos_build_image" role to fix vyos setup tests to use an actual image instead of skipping the parts where you verify that vyos is setup
3. have the vyos setup and tests pull the password and ssh keys from "Infisical"
4. There should be different subnets for each of the vlans so 10.<vlan>.0.0/16. Example is 10.60.0.0/16 for vlan 60
5. The network and such need to be set to use `awynn.info`
- dmz vlan (10) is `public.awynn.info`
- secure vlan (50) is `private.awynn.info`
- management vlan (60) is `management.awynn.info`
- logging vlan (70) is `logs.awynn.info`
6. add a molecule test for the vlans `nexus.vyos.vlans`
7. Ensure tests still work and test steps are not being skipped
8. Ensure that tests are idempotent


## EXAMPLES:

The current vyos setup has quite a few building blocks in `collections/ansible_collections/homelab/nexus/roles/vyos_setup`

You can see how to pull secrets from Infisical by checking the `server-inventory.yaml`

## DOCUMENTATION:

You can find the molecule documentation in `references/molecule/docs`

You can find ehe documentation for the delegated_vm_install in `references/ansible-role-delegated_vm_install`
There is a lot covered in the Readme. Many of what you will need is in the code, however use the github links in the readme if you need more information than what is in the repo

The other stafwag repos we use documentation: (they are also in the `references/ansible-role-delegated_vm_install/README.md`)
* **stafwag.libvirt**:
  [https://github.com/stafwag/ansible-role-libvirt](https://github.com/stafwag/ansible-role-libvirt)
* **stafwag.qemu_img**:
  [https://github.com/stafwag/ansible-role-qemu_img](https://github.com/stafwag/ansible-role-qemu_img)
* **stafwag.cloud_localds**:
  [https://github.com/stafwag/ansible-role-cloud_localds](https://github.com/stafwag/ansible-role-cloud_localds)
* **stafwag.virt_install_import**:
  [https://github.com/stafwag/ansible-role-virt_install_import](https://github.com/stafwag/ansible-role-virt_install_import)

The architecture of the entire homelab is in `docs/llms/design/architecture.md`

You can find docs for configuration of vyos via ansible by following the links to more specific documentation on this page https://docs.ansible.com/ansible/latest/collections/vyos/vyos/index.html

There are security best practices for vyos in `docs/llms/exmaples/best-practices.md`

## OTHER CONSIDERATIONS:

Infisical variable names are:
- `lizWorkstationPublicSshKey` (the machine ansible is running on now)
- `nexusAnsiblePublicSshKey`
- `nexusAnsiblePrivateSshKey`
- `systemSudoPassword`
- `vyosPrivateSshKey`
- `vyosPublicSshKey`

all tests and roles should be impotent
tests should be prefixed and named with whatever their location is ie `nexus.vyos.setup`, `nexus.vyos.security_hardening` or `epyc.harvester.setup`
You might need to move some files around to fit the new format
The dmz will be on `<service>.public.awynn.info` and the internal services will be on `<service>.public.awynn.info`
The llm implementing the project will need to ensure that they actually test the full configuration/setup that they make. A syntax check is not enough to ensure that the deploy works
First step when they cannot run tests is to source the venv before each molecule call, something like `source ~/ansible-venv/bin/activate && molecule test -s <vyos-test>`. The llm should ensure they are in `collections/ansible_collections/homelab/nexus/extenstions/` before running tests using `echo $PWD`
Second step if they cannot get tests to run is to stop and let the user know, ask for input to fix the tests
the llm will be able to test first thing before making changes that the tests run. The tests complete with errors right now and the goal of these changes is to finish implementing them and then get the tests working so that we can ensure that a full deploy onto physical hardware will go smoothly and work the first time

There are scripts to run that do the build process, you should use them to verify that your tests will work they are in `scripts/testing/`

make sure to include a desired folder structure in your resulting PRP
