import os
import re

import yaml

# instances.yml roles to ansible roles mapping
roles_mapping = {
    'appformix_flows': ['loadbalancer', 'apiserver', 'clickhouse', 'vflow', 'kafka', 'zookeeper'],
}


def generate_all_vars(instances):
    dir_path = os.path.dirname(os.path.realpath(__file__))
    defaults_file = dir_path + '/defaults/main.yml'
    defaults = load_yaml(defaults_file)
    xflow_configuration = instances.get('xflow_configuration', {})
    xflow_pkg_path = "/opt/software/xflow/"
    all_vars = {}

    ntp_servers = [provider.get('ntpserver', {})
                   for provider in instances['provider_config'].values()
                   if 'ntpserver' in provider]
    if ntp_servers:
        all_vars['ntp_servers'] = ntp_servers
    else:
        print('[warn] no ntp servers found')

    version_cfg_file = dir_path + '/../config.yml'
    version_cfg = load_yaml(version_cfg_file)
    version = version_cfg['xflow_version']

    all_vars['docker_images_tar'] = os.path.join(xflow_pkg_path,
                                                 'xflow-{}.tar.gz'.format(version))
    all_vars['xflow_release'] = str(version)
    xflow_ansible_tar_path = os.path.join(xflow_pkg_path,
                                          'xflow-ansible-{}.tar.gz'.format(version))

    keystone_auth_host = instances.get('contrail_configuration', {}).get('KEYSTONE_AUTH_HOST', {})
    keystone_auth_url_version = instances.get('contrail_configuration', {}).get('KEYSTONE_AUTH_URL_VERSION', {})
    if keystone_auth_host and keystone_auth_url_version:
        all_vars['keystone_auth_url'] = 'http://{}:5000{}'.format(keystone_auth_host, keystone_auth_url_version)
    else:
        print('[warn] no keystone auth url found')

    appformix_ip = [instance.get('ip', {})
                    for instance in instances['instances'].values()
                    if 'appformix_controller' in instance.get('roles', {})]
    if appformix_ip:
        all_vars['appformix_address'] = "http://{}:9000".format(appformix_ip[0])
    else:
        print('[warn] no appformix address found')

    all_vars['keystone_password'] = instances.get('kolla_config', {}) \
        .get('kolla_passwords', {}) \
        .get('keystone_admin_password', {})

    result = {}
    for d in [defaults, all_vars, xflow_configuration]:
        result.update(d)

    return result, xflow_ansible_tar_path


def generate_inventory(instances, all_vars):
    groups_map = {}
    for instance in instances['instances'].values():
        for role in instance['roles']:
            if role in roles_mapping:
                ssh_user = get_instance_credential(instances, instance, 'ssh_user')
                ssh_pwd = get_instance_credential(instances, instance, 'ssh_pwd')
                ssh_private_key = get_instance_credential(instances, instance, 'ssh_private_key')
                hostname = instance['ip']
                group_names = roles_mapping[role]

                for group_name in group_names:
                    if group_name not in groups_map:
                        groups_map[group_name] = {
                            'hosts': {}
                        }

                    hostvars = {'ansible_ssh_user': ssh_user}
                    if ssh_private_key:
                        hostvars['ansible_ssh_private_key_file'] = ssh_private_key
                    else:
                        hostvars['ansible_ssh_pass'] = ssh_pwd
                    groups_map[group_name]['hosts'][hostname] = hostvars

    remove_abundant_zookeeper_nodes(groups_map['zookeeper'], all_vars)
    remove_unused_loadbalancer(groups_map, all_vars)

    return {
        'all': {
            'children': groups_map,
        }
    }


def get_instance_credential(instances, instance, key_name):
    return instance.get(key_name,
                        instances.get('provider_config', {}).get(instance.get('provider'), {}).get(key_name))


def remove_abundant_zookeeper_nodes(zk_group, all_vars):
    zk_hosts = zk_group['hosts']
    current_zk_nodes_no = len(zk_hosts)
    user_provided_zk_nodes_no = all_vars.get('zookeeper_number_of_nodes')
    desired_zk_nodes_no = desired_zookeeper_nodes_number(current_zk_nodes_no, user_provided_zk_nodes_no)
    print('Using {} zookeeper nodes'.format(desired_zk_nodes_no))
    desired_zk_host_keys = sorted(zk_hosts.keys())[:desired_zk_nodes_no]
    zk_group['hosts'] = {k: zk_hosts[k] for k in desired_zk_host_keys}


def desired_zookeeper_nodes_number(current_zk_nodes_no, user_provided_zk_nodes_no):
    desired_zk_nodes_no = 3
    if current_zk_nodes_no < 3:
        desired_zk_nodes_no = 1
    if user_provided_zk_nodes_no:
        desired_zk_nodes_no = user_provided_zk_nodes_no
    return desired_zk_nodes_no


def remove_unused_loadbalancer(groups_map, all_vars):
    if 'keepalived_shared_ip' not in all_vars:
        lb_hosts = len(groups_map['loadbalancer']['hosts'])
        if lb_hosts == 1:
            del groups_map['loadbalancer']
        elif lb_hosts > 1:
            raise ValueError('More than 1 loadbalancer host, but keepalived_shared_ip is not set')


def supply_inventory_vars(inventory, all_vars):
    if all_vars:
        inventory['all']['vars'] = all_vars
    # clickhouse shards
    clickhouse_replication_factor = all_vars.get('clickhouse_replication_factor')
    clickhouse_hosts = [host for host in
                        inventory.get('all', {}).get('children', {}).get('clickhouse', {}).get('hosts', {})]
    clickhouse_hosts.sort()
    if clickhouse_replication_factor >= 1 and clickhouse_hosts:
        if len(clickhouse_hosts) % clickhouse_replication_factor != 0:
            raise RuntimeError(
                "can't divide clickhouse shards evenly: "
                "clickhouse_replication_factor {} while {} clickhouse hosts"
                .format(clickhouse_replication_factor, len(clickhouse_hosts)))
        for idx, clickhouse_host in enumerate(clickhouse_hosts):
            clickhouse_shard = idx // clickhouse_replication_factor + 1
            inventory['all']['children']['clickhouse']['hosts'][clickhouse_host]['clickhouse_shard'] = clickhouse_shard


def load_yaml(filename):
    with open(filename) as f:
        return yaml.safe_load(f)


def save_yaml(obj, filename):
    with open(filename, 'w') as f:
        yaml.dump(obj, f, default_flow_style=False)


def convert_instances_config(inventory_path, instances):
    print('generating xflow inventory...')
    all_vars, xflow_ansible_tar_path = generate_all_vars(instances)
    inventory = generate_inventory(instances, all_vars)
    supply_inventory_vars(inventory, all_vars)
    save_yaml(inventory, inventory_path)
    print('inventory saved to ' + inventory_path)
    return xflow_ansible_tar_path
