## Introduction

This document contains instructions to deploy a Contrail cluster with vCenter 6.5.

1. Setup base host running Centos 7.5 then add 2 more hosts running Centos 7.5 for HA (if desired)
2. Setup vCenter and 1 or more ESXi servers
3. Deploy Contrail Containers and vRouter VMs


## Requirements

To start deploying the vCenter cluster you will 1 or 3 base hosts depending on if you want an HA cluster or not.

On your base host/build server you will need to run the following steps:

The example setup consists of a 3 Contrail controllers and 2 computes.

- 3x Contrail Control Plane
- 2x ESXi Compute

You will also need base host, on which contrail-ansible-deployer will be installed.

**NOTE**: This is just an example deployment for simple test purposes. It is NOT a sizing recommendation or specification.

## Preparing the base host

The build/controller server is installed with Centos 7.4. Here are the preparation steps:

```
yum update -y
yum install -y yum-plugin-priorities https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm
yum install -y python-pip git gcc python-devel sshpass
pip install "ansible==2.7.18" pyvmomi
```

Next, get the contrail-ansible-deployer from https://www.juniper.net/support/downloads/?p=contrail#sw:

```
tar –xvf {Ansible deployer}.tgz
```

or clone latest version from github:

```
git clone http://www.github.com/Juniper/contrail-ansible-deployer
```

## Populate vcenter_vars.yml

Next, populate the following file: playbooks/roles/vcenter/vars/vcenter_vars.yml

NOTE: https://github.com/Juniper/contrail-ansible-deployer/blob/master/playbooks/roles/vcenter/vars/vcenter_vars.yml.sample is the complete set of configuration variables

Here is an vcenter_vars.yml example that is multi-node and multi-nic:

```
vcenter_servers:
  - SRV1:
      hostname: 10.85.192.50
      username: administrator@vsphere.local
      password: ****
      datacentername: "PS-DC1"
      clusternames:
        - "DC1-CL1"
      vmdk: http://10.85.192.51/centos-7.5/LATEST/ContrailVM.ovf
      dv_switch:
        dv_switch_name: overlay
        dv_switch_version: 6.5.0
      dv_port_group:
        dv_portgroup_name: VM_pg
        number_of_ports: 1800
      dv_switch_control_data:
        dv_switch_name: underlay
        dv_switch_version: 6.5.0
      dv_port_group_control_data:
        dv_portgroup_name: data_pg
        number_of_ports: 3
        uplink: vmnic8

esxihosts:
  - name: 10.85.192.8
    username: root
    password: contrail123
    datastore: datastore1
    datacenter: "PS-DC1"
    cluster: "DC1-CL1"
    std_switch_list:
      - pg_name: mgmt-pg
        switch_name: vSwitch0
    contrail_vm:
      networks:
        - mac: 00:77:56:aa:bb:01
          sw_type: standard
          switch_name: vSwitch0
          pg: mgmt-pg
        - mac: 00:77:56:aa:bb:02
          sw_type: dvs
          switch_name: underlay
          pg: data_pg
    vcenter_server: SRV1
  - name: esx-srv3.pslab.net
    username: root
    password: ******
    datastore: datastore2
    datacenter: "PS-DC1"
    cluster: "DC1-CL1"
    std_switch_list:
      - pg_name: mgmt-pg
        switch_name: vSwitch0
    contrail_vm:
      networks:
         - mac: 00:77:56:aa:bb:03
           sw_type: standard
           switch_name: vSwitch0
           pg: mgmt-pg
         - mac: 00:77:56:aa:bb:04
           sw_type: dvs
           switch_name: underlay
           pg: data_pg
    vcenter_server: SRV1
```

## Deploying the vCenter components

The 1st deployment step is to deploy the vCenter components:

```
cd contrail-ansible-deployer
ansible-playbook playbooks/vcenter.yml

```

After the first step completes you can SSH from the build server/controller to the vRouter VM instances.
This is a good time to validate the connectivity to the controllers and vRouter VM(s). If you are deploying separate 
management and control/data, this is also a good time to validate your routing table on the controller(s) and vRouter VM(s).

## Populate instances.yaml

The 2nd deployment step is to configure the instances.yaml. 

```
cd contrail-ansible-deployer
> config/instances.yaml
vi config/instances.yaml

```

Here is an example of an instances.yaml that is multi-node and multi-nic:

```
provider_config:
  bms:
    ssh_pwd: ****
    ssh_user: root
    ntpserver: 10.85.130.130
    domainsuffix: pslab.net 

instances:
  bms1:
    provider: bms
    ip: 10.85.192.20
    roles:
      config_database:
      config:
      control:
      analytics_database:
      analytics:
      webui:
      vcenter_plugin:
  bms2:
    provider: bms
    ip: 10.85.192.21
    roles:
      config_database:
      config:
      control:
      analytics_database:
      analytics:
      webui:
      vcenter_plugin:
  bms3:
    provider: bms
    ip: 10.85.192.22
    roles:
      config_database:
      config:
      control:
      analytics_database:
      analytics:
      webui:
      vcenter_plugin:
  bms4:
    provider: bms
    esxi_host: 10.85.192.8
    ip: 10.85.192.23
    roles:
      vrouter:
        PHYSICAL_INTERFACE: ens192
      vcenter_manager:
        ESXI_USERNAME: root
        ESXI_PASSWORD: c0ntrail123
  bms5:
    provider: bms
    esxi_host: 10.85.192.10
    ip: 10.85.192.24
    roles:
      vrouter:
        PHYSICAL_INTERFACE: ens192
      vcenter_manager:
        ESXI_USERNAME: root
        ESXI_PASSWORD: c0ntrail123

contrail_configuration:
  CLOUD_ORCHESTRATOR: vcenter
  CONTRAIL_VERSION: 5.0.0-0.40
  CONTROL_DATA_NET_LIST: 10.85.194.0/23
  VROUTER_GATEWAY: 10.85.194.5
  PHYSICAL_INTERFACE: ens160
  CONTROLLER_NODES: 10.85.192.20,10.85.192.21,10.85.192.22
  RABBITMQ_NODE_PORT: 5673
  VCENTER_SERVER: 10.85.192.50
  VCENTER_USERNAME: administrator@vsphere.local
  VCENTER_PASSWORD: ****
  VCENTER_DATACENTER: PS-DC1
  VCENTER_DVSWITCH: overlay
  VCENTER_WSDL_PATH: /usr/src/contrail/contrail-web-core/webroot/js/vim.wsdl
  VCENTER_AUTH_PROTOCOL: https
  CONFIG_NODEMGR__DEFAULTS__minimum_diskGB: 5
  DATABASE_NODEMGR__DEFAULTS__minimum_diskGB: 5

global_configuration:
  CONTAINER_REGISTRY: hub.juniper.net/contrail
  CONTAINER_REGISTRY_PASSWORD: ****
  CONTAINER_REGISTRY_USERNAME: ****
```
## Deploy Contrail

After you populate the instances.yaml then you are ready to run the following playbooks:

```
ansible-playbook -i inventory/ -e orchestrator=vcenter playbooks/configure_instances.yml
ansible-playbook -i inventory/ -e orchestrator=vcenter playbooks/install_contrail.yml

```
