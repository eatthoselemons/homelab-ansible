## FEATURE:

The goal of this feature is to finish the vyos image builder. The base of the builder is built but there needs to be tests made that actually test that the image builder actually creates an image correctly

note as laid out in the vyos build readme, to build a specific version you need to checkout the 1.4 branch of vyos `sagitta`


## EXAMPLES:

The current vyos setup has quite a few building blocks in `collections/ansible_collections/homelab/nexus/roles/vyos_setup`

The existing vyos build image is in `collections/ansible_collections/homelab/nexus/roles/vyos_image_builder`

## DOCUMENTATION:

You can find the molecule documentation in `references/molecule/docs`

You can find the documentation for the delegated_vm_install in `references/ansible-role-delegated_vm_install`
There is a lot covered in the Readme. Many of what you will need is in the code, however use the github links in the readme if you need more information than what is in the repo

The architecture of the entire homelab is in `docs/llms/design/architecture.md`

You can find docs for configuration of vyos via ansible by following the links to more specific documentation on this page https://docs.ansible.com/ansible/latest/collections/vyos/vyos/index.html

Vyos build readme: https://github.com/vyos/vyos-build

## OTHER CONSIDERATIONS:

The build image should be able to run multiple times without issue
tests should be prefixed and named with whatever their location is ie `nexus.vyos.setup`, `nexus.vyos.security_hardening` or `epyc.harvester.setup`
The dmz will be on `<service>.public.awynn.info` and the internal services will be on `<service>.public.awynn.info`
The llm implementing the project will need to ensure that they actually test the full configuration/setup that they make. A syntax check is not enough to ensure that the deploy works
if the llm cannot run the tests the steps for debugging are:
1. when they cannot run tests is to source the venv before each molecule call, something like `source ~/ansible-venv/bin/activate && molecule test -s <vyos-test>`. The llm should ensure they are in `collections/ansible_collections/homelab/nexus/extenstions/` before running tests using `echo $PWD`
2. if they cannot get tests to run is to stop and let the user know, ask for input to fix the tests

The tests should be able to run from the start, the llm can verify they can run the tests when they start by `cd collections/ansible_collections/homelab/nexus/extensions` then `molecule test -s nexus.vyos.setup`

Note that you cannot just download the vyos image, there will need to be an ansible playbook that builds the vyos image using the docker method as described on this page: https://docs.vyos.io/en/latest/contributing/build-vyos.html, that image will then need to be saved to a folder ignored in the .gitignore that holds the vyos image