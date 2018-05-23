# KVM based k8s HA with separate control and data plane instaces
This example creates, configures and installs 5 KVM instances. The first 3 instances    
are configured as control plane nodes and the remaining 2 as data plane nodes.    
The provider_config.kvm parameters must be adjusted!     
```
git clone http://github.com/juniper/contrail-ansible-deployer
cd contrail-ansible-deployer
cat << EOF > config/instances.yaml
provider_config:
  kvm:
    image: CentOS-7-x86_64-GenericCloud-1802.qcow2.xz
    image_url: https://cloud.centos.org/centos/7/images/
    ssh_pwd: <Password> 
    ssh_user: root
    vcpu: 8
    vram: 24000
    vdisk: 100G
    subnet_prefix: 192.168.1.0
    subnet_netmask: 255.255.255.0
    gateway: 192.168.1.1
    nameserver: 10.84.5.100
    ntpserver: 192.168.1.1
    domainsuffix: local
instances:
  kvm1:
    provider: kvm
    host: 10.87.64.31
    bridge: br1
    ip: 192.168.1.100
    roles:
      config_database:
      config:
      control:
      analytics_database:
      analytics:
      webui:
      k8s_master:
      kubemanager:
  kvm2:
    provider: kvm
    host: 10.87.64.32
    bridge: br1
    ip: 192.168.1.101
    roles:
      config_database:
      config:
      control:
      analytics_database:
      analytics:
      webui:
      kubemanager:
  kvm3:
    provider: kvm
    host: 10.87.64.33
    bridge: br1
    ip: 192.168.1.102
    roles:
      config_database:
      config:
      control:
      analytics_database:
      analytics:
      webui:
      kubemanager:
  kvm4:
    provider: kvm
    host: 10.87.64.33
    bridge: br1
    ip: 192.168.1.104
    UPGRADE_KERNEL: true
    roles:
      vrouter:
      k8s_node:
  kvm5:
    provider: kvm
    host: 10.87.64.32
    bridge: br1
    ip: 192.168.1.105
    UPGRADE_KERNEL: true
    roles:
      vrouter:
      k8s_node:
contrail_configuration:
  CONTRAIL_VERSION: latest
global_configuration:
  CONTAINER_REGISTRY: opencontrailnightly
EOF
ansible-playbook -e orchestrator=kubernetes -i inventory/ playbooks/provision_instances.yml
ansible-playbook -e orchestrator=kubernetes -i inventory/ playbooks/configure_instances.yml
ansible-playbook -e orchestrator=kubernetes -i inventory/ playbooks/install_contrail.yml
ansible-playbook -e orchestrator=kubernetes -i inventory/ playbooks/install_k8s.yml
```
