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

You can find docs for configuration of vyos via ansible by following the links to more specific documentation on this page https://docs.ansible.com/ansible/latest/collections/vyos/vyos/index.html

There are security best practices for vyos in `docs/llms/exmaples/best-practices.md`

## OTHER CONSIDERATIONS:

The vyos-setup should be able to run multiple times without issue
tests should be prefixed and named with whatever their location is ie `nexus.vyos.setup`, `nexus.vyos.security_hardening` or `epyc.harvester.setup`
You might need to move some files around to fit the new format
The dmz will be on `<service>.public.awynn.info` and the internal services will be on `<service>.public.awynn.info`
The llm implementing the project will need to ensure that they actually test the full configuration/setup that they make. A syntax check is not enough to ensure that the deploy works
First step when they cannot run tests is to source the venv before each molecule call, something like `source ~/ansible-venv/bin/activate && molecule test -s <vyos-test>`. The llm should ensure they are in `collections/ansible_collections/homelab/nexus/extenstions/` before running tests using `echo $PWD`
Second step if they cannot get tests to run is to stop and let the user know, ask for input to fix the tests
the llm will be able to test first thing before making changes that the tests run. The tests complete with errors right now and the goal of these changes is to finish implementing them and then get the tests working so that we can ensure that a full deploy onto physical hardware will go smoothly and work the first time

Note that you cannot just download the vyos image, there will need to be an ansible playbook that builds the vyos image using the docker method as described on this page: https://docs.vyos.io/en/latest/contributing/build-vyos.html, that image will then need to be saved to a folder ignored in the .gitignore that holds the vyos image. Then you can use that image to create the vyos vm for running libvirt. We need to use the "delegated_vm_install" but the image to use is the vyos image created following the instructions from vyos on the provided page. Use the docker container method

make sure to include a desired folder structure in your resulting PRP
