#!/bin/bash
trap_msg='s=${?}; echo "${0}: Error on line "${LINENO}": ${BASH_COMMAND}"; exit ${s}'    
set -uo pipefail    
trap "${trap_msg}" ERR    

ansible-galaxy collection install infisical.vault
ansible-galaxy collection install ansibleguy.opnsense
ansible-galaxy collection install community.libvirt
ansible-galaxy role install stafwag.qemu_img
ansible-galaxy role install mrlesmithjr.netplan
