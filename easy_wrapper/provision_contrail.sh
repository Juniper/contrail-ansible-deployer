#!/bin/bash

yum -y install epel-release
yum -y remove python-jinja2
yum -y install centos-release-openstack-ocata
yum -y install ansible-2.3.1.0
yum -y install python-oslo-config
yum -y install python-pip
pip install --upgrade Jinja2

modprobe ip_vs
export ANSIBLE_HOST_KEY_CHECKING=False
#ansible-playbook -i inventory/hosts playbooks/prepare_kolla.yml
ansible-playbook -i inventory/hosts playbooks/site.yml

cd ../contrail-kolla-ansible/ansible && ansible-playbook -i inventory/my_inventory -e@../etc/kolla/globals.yml -e@../etc/kolla/passwords.yml -e action=bootstrap-servers kolla-host.yml && cd -

cd ../contrail-kolla-ansible/ansible && ansible-playbook -i inventory/my_inventory -e@../etc/kolla/globals.yml -e@../etc/kolla/passwords.yml -e action=deploy site.yml && cd -

# Assuming CONFIGURE_VMS=true is set in
# contrail-ansible-deployer/inventory/group_vars/all.yml by the contrail role
cd .. && ansible-playbook -t configure_vms -i inventory/ playbooks/deploy.yml && cd -

# Assuming CREATE_CONTAINERS=true is set in
# contrail-ansible-deployer/inventory/group_vars/all.yml by the contrail role
cd .. && ansible-playbook -t create_containers -i inventory/ playbooks/deploy.yml && cd -

cd ../contrail-kolla-ansible/ansible && ansible-playbook -i inventory/my_inventory -e@../etc/kolla/globals.yml -e@../etc/kolla/passwords.yml -e action=deploy post-deploy.yml && cd -

cd ../contrail-kolla-ansible/ansible && ansible-playbook -i inventory/my_inventory -e@../etc/kolla/globals.yml -e@../etc/kolla/passwords.yml -e action=deploy post-deploy-contrail.yml && cd -

