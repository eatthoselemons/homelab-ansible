#!/bin/bash
# Test all VyOS scenarios
export PATH="/home/user/ansible-venv/bin:$PATH"
cd /home/user/IdeaProjects/homelab-ansible
./test-collection.sh --pattern vyos