# contrail multicloud ansible
This set of playbooks install and create encrypted connection between gateways
#How to start
1. Install ansible
```bash
apt install ansible 
```
2. Install python modules
```bash
pip install docker-py
```
3. Install inventory dependencies
```bash
pip install -r inventory_build/requirements.txt
```
4. Create inventory 
Template: 
```yaml
<unique host name>:
  id: <unique int>
  cluster: <cluster name>
  ansible_host: <ip reachable by deplyment host>
  ip_public: <ip public>
  ip_local: <ip local>
  local_lan: <cidr>
  protocols: <list with useable protocol>
  services: <optiona flag>
```
Example:
```yaml
AWS_1:
  id: 1
  cluster: AWS_PARIS
  ansible_host: wan ip 
  ip_public: wan ip 
  ip_local: lan ip 
  local_lan: 192.168.100.0/24
  protocols:
    - ipsec_server
    - ipsec_client
    - openvpn_client
    - openvpn_server:
        port: 443
  services:
  - BGP_rr
```
5. Deployment 
```bash
ansi
```


###TODOS
1. Set version to install_docker.yml
2. Make README.md beautiful
3. How to create Invetory
4. Create module for build invetory
5. Add lasers to topology build
6. Use openssl module
7. Download image (remove build)
8. Dynamic inventory 
###Bugs
1. Stroke.conf < ignore_missing_ca_basic_constraint = yes 
2. BGD rr 