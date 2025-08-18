# Symlink to the actual vagrant module
# This makes the vagrant module available to Ansible
import sys
import os

# Add the molecule_plugins path to Python's module search path
module_path = '/home/user/ansible-venv/lib/python3.13/site-packages/molecule_plugins/vagrant/modules'
if module_path not in sys.path:
    sys.path.insert(0, module_path)

# Now import the actual vagrant module
from vagrant import *