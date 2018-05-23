# AWS k8s with separate control and data plane instaces
This example creates, configures and installs 3 AWS instances. The first instance   
is configured as control plane node and the other 2 as data plane nodes.    
The provider_config.aws and vpc_subnet_id parameters must be adjusted!     
```
git clone http://github.com/juniper/contrail-ansible-deployer
cd contrail-ansible-deployer
cat << EOF > config/instances.yaml
provider_config:
  aws:
    ec2_access_key: YOUR_EC2_ACCESS_KEY
    ec2_secret_key: YOUR_EC2_SECRET_KEY
    ssh_public_key: PATH_TO_SSH_PUBLIC_KEY
    ssh_private_key: PATH_TO_SSH_PRIVATE_KEY
    ssh_user: SSH_USER
    instance_type: t2.xlarge
    image: ami-337be65c
    region: eu-central-1
    assign_public_ip: yes
    volume_size: 50
    key_pair: YOUR_KEY_PAIR
    ntpserver: 169.254.169.123
instances:
  aws1:
    provider: aws
    vpc_subnet_id: VPC_SUBNET_ID
    roles:
      config_database:
      config:
      control:
      analytics_database:
      analytics:
      webui:
      k8s_master:
      kubemanager:
  aws2:
    UPGRADE_KERNEL: true
    provider: aws
    vpc_subnet_id: VPC_SUBNET_ID
    roles:
      vrouter:
      k8s_node:
  aws3:
    UPGRADE_KERNEL: true
    provider: aws
    vpc_subnet_id: VPC_SUBNET_ID
    roles:
      vrouter:
      k8s_node:
contrail_configuration:
  CONTRAIL_VERSION: latest
global_configuration:
  CONTAINER_REGISTRY: opencontrailnightly
EOF
ansible-playbook -i inventory/ -e orchestrator=kubernetes playbooks/provision_instances.yml
ansible-playbook -i inventory/ -e orchestrator=kubernetes playbooks/configure_instances.yml
ansible-playbook -i inventory/ -e orchestrator=kubernetes playbooks/install_contrail.yml
ansible-playbook -i inventory/ -e orchestrator=kubernetes playbooks/install_k8s.yml
```
