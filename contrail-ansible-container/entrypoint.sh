#!/bin/sh
git clone http://github.com/juniper/contrail-ansible-deployer
mkdir /configs
echo $INSTANCES | jq . > /configs/instances.json
echo $GCE | jq . > /configs/gce.json
echo "[defaults]" > /etc/ansible/ansible.cfg
echo "host_key_checking = False" >> /etc/ansible/ansible.cfg
exec "$@"
