# Contrail vCenter integration

## Prerequisites

    yum update -y

    yum install -y yum-plugin-priorities https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm

    yum install -y python-pip

    yum install -y git

    yum install ansible-2.3.2.0

    pip install pyvmomi


## Steps for provisioning

## Setup vcenter server with Datacenter/Cluster/DVSwitches/ContrailVM etc.

clone the contrail-ansible-deployer repo

    git clone git@github.com:Juniper/contrail-ansible-deployer.git

    cp playbooks/roles/vcenter/vars/vcenter_vars.yml.sample playbooks/roles/vcenter/vars/vcenter_vars.yml

populate the vcenter_vars.yml with vcenter server and esxi hosts parameters.
ContrailVM vmdk is at /cs-shared/contrail-vcenter/vmdk/centos-7.4/LATEST.

Run the vcenter playbook

    ansible-playbook playbooks/vcenter.yml


## Configure and install contrail

populate the config/instances.yaml with contrail roles.

Run the contrail playbooks

    ansible-playbook -i inventory/ -e orchestrator=vcenter playbooks/configure_instances.yml

    ansible-playbook -i inventory/ -e orchestrator=vcenter playbooks/install_contrail.yml

