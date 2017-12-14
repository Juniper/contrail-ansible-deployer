# Instructions for installing Contrail Micro Services with Kolla

This set of instructions explains how to separately install Contrail Micro Services    
with Kolla OpenStack containers. This installation procedure does not use Kolla    
Ansible to deploy Contrail but the contrail-ansible-deployer.    

## Prerequisites

The example configuration assumes a multi-node setup with three hosts:   
192.168.1.100, 192.168.1.101, 192.168.1.102    
All hosts contain all roles (OpenStack, Contrail, Compute).    
The hosts have to be installed with CentOS 7.4.    

## The process

- pull contrail-ansible playbooks for kolla
- configure kolla ansible
- run kolla ansible bootstrap
- pull contrail-ansible-deployer playbooks for contrail
- configure contrail ansible
- run contrail ansible bootstrap
- deploy kolla containers
- deploy contrail containers

### Kolla preparation

#### Get contrail-ansible for kolla
```
git clone https://github.com/Juniper/contrail-ansible.git
```

#### Configure kolla ansible

1. Create the passwords.yml and the globals.yml file    

```
cd ~/contrail-ansible/kolla-ansible/etc/kolla
cp passwords.yml.original passwords.yml
cp globals.yml.original globals.yml
```

2. Set/add the following parameters in ~/contrail-ansible/kolla-ansible/etc/kolla/globals.yml    

```
kolla_install_type: "binary"
openstack_release: "contrail_4_1_8"
docker_registry: "10.84.22.43:5000"
keystone_admin_user: admin
contrail_api_interface_address: "192.168.1.100"
enable_keystone_v3: "no"
kolla_external_vip_address: 192.168.1.100
kolla_external_vip_interface: eth0
kolla_internal_vip_address: 192.168.1.100
network_interface: eth0
neutron_plugin_agent: opencontrail
rabbitmq_user: openstack
contrail_docker_registry: 10.84.22.43:5000
enable_nova_compute: 'yes'
```

Adjust the above values.    

3. Add your hosts to the inventory    

```
cat ~/contrail-ansible/kolla-ansible/ansible/inventory/all-in-one |head -40
# These initial groups are the only groups required to be modified. The
# additional groups are for more control of the environment.
[control]
192.168.1.100       ansible_ssh_pass=contrail123
192.168.1.101       ansible_ssh_pass=contrail123
192.168.1.102       ansible_ssh_pass=contrail123

[network]
192.168.1.100       ansible_ssh_pass=contrail123
192.168.1.101       ansible_ssh_pass=contrail123
192.168.1.102       ansible_ssh_pass=contrail123

[compute]
192.168.1.100       ansible_ssh_pass=contrail123
192.168.1.101       ansible_ssh_pass=contrail123
192.168.1.102       ansible_ssh_pass=contrail123

[storage]
192.168.1.100       ansible_ssh_pass=contrail123
192.168.1.101       ansible_ssh_pass=contrail123
192.168.1.102       ansible_ssh_pass=contrail123

[monitoring]
192.168.1.100       ansible_ssh_pass=contrail123
192.168.1.101       ansible_ssh_pass=contrail123
192.168.1.102       ansible_ssh_pass=contrail123
```

Make sure that ssh from the deployment machine to the hosts works.    

#### Run kolla ansible bootstrap to install kolla requirements on the host

```
cd ~/contrail-ansible/kolla-ansible/ansible
ansible-playbook -i inventory/all-in-one -e@../etc/kolla/globals.yml -e@../etc/kolla/passwords.yml -e action=bootstrap-servers kolla-host.yml
```

### Contrail preparation

#### Get contrail-ansible-deployer
```
git clone http://github.com/Juniper/contrail-ansible-deployer
```

#### Configure contrail ansible deployer

1. Add hosts to the inventory    
```
cat ~/contrail-ansible-deployer/inventory/hosts
container_hosts:
  hosts:
    192.168.1.100:
      ansible_ssh_pass: contrail123
    192.168.1.101:
      ansible_ssh_pass: contrail123
    192.168.1.102:
      ansible_ssh_pass: contrail123
```

2. Configure Contrail containers    
Set the following parameters:    
```
cat ~/contrail-ansible-deployer/inventory/group_vars/container_hosts.yml
CONTAINER_REGISTRY: michaelhenkel
contrail_configuration:
  OPENSTACK_VERSION: ocata
  CONTRAIL_VERSION: 4.1.0.0-8
  CONTROLLER_NODES: 192.168.1.100,192.168.1.101,192.168.1.102
  CLOUD_ORCHESTRATOR: openstack
  AUTH_MODE: keystone
  KEYSTONE_AUTH_ADMIN_PASSWORD: c0ntrail123
  KEYSTONE_AUTH_HOST: 192.168.1.100
  RABBITMQ_PORT: 5673
roles:
  192.168.1.100:
    configdb:
    config:
    control:
    webui:
    analytics:
    analyticsdb:
    vrouter:
  192.168.1.101:
    configdb:
    config:
    control:
    webui:
    analytics:
    analyticsdb:
    vrouter:
  192.168.1.102:
    configdb:
    config:
    control:
    webui:
    analytics:
    analyticsdb:
    vrouter:
```

3. install Contrail requirements    
It is important to specify a working ntp server.    
```
ansible-playbook -e '{"CONFIGURE_VMS":true}' -e '{"CONTAINER_VM_CONFIG":{"network":{"ntpserver":"192.168.1.1"}}}' -i inventory/ playbooks/deploy.yml
```

### Container deployment

#### Deploy kolla containers

```
cd ~/contrail-ansible/kolla-ansible/ansible
ansible-playbook -i inventory/all-in-one -e@../etc/kolla/globals.yml -e@../etc/kolla/passwords.yml -e action=deploy site.yml
```

#### Deploy Contrail containers

```
cd ~/contrail-ansible-deployer
ansible-playbook -e '{"CREATE_CONTAINERS":true}' -i inventory/ playbooks/deploy.yml
```
