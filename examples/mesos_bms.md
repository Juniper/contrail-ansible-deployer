## Introduction

This document contains instructions to deploy a Contrail cluster on Mesos dcos
orchestration Cluster.

# Deployment of contrail on MESOS DCOS orchestrator

This example creates and configures contrail on dcos cluster. The example
includes instances for mesos_master, mesos_agent_public, mesos_agent_private and
a boot node. In all there are 4 instances. Contrail mesos-manager will be
installed on instances with role 'mesosmanager' and contrail mesos cni will be
installed on instances with role 'mesosmanager_agent_private' or
'mesosmanager_agent_public'

## Requirements

To start working on contrail deployment, you will need to have a DCOS setup up
and running. Make sure to install contrail roles on the infrastucture/boot
instance.

```
git clone http://github.com/juniper/contrail-ansible-deployer
cd contrail-ansible-deployer
cat << EOF > config/instances.yaml
provider_config:
  bms:
    ssh_pwd: c0ntrail123
    ssh_user: root
    ntpserver: 10.84.5.100
    domainsuffix: local
instances:
  bms1:
    provider: bms
    ip: BOOT INSTANCE IP
    roles:
        config_database:
        config:
        webui:
        control:
        analytics_database:
        analytics:
  bms2:
    provider: bms
    ip: MESOS MASTER INSTANCE IP
    roles:
        mesos_master:
  bms3:
    provider: bms
    ip: MESOS AGENT PRIVATE INSTANCE IP
    roles:
        vrouter:
        mesosmanager:
        mesos_agent_private:
  bms4:
    provider: bms
    ip: MESOS AGENT PUBLIC INSTANCE IP
    roles:
        vrouter:
        mesosmanager:
        mesos_agent_public:
contrail_configuration:
  CLOUD_ORCHESTRATOR: mesos
  CONTRAIL_VERSION: latest
  RABBITMQ_NODE_PORT: 5673
global_configuration:
  CONTAINER_REGISTRY: opencontrailnightly
EOF
ansible-playbook -i inventory/ -e orchestrator=mesos playbooks/configure_instances.yml
ansible-playbook -i inventory/ -e orchestrator=mesos playbooks/install_contrail.yml
```
