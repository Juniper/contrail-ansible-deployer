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

### general    

The playbook contains three plays:    

- playbooks/provision_instances.yml    

Provisions operating system instances for hosting the containers    
to the following providers:    
-- kvm    
-- gce    
-- aws (to be implemented)    
-- azure (to be implemented)    
-- openstack (to be implemented)    

- playbooks/configure_instances.yml    

Configures provisioned instances. Applicable to all providers.    
Installs software, configures operating system as outlined under    
prerquisites.    

- playbooks/install_contrail.yml    

Pulls, configures and starts Contrail containers.    

#### configuration

Configuration for all three plays is done in a single file    

```
provider_config: # the provider section contains all provider relevant configuration
  kvm:
    image: CentOS-7-x86_64-GenericCloud-1710.qcow2.xz     # Mandatory for provision play. Image to be deployed.
    image_url: https://cloud.centos.org/centos/7/images/  # Mandatory for provision play. Path/url to image.
    ssh_pwd: contrail123                                  # Mandatory for provision/configuration/install play. Ssh password set/used.
    ssh_user: root                                        # Mandatory for provision/configuration/install play. Ssh user set/used.
    ssh_public_key:                                       # Optional for provision/configuration/install play.
    ssh_private_key:                                      # Optional for provision/configuration/install play.
    vcpu: 12                                              # Mandatory for provision play.
    vram: 64000                                           # Mandatory for provision play.
    vdisk: 100G                                           # Mandatory for provision play.
    subnet_prefix: 192.168.1.0                            # Mandatory for provision play.
    subnet_netmask: 255.255.255.0                         # Mandatory for provision play.
    gateway: 192.168.1.1                                  # Mandatory for provision play.
    nameserver: 10.84.5.100                               # Mandatory for provision play.
    ntpserver: 192.168.1.1                                # Mandatory for provision/configuration play.
    domainsuffix: local                                   # Mandatory for provision play.
  gce:
    service_account_email:       # Mandatory. GCE service account email address.
    credentials_file:            # Mandatory. Path to GCE account json file.
    project_id:                  # Mandatory. GCE project name.
    ssh_user:                    # Mandatory. Ssh user for GCE instances.
    #ssh_pwd:                    # Optional.  Ssh password used by ssh user, not needed when public is used
    ssh_private_key:             # Optional.  Path to private SSH key, used by by ssh user, not needed when ssh-agent loaded private key
    machine_type: n1-standard-4  # Mandatory. Default is too small
    image: centos-7              # Mandatory. For provisioning and configuration only centos-7 is currently supported.
    network: microservice-vn     # Optional.  Defaults to default
    subnetwork: microservice-sn  # Optional.  Defaults to default
    zone: us-west1-aA            # Optional.  Defaults to  ?
    disk_size: 50                # Mandatory. Default is too small
instances:
  gce1:                          # Mandatory. Instance name
    provider: gce                # Mandatory. Instance runs on GCE
      roles:                     # Optional.  If roles is not defined, all below roles will be created
        config_database          # Optional.
        config                   # Optional.
        control                  # Optional.
        analytics_database       # Optional.
        analytics                # Optional.
        webui                    # Optional.
        k8s_master               # Optional.
        k8s_node                 # Optional.
        vrouter                  # Optional.
  gce2:
    provider: gce
  gce3:
    provider: gce
#  kvm1:                        # Mandatory. Instance name. Provisiong play sets instance name as hostname.
#    provider: kvm              # Mandatory. Instance runs on kvm
#    host: 10.87.64.31          # Mandatory for provision play. KVM host.
#    bridge: br1                # Mandatory for provision play. Bridge to which instance is connected to
#    ip: 192.168.1.100          # Mandatory. IP address of instance
#    roles:                     # Optional.  If roles is not defined, all below roles will be created
#      config_database          # Optional.
#      config                   # Optional.
#      control                  # Optional.
#      analytics_database       # Optional.
#      analytics                # Optional.
#      webui                    # Optional.
#      k8s_master               # Optional.
#      k8s_node                 # Optional.
#      vrouter                  # Optional.
#  kvm2:
#    provider: kvm
#    host: 10.87.64.32
#    bridge: br1
#    ip: 192.168.1.101
#  kvm3:
#    provider: kvm
#    host: 10.87.64.33
#    bridge: br1
#    ip: 192.168.1.102
#  kvm4:
#    provider: kvm
#    host: 10.87.64.33
#    bridge: br1
#    ip: 192.168.1.104
#    roles:
#      vrouter:
contrail_configuration:     # Contrail service configuration section
  CONTAINER_REGISTRY: michaelhenkel
  CONTRAIL_VERSION: 5.0.0-134-centos7-ocata
```

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
```
ansible-playbook -i inventory/ playbooks/install_contrail.yml
```

The location of the configuration file (inventory/instances.yml) can be changes    
using the -e config_file= parameter, i.e.:    

```
ansible-playbook -i inventory/ -e config_file=/config/instances_gce.yml playbooks/install_contrail.yml
```

yaml and json formats are supported.    
