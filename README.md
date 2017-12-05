# contrail-container-deployer
## instructions

### get playbook    

```
git clone http://github.com/michaelhenkel/contrail-container-deployer
```

### configuration    

The playbook consists of three main plays:    
- install virtual machines (container hosts) hosting the containers    
- configure/install required software on virtual machines    
- create containers    

All three plays can be enabled/disabled and run individually:    

```
vi inventory/group_vars/all.yml
---
BUILD_VMS: true #will build virtual machines, true/false
CONFIGURE_VMS: true #will configure virtual machines, true/false
CREATE_CONTAINERS: true #will create containers, true/false
```

### Prerequisites

The container hosts have to have:    
- working name resolution through either DNS or host file    
- docker engine (1.12.6) and docker-compose installed   
- in case of HA, the time must be in sync    

The first version only supports CentOS 7.4 for the container host    
creation and configuration.    

The playbooks/roles/configure_container_hosts play takes care if    
required.    

### hosts configuration (inventory/hosts)

This file defines the hypervisors hosting the container hosts and    
the container hosts. The hypervisors section is only required in case    
the container host VMs will be built:    
```
vi inventory/hosts
hypervisors:
  hosts:
    10.87.64.31:         # hypervisor 1 IP address
      bridge: br1        # virsh network the container vms will be connected to
      container_hosts:   # container host vms to be started on that hypervisor
        192.168.1.100:
    10.87.64.32:
      bridge: br1
      container_hosts:
        192.168.1.101:
    10.87.64.33:
      bridge: br1
      container_hosts:
        192.168.1.102:
container_hosts:
  hosts:
    192.168.1.100:                   # container host
      ansible_ssh_pass: contrail123  # container host password
    192.168.1.101:
      ansible_ssh_pass: contrail123
    192.168.1.102:
      ansible_ssh_pass: contrail123
```

#### Container VM configuration

The pre-requisites for building the container VMs are:    
- kvm    
- a virsh network to which the VMs can be connected    

The container VMs configuration is done in:    
```
vi inventory/group_vars/hypervisors.yml
CENTOS_DOWNLOAD_URL: http://cloud.centos.org/centos/7/images/ #Download URL for CentOS image
CENTOS_IMAGE_NAME: CentOS-7-x86_64-GenericCloud-1710.qcow2.xz #CentOS image name
CONTAINER_VM_CONFIG:
  root_pwd: contrail123
  vcpu: 4
  vram: 16384
  vdisk: 100G
  network:
    subnet_prefix: 192.168.1.0
    subnet_netmask: 255.255.255.0
    gatway: 192.168.1.1
    nameserver: 10.84.5.100
    ntpserver: 192.168.1.1
    domainsuffix: local
```

#### Contrail configuration

The minimal configuration requires the cluster node  ip addresses,    
the contrail version and docker registry:    
```
vi inventory/group_vars/container_hosts.yml
CONTAINER_REGISTRY: michaelhenkel
contrail_configuration:
  CONTRAIL_VERSION: 4.1.0.0-4
  CONTROLLER_NODES: 192.168.1.100,192.168.1.101,192.168.1.102
  CLOUD_ORCHESTRATOR: kubernetes
```

The role assignment is done in the same file:    
```
vi inventory/group_vars/container_hosts.yml
roles:
  192.168.1.100:
    configdb:
    config:
    control:
    webui:
    analytics:
    analyticsdb:
    k8s_master:
    vrouter:
  192.168.1.101:
    configdb:
    config:
    control:
    webui:
    analytics:
    analyticsdb:
    k8s_master:
    vrouter:
  192.168.1.102:
    configdb:
    config:
    control:
    webui:
    analytics:
    analyticsdb:
    k8s_master:
    vrouter:
```
## Execution

```
ansible-playbook -i inventory/ playbooks/deploy.yml
```
