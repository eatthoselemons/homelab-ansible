#!/bin/bash
trap_msg='s=${?}; echo "${0}: Error on line "${LINENO}": ${BASH_COMMAND}"; exit ${s}'    
set -uo pipefail    
trap "${trap_msg}" ERR    

virtualEnvPath=$1/ansible-venv

# Install packages needed on a base Debian system
sudo apt update
sudo apt --yes install  --no-install-recommends $(
echo "build-essential
      python3-httpx
      python3-dev
      python3-netaddr
      python3-pip
      python3-setuptools
      python3-wheel
      python3-venv
      sshpass" )

# package requirements

mkdir -p ${virtualEnvPath}

# Create requirements file for pip
echo "
ansible
ansible-cmdb
ansible-core
ansible-lint
yamllint
infisicalsdk
httpx
molecule
" > ${virtualEnvPath}/requirements.txt



# Create virtual environment we we install ansible into
if test ! -x ${virtualEnvPath}/bin/pip ; then
    /usr/bin/python3 -m venv ${virtualEnvPath}/
fi

# Upgrade pip
${virtualEnvPath}/bin/pip install --upgrade pip

# install/upgrade ansible in the virtual environment
${virtualEnvPath}/bin/pip install --upgrade --requirement ${virtualEnvPath}/requirements.txt


source ${virtualEnvPath}/bin/activate

mkdir -p $1/git
if test ! -x $1/git/ansible_systemd; then
  cd $1/git/
  git clone https://github.com/stuvusIT/ansible_systemd.git
else
  cd $1/git/ansible_systemd
  git fetch
fi

mkdir -p $1/.ansible/roles
ln -sf  $1/git/ansible_systemd $1/.ansible/roles

