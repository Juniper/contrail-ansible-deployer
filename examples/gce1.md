# GCE k8s HA with separate control and data plane instaces
This example creates, configures and installs  6 GCE instances. The first 3 instances    
are configured as control plane nodes and the remaining 3 as data plane nodes.    
The provider_config.gce parameters must be adjusted!     
```
git clone http://github.com/juniper/contrail-ansible-deployer
cd contrail-ansible-deployer
cat << EOF > config/instances.yaml
provider_config:
  gce:
    service_account_email: YOU_SERVICE_ACCOUNT_EMAIL
    credentials_file: /path/to/creds.json
    project_id: YOUR_PROJECT_ID
    ssh_user: centos
    machine_type: n1-standard-4
    image: centos-7
    network: microservice-vn
    subnetwork: microservice-sn
    zone: us-west1-a
    disk_size: 50
instances:
  master1:
    provider: gce
    roles:
      config_database:
      config:
      control:
      analytics_database:
      analytics:
      webui:
      k8s_master:
  master2:
    provider: gce
    roles:
      config_database:
      config:
      control:
      analytics_database:
      analytics:
      webui:
      k8s_master:
  master3:
    provider: gce
    roles:
      config_database:
      config:
      control:
      analytics_database:
      analytics:
      webui:
      k8s_master:
  node1:
    provider: gce
    roles:
      vrouter:
      k8s_node:
  node2:
    provider: gce
    roles:
      vrouter:
      k8s_node:
  node3:
    provider: gce
    roles:
      vrouter:
      k8s_node:
EOF
ansible-playbook -i inventory/ playbooks/provision_instances.yml
ansible-playbook -e orchestrator=kubernetes -i inventory/ playbooks/configure_instances.yml
ansible-playbook -e orchestrator=kubernetes -i inventory/ playbooks/install_contrail.yml
ansible-playbook -e orchestrator=kubernetes -i inventory/ playbooks/install_k8s.yml
```
