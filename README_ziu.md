# ZIU Ansible
Sequence of steps to perform Zero impact upgrade unsing ansible:
1. Upgrade contrail_container_tag in instances.yaml to set proper version of contrail
2. Run the playbook file ziu.yml to upgrade the control plane:
```sh
sudo -E ansible-playbook -v -e orchestrator=openstack -e config_file=instances.yaml playbooks/ziu.yml
```
3. Run the install_openstack.yml playbook to upgrade openstack plugin
```sh
sudo -E ansible-playbook -v -e orchestrator=openstack -e config_file=instances.yaml playbooks/install_openstack.yml
```
4. Run contrail-status to check all works well
5. Migrate workloads VM from one group of compute nodes. Leave them uncommented in the instances.yaml. Comment other computes not ready to upgrаde in instances.yaml.
6. Run install_contrail.yml playbook to upgrade compute nodes (group that uncommented in instances.yml).
```sh
sudo -E ansible-playbook -v -e orchestrator=openstack -e config_file=instances.yaml playbooks/install_contrail.yml
```
7. Repeat steps 5 and 6 for all groups of compute nodes