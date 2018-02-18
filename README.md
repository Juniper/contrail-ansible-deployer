# contrail-container-deployer

This set of playbooks installs Contrail Networking using a microservices architecture.

## container grouping

All processes are running in their own container.
The containers are grouped together into services, similiar to PODs
in kubernetes.

```
                                                                   +-------------+
                                                                   |             |
                                                                   | +---------+ |
                                                                   | |nodemgr  | |
                                                                   | +---------+ |
                                                                   | +---------+ |
                                                                   | |redis    | |
                                                                   | +---------+ |
                                                                   | +---------+ |
                +------------------+                               | |api      | |
                |                  |                               | +---------+ |
                | +--------------+ |                               | +---------+ |
                | |nodemgr       | | +-----------+ +-------------+ | |collector| |
                | +--------------+ | |           | |             | | +---------+ |
                | +--------------+ | | +-------+ | | +---------+ | | +---------+ |
+-------------+ | |api           | | | |nodemgr| | | |nodemgr  | | | |alarm    | | +----------+
|             | | +--------------+ | | +-------+ | | +---------+ | | +---------+ | |          |
| +---------+ | | +--------------+ | | +-------+ | | +---------+ | | +---------+ | | +------+ |
| |rabbitmq | | | |svc monitor   | | | |control| | | |kafka    | | | |query    | | | |redis | |
| +---------+ | | +--------------+ | | +-------+ | | +---------+ | | +---------+ | | +------+ |
| +---------+ | | +--------------+ | | +-------+ | | +---------+ | | +---------+ | | +------+ |
| |zookeeper| | | |device manager| | | |dns    | | | |zookeeper| | | |snmp     | | | |job   | |
| +---------+ | | +--------------+ | | +-------+ | | +---------+ | | +---------+ | | +------+ |
| +---------+ | | +--------------+ | | +-------+ | | +---------+ | | +---------+ | | +------+ |
| |cassandra| | | |schema        | | | |named  | | | |cassandra| | | |topology | | | |server| |
| +---------+ | | +--------------+ | | +-------+ | | +---------+ | | +---------+ | | +------+ |
|             | |                  | |           | |             | |             | |          |
| configdb    | |  config          | |  control  | | analyticsdb | |  analytics  | | webui    |
|             | |                  | |           | |             | |             | |          |
+-------------+ +------------------+ +-----------+ +-------------+ +-------------+ +----------+
```

## Prerequisites

- CentOS 7.4
- working name resolution through either DNS or host file for long and short hostnames of the cluster nodes
- docker engine (tested with 17.03.1-ce)
- docker-compose (tested with 1.17.0) installed
- docker-compose python library (tested with 1.9.0)
- in case of k8s will be used, the tested version is 1.9.2.0
- for HA, the time must be in sync between the cluster nodes

## instructions

### get the playbooks

```
git clone http://github.com/Juniper/contrail-ansible-deployer
```

### configuration

#### container host configuration (inventory/hosts)

This file defines the hosts hosting the containers.
```
vi inventory/hosts
container_hosts:
  hosts:
    192.168.1.100:                   # container host
      ansible_ssh_pass: contrail123  # container host password
    192.168.1.101:
      ansible_ssh_pass: contrail123
    192.168.1.102:
      ansible_ssh_pass: contrail123
```
#### Contrail configuration

In case no configuration is provided, the playbook will do an all in one installation
on all hosts specified in inventory/hosts.
The following roles are installed by default:
['analytics', 'analytics_database', 'config', 'config_database', 'control', 'k8s_master', 'vrouter', 'webui']
The registry defaults to opencontrailnightly and the latest tag of the container.

For customization the file inventory/group_vars/container_hosts.yml must be created.
The inventory/group_vars directory contains some examples.
In this file the following settings can be set:

- Contrail Service configuration
- Registry settings
- Container versions
- Role assignments

## Execution

```
ansible-playbook -i inventory/ playbooks/deploy.yml
```
