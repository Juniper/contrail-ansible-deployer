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

- CentOS 7.4 (kernel >= 3.10.0-693.17.1)
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

#### container host configuration (config/instances.yaml)

This file defines the hosts hosting the containers.
```
vi config/instances.yaml
provider_config:
  bms:
instances:
  bms1:
    provider: bms
    ip: 192.168.1.100
contrail_configuration:
  CONTAINER_REGISTRY: opencontrailnightly
  CONTRAIL_VERSION: latest
  UPGRADE_KERNEL: true
```
#### Contrail configuration

In case no configuration is provided, the playbook will do an all in one installation
on all hosts specified in inventory/hosts.
The following roles are installed by default:
['analytics', 'analytics_database', 'config', 'config_database', 'control', 'k8s_master', 'vrouter', 'webui']
The registry defaults to opencontrailnightly and the latest tag of the container.

For customization use `config/instances.yaml`.

The `examples` directory contains `instances.yaml` for different setups.

## Execution

```
ansible-playbook -i inventory/ playbooks/provision_instances.yml
ansible-playbook -i inventory/ playbooks/configure_instances.yml
ansible-playbook -i inventory/ -e orchestrator=kubernetes playbooks/install_contrail.yml
```
