#!/bin/bash
git clone http://github.com/juniper/contrail-ansible-deployer
cd contrail-ansible-deployer
if [[ ! -d /configs ]]; then
  mkdir /configs
fi
if [[ $config ]]; then
  printenv $config > /instances.yaml
fi
echo "[defaults]" > /etc/ansible/ansible.cfg
echo "host_key_checking = False" >> /etc/ansible/ansible.cfg
exec "$@"
