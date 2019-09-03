## Introduction

This document contains instructions to deploy a Contrail cluster with OpenStack on AWS.
To deploy OpenStack cluster we use OpenStack Kolla.

Deploying Kolla containers using contrail-kolla-ansible and contrail containers using contrail-ansible-deployer involves the following broad steps:
```
1. Setup base host
2. Deploy Openstack (kolla) and Contrail containers
```

## Requirements

To start working on AWS You will need AWS account with API key/secret access.

For Contrail+Openstack environment You will need to prepare Amazon infra:

1) Dedicated AWS VPC
2) Dedicated AWS Internet Gateway (attached to Yours VPC)
3) Dedicated AWS subnet (attached to Yours VPC)
4) Default route (0.0.0.0/0) added to AWS Route Table assigned to Yours VPC
5) AWS Security Group should allow ALL trafic
6) SSH Keys added to AWS

The example setup consists of a five EC2 instances.

- 3x Contrail Control Plane
- 1x OpenStack Control Plane
- 1x OpenStack Compute

Each AWS EC2 has the resources defined by AWS flavor. (https://aws.amazon.com/ec2/instance-types/)

You will also need base host, on which contrail-ansible-deployer will be installed.

You don't need to create the VMs. Instead, the deployment scripts will do it for you.

**NOTE**: This is just an example deployment for simple test purposes. It is NOT a sizing recommendation or specification.

## Preparing the base host

The server is installed with Centos 7.4. Here are some preparation steps:

```
yum install -y epel-release
yum install -y python-urllib3 git python-pip python-boto python2-boto3
pip install ansible==2.5.2.0
```

Next, clone the contrail-ansible-deployer repo and populate the configuration:

```
git clone https://github.com/Juniper/contrail-ansible-deployer
cd contrail-ansible-deployer
> config/instances.yaml
vi config/instances.yaml
```

Here is an instances.yaml example:

```
provider_config:
  aws:
    ec2_access_key: "ACCESS_KEY"
    ec2_secret_key: "SECRET_KEY"
    ssh_public_key: /root/.ssh/id_rsa.pub
    ssh_private_key: /root/.ssh/id_rsa
    ssh_user: centos
    instance_type: t2.xlarge
    # https://wiki.centos.org/Cloud/AWS#head-78d1e3a4e6ba5c5a3847750d88266916ffe69648
    image: ami-6e28b517
    # https://docs.aws.amazon.com/general/latest/gr/rande.html#ec2_region
    region: eu-west-1
    security_group: default
    # console.aws.amazon.com/vpc/
    vpc_subnet_id: subnet-ca9c4f82
    assign_public_ip: yes
    volume_size: 50
    key_pair: contrail
instances:
  aws_control1:
    provider: aws
    instance_type: t2.xlarge
    roles:
      config_database:
      config:
      control:
      analytics_database:
      analytics:
      webui:
  aws_control2:
    provider: aws
    instance_type: t2.xlarge
    roles:
      config_database:
      config:
      control:
      analytics_database:
      analytics:
      webui:
  aws_control3:
    provider: aws
    instance_type: t2.xlarge
    roles:
      config_database:
      config:
      control:
      analytics_database:
      analytics:
      webui:
  aws_control_openstack:
    provider: aws
    instance_type: t2.xlarge
    roles:
      openstack:
  aws_compute1:
    provider: aws
    instance_type: t2.xlarge
    roles:
      vrouter:
      openstack_compute:
global_configuration:
  CONTAINER_REGISTRY: opencontrailnightly
contrail_configuration:
  CONTRAIL_VERSION: latest
  CLOUD_ORCHESTRATOR: openstack
  RABBITMQ_NODE_PORT: 5673
  AUTH_MODE: keystone
  KEYSTONE_AUTH_URL_VERSION: /v3
  KEYSTONE_AUTH_ADMIN_PASSWORD: contrail123
  UPGRADE_KERNEL: true
kolla_config:
  customize:
    nova.conf: |
      [libvirt]
      virt_type=qemu
      cpu_mode=none
  kolla_globals:
    network_interface: "eth0"
    kolla_external_vip_interface: "eth0"
    enable_haproxy: "no"
    enable_ironic: "no"
    enable_swift: "no"
```

## Deploying the Cluster

The deployment takes just four steps:

```
ansible-playbook -i inventory/ playbooks/provision_instances.yml
ansible-playbook -i inventory/ playbooks/configure_instances.yml
ansible-playbook -i inventory/ playbooks/install_openstack.yml
ansible-playbook -i inventory/ -e orchestrator=openstack playbooks/install_contrail.yml
```

After the first step completes you can SSH from the server to all EC2 instances with SSH key You used during deployment.

## Launching & Interconnecting Tenant PODs and VMs

Log into EC2 instance with OpenStack role.

```
yum install -y gcc python-devel wget
pip install python-openstackclient
pip install python-ironicclient
```
```
source /etc/kolla/admin-openrc.sh
wget http://download.cirros-cloud.net/0.4.0/cirros-0.4.0-x86_64-disk.img
openstack image create cirros2 --disk-format qcow2 --public --container-format bare --file cirros-0.4.0-x86_64-disk.img                                      
openstack network create testvn
openstack subnet create --subnet-range 192.168.100.0/24 --network testvn subnet1
openstack flavor create --ram 512 --disk 1 --vcpus 1 m1.tiny
NET_ID=`openstack network list | grep testvn | awk -F '|' '{print $2}' | tr -d ' '`
openstack server create --flavor m1.tiny --image cirros2 --nic net-id=${NET_ID} test_vm1
openstack server create --flavor m1.tiny --image cirros2 --nic net-id=${NET_ID} test_vm2
```
