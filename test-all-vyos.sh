#!/bin/bash
# Test all VyOS scenarios
export PATH="/home/user/ansible-venv/bin:$PATH"
cd /home/user/IdeaProjects/homelab-ansible
./scripts/testing/run-molecule-test.sh --pattern vyos