# Instructions for setting up contrail vcenter integration

Follow the instructions here to setup vcenter server with Datacenter/Cluster/DVSwitches/contrailVM etc. 

## Prerequisites

Need to have ansible >= 2.3 and pyvmomi package.

## Steps for provisioning

clone the contrail-ansible-deployer repo

    git clone git@github.com:Juniper/contrail-ansible-deployer.git

    cp playbooks/roles/vcenter/vars/vcenter_vars.yml.sample playbooks/roles/vcenter/vars/vcenter_vars.yml

populate the vcenter_vars.yml with vcenter server and esxi hosts parameters.

Run the vcenter playbook

    ansible-playbook playbooks/vcenter.yml

