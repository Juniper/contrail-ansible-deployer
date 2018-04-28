# contrail-container-deployer

This set of playbooks installs Contrail Networking using a microservices architecture.

# quick start for the impatient (requires a CentOS7 instance)...

This set of commands will configure the instance and install AIO contrail with k8s on the instance:
```
ssh-copy-id 192.168.1.100
yum install -y ansible-2.4.2.0
git clone http://github.com/Juniper/contrail-ansible-deployer
cd contrail-ansible-deployer
ansible-playbook -i inventory/ -e orchestrator=kubernetes -e '{"instances":{"bms1":{"ip":"192.168.1.100","provider":"bms"}}}' playbooks/configure_instances.yml
ansible-playbook -i inventory/ -e orchestrator=kubernetes -e '{"instances":{"bms1":{"ip":"192.168.1.100","provider":"bms"}}}' playbooks/install_contrail.yml
```
The ip address 192.168.1.100 has to be replaced with the instances ip address

# the long story

## container grouping

All processes are running in their own container.
The containers are grouped together into services, similiar to PODs
in kubernetes.

```
                                                                   +-------------+
                                                                   |             |
                                                                   | +---------+ |
                +------------------+                               | |nodemgr  | |
                |                  |                               | +---------+ |
                | +--------------+ |                               | +---------+ |
                | |nodemgr       | | +-----------+ +-------------+ | |redis    | |
                | +--------------+ | |           | |             | | +---------+ |
                | +--------------+ | | +-------+ | | +---------+ | | +---------+ |
+-------------+ | |api           | | | |nodemgr| | | |nodemgr  | | | |api      | | +----------+
|             | | +--------------+ | | +-------+ | | +---------+ | | +---------+ | |          |
| +---------+ | | +--------------+ | | +-------+ | | +---------+ | | +---------+ | | +------+ |
| |rabbitmq | | | |svc monitor   | | | |control| | | |kafka    | | | |collector| | | |redis | |+-----------+
| +---------+ | | +--------------+ | | +-------+ | | +---------+ | | +---------+ | | +------+ ||           |
| +---------+ | | +--------------+ | | +-------+ | | +---------+ | | +---------+ | | +------+ || +-------+ |
| |zookeeper| | | |device manager| | | |dns    | | | |zookeeper| | | |alarm    | | | |job   | || |nodemgr| |
| +---------+ | | +--------------+ | | +-------+ | | +---------+ | | +---------+ | | +------+ || +-------+ |
| +---------+ | | +--------------+ | | +-------+ | | +---------+ | | +---------+ | | +------+ || +-------+ |
| |cassandra| | | |schema        | | | |named  | | | |cassandra| | | |query    | | | |server| || |agent  | |
| +---------+ | | +--------------+ | | +-------+ | | +---------+ | | +---------+ | | +------+ || +-------+ |
|             | |                  | |           | |             | |             | |          ||           |
| configdb    | |  config          | |  control  | | analyticsdb | |  analytics  | | webui    || vrouter   |
|             | |                  | |           | |             | |             | |          ||           |
+-------------+ +------------------+ +-----------+ +-------------+ +-------------+ +----------++-----------+
```

## Prerequisites

- CentOS 7.4 (kernel >= 3.10.0-693.17.1)
- Ansible (==2.4.2.0)
- working name resolution through either DNS or host file for long and short hostnames of the cluster nodes
- docker engine (tested with 17.03.1-ce)
- docker-compose (tested with 1.17.0) installed
- docker-compose python library (tested with 1.9.0)
- in case of k8s will be used, the tested version is 1.9.2.0
- for HA, the time must be in sync between the cluster nodes

** NOTE **
Ansible 2.4.2.0 is temporary fix for 2.5 issues with our playbooks.

## instructions

### get the playbooks

```
git clone http://github.com/Juniper/contrail-ansible-deployer
```

### Providers

The playbooks support installing Contrail on these providers:
-- bms - Baremetal Server
-- kvm - KVM hosted Virtual Machines
-- gce - GCE hosted Virtual Machines
-- aws - AWS hosted Virtual Machines

### The plays

The playbook contains three plays:

- playbooks/provision_instances.yml

Provisions operating system instances for hosting the containers
to the following infrastructure providers:

-- kvm    
-- gce     
-- aws    
-- azure (to be implemented)
-- openstack (to be implemented)

- playbooks/configure_instances.yml

Configures provisioned instances. Applicable to all providers.
Installs software, configures operating system as outlined under
prerquisites.

- playbooks/install_contrail.yml

Pulls, configures and starts Contrail containers.

#### configuration

Configuration for all three plays is done in a single file (default locataion:
config/instances.yaml)
The configuration has multiple main sections.

#### provider configuration

This section configures provider specific settings.

##### kvm provider example
```
provider_config:                                          # the provider section contains all provider relevant configuration
  kvm:                                                    # Mandatory.
    image: CentOS-7-x86_64-GenericCloud-1710.qcow2.xz     # Mandatory for provision play. Image to be deployed.
    image_url: https://cloud.centos.org/centos/7/images/  # Mandatory for provision play. Path/url to image.
    ssh_pwd: contrail123                                  # Mandatory for provision/configuration/install play. Ssh password set/used.
    ssh_user: centos                                      # Mandatory for provision/configuration/install play. Ssh user set/used.
    ssh_public_key: /home/centos/.ssh/id_rsa.pub          # Optional for provision/configuration/install play.
    ssh_private_key: /home/centos/.ssh/id_rsa             # Optional for provision/configuration/install play.
    vcpu: 12                                              # Mandatory for provision play.
    vram: 64000                                           # Mandatory for provision play.
    vdisk: 100G                                           # Mandatory for provision play.
    subnet_prefix: 192.168.1.0                            # Mandatory for provision play.
    subnet_netmask: 255.255.255.0                         # Mandatory for provision play.
    gateway: 192.168.1.1                                  # Mandatory for provision play.
    nameserver: 10.84.5.100                               # Mandatory for provision play.
    ntpserver: 192.168.1.1                                # Mandatory for provision/configuration play.
    domainsuffix: local                                   # Mandatory for provision play.
```
##### bms provider example
```
provider_config:
  bms:                                            # Mandatory.
    ssh_pwd: contrail123                          # Optional. Not needed if ssh keys are used.
    ssh_user: centos                              # Mandatory.
    ssh_public_key: /home/centos/.ssh/id_rsa.pub  # Optional. Not needed if ssh password is used.
    ssh_private_key: /home/centos/.ssh/id_rsa     # Optional. Not needed if ssh password is used.
    ntpserver: 192.168.1.1                        # Optional. Needed if ntp server should be configured.
    domainsuffix: local                           # Optional. Needed if configuration play should configure /etc/hosts
```
##### aws provider example
```
provider_config:
  aws:                                            # Mandatory.
    ec2_access_key: THIS_IS_YOUR_ACCESS_KEY       # Mandatory.
    ec2_secret_key: THIS_IS_YOUR_SECRET_KEY       # Mandatory.
    ssh_public_key: /home/centos/.ssh/id_rsa.pub  # Optional.
    ssh_private_key: /home/centos/.ssh/id_rsa     # Optional.
    ssh_user: centos                              # Mandatory.
    instance_type: t2.xlarge                      # Mandatory.
    image: ami-337be65c                           # Mandatory.
    region: eu-central-1                          # Mandatory.
    security_group: SECURITY_GROUP_ID             # Mandatory.
    vpc_subnet_id: VPC_SUBNET_ID                  # Mandatory.
    assign_public_ip: yes                         # Mandatory.
    volume_size: 50                               # Mandatory.
    key_pair: KEYPAIR_NAME                        # Mandatory.
```
##### gce provider example
```
provider_config:
  gce:                           # Mandatory.
    service_account_email:       # Mandatory. GCE service account email address.
    credentials_file:            # Mandatory. Path to GCE account json file.
    project_id:                  # Mandatory. GCE project name.
    ssh_user:                    # Mandatory. Ssh user for GCE instances.
    ssh_pwd:                     # Optional.  Ssh password used by ssh user, not needed when public is used
    ssh_private_key:             # Optional.  Path to private SSH key, used by by ssh user, not needed when ssh-agent loaded private key
    machine_type: n1-standard-4  # Mandatory. Default is too small
    image: centos-7              # Mandatory. For provisioning and configuration only centos-7 is currently supported.
    network: microservice-vn     # Optional.  Defaults to default
    subnetwork: microservice-sn  # Optional.  Defaults to default
    zone: us-west1-aA            # Optional.  Defaults to  ?
    disk_size: 50                # Mandatory. Default is too small
```

### Global services configuration
This section sets global service parameters. All parameters are optional.

```
global_configuration:
  CONTAINER_REGISTRY: opencontrailnightly
  REGISTRY_PRIVATE_INSECURE: True
  CONTAINER_REGISTRY_USERNAME: YourRegistryUser
  CONTAINER_REGISTRY_PASSWORD: YourRegistryPassword
```

### Contrail services configuration
This section sets global contrail service parameters. All parameters are optional.

```
contrail_configuration:     # Contrail service configuration section
  CONTRAIL_VERSION: latest
  UPGRADE_KERNEL: true
```

[Complete list of contrail_configuration](contrail_configuration.md)

### Kolla services configuration
In case kolla openstack is deployed, this section defines the paramters for it.

```
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
  kolla_passwords:
    metadata_secret: strongmetdatasecret
    keystone_admin_password: password
```

More documentation about kolla-ansible parameters can be found in kolla-ansible repository.

### Instances
Instances are the operating systems on which the containers will be launched.
The instance configuration has only a very few provider specific knobs.
The instance configuration specifies which roles are installed on which instance.
Furthermore instance wide and role specifc contrail and kolla configurations can be
specified, overwriting the paramters from the global contrail and kolla configuration
settings.

#### GCE default AIO instance
This is a very simple all in one GCE instance. It will install all contrail roles
and kubernetes master and node using default configuration.
```
instances:
  gce1:                          # Mandatory. Instance name
    provider: gce                # Mandatory. Instance runs on GCE
```
#### AWS default AIO HA
This example uses three EC2 instances to deploy and AIO HA setup with all roles
and default parameters.
```
instances:
  aws1:
    provider: aws
  aws2:
    provider: aws
  aws3:
    provider: aws
```

#### KVM control plane instance
A KVM based instance only installing contrail control plane containers.
```
instances:
  kvm1:
    provider: kvm
    ip: 10.0.0.1
    host: 1.1.1.1
    bridge: br1
    roles:
      config_database:
      config:
      control:
      analytics_database:
      analytics:
      webui:
      k8s_master:
```
### more examples
[GCE k8s HA with separate control and data plane instaces](examples/gce1.md)
[AWS Kolla HA with separate control and data plane instaces](examples/aws1.md)
[KVM Kolla per instance and role configuration](examples/kvm1.md)
[KVM Kolla and k8s](examples/bms2.md)
[BMS remote compute configuration](examples/bms1.md)

### start the playbooks

Instance provisioning:
```
ansible-playbook -i inventory/ playbooks/provision_instances.yml
```

Instance configuration:
```
ansible-playbook -i inventory/ playbooks/configure_instances.yml
```

Contrail installation:
orchestrator can be openstack (installs kolla) or none or kubernetes (for pure k8s installations).
```
ansible-playbook -e orchestrator=none|openstack|kubernetes -i inventory/ playbooks/install_contrail.yml
```

The location of the configuration file (config/instances.yaml) can be changed
using the -e config_file= parameter, i.e.:

```
ansible-playbook -i inventory/ -e config_file=/config/instances_gce.yml playbooks/install_contrail.yml
```

yaml and json formats are supported.

