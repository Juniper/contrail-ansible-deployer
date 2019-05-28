#!/usr/bin/python

"""
This filter plugin script takes api_server_list and instances file as input and
returns lists of new roles, existing roles, deleted roles and instances roles
for all the nodes in the instances file.
"""

import requests
import urllib, urllib2
import json

class FilterModule(object):

    keystone_auth_host = ""
    keystone_admin_password = ""

    auth_token = None
    api_server_ip = ""
    api_server_port = "8082"
    contrail_auth_url = ""
    aaa_mode = ""
    node_name_ip_map = {}
    node_ip_name_map = {}
    existing_tor_agents = {}

    valid_roles = ["config", "control", "analytics_database",
                   "analytics", "analytics_alarm", "analytics_snmp", "vrouter"]

    def get_ks_token_request(self):
        keystone_token_request = {
            'auth': {
                'identity': {
                    'methods': [
                        'password'
                    ],
                    'password': {
                        'user': {
                            'domain': {
                                'name': 'default'
                            },
                            'name': 'admin',
                            'password': self.keystone_admin_password
                        }
                    }
                },
                'scope': {
                    'project': {
                        'domain': {
                            'name': 'default'
                        },
                        'name':  'admin'
                    }
                }
            }
        }
        return keystone_token_request

    keystone_auth_headers = {
        'Content-Type': 'application/json'
    }

    contrail_auth_headers = {
        'Content-Type': 'application/json',
        'charset': 'UTF-8'
    }

    contrail_cluster_roles = [
        "config",
        "configdb",
        "analytics",
        "analyticsdb",
        "control"
    ]

    contrail_object_map = {
        "virtual-routers": "vrouter",
        "config-nodes": "config",
        "database-nodes": "analytics_database",
        "bgp-routers": "control",
        "analytics-nodes": "analytics",
        "analytics-alarm-nodes": "analytics_alarm",
        "analytics-snmp-nodes": "analytics_snmp"
    }

    ip_role_map = {
        "virtual-routers": "virtual_router_ip_address",
        "config-nodes": "config_node_ip_address",
        "database-nodes": "database_node_ip_address",
        "bgp-routers": "bgp_router_parameters.address",
        "analytics-nodes": "analytics_node_ip_address",
        "analytics-alarm-nodes": "analytics_alarm_node_ip_address",
        "analytics-snmp-nodes": "analytics_snmp_node_ip_address"
    }

    indexed_roles = [
        'toragent',
    ]

    def filters(self):
        return {
            'calculate_contrail_roles': self.calculate_contrail_roles,
            'extract_roles': self.extract_roles,
            'calculate_deleted_toragent_roles': self.calculate_deleted_toragent_roles,
            'calculate_tsn_haproxy_config': self.calculate_tsn_haproxy_config
        }

    def get_ks_auth_token(self, contrail_config):
        self.keystone_auth_host = contrail_config.get("KEYSTONE_AUTH_HOST", "")
        self.keystone_admin_password = contrail_config.get(
            "KEYSTONE_AUTH_ADMIN_PASSWORD", "")
        keystone_auth_url_version = contrail_config.get(
            "KEYSTONE_AUTH_URL_VERSION",
            "")
        if keystone_auth_url_version == '/v2.0':
            keystone_auth_url_tokens = '/v2.0/tokens'
        else:
            keystone_auth_url_tokens = '/v3/auth/tokens'

        # TODO: Add support for https and non-default port

        keystone_auth_url = 'http://' + str(
            self.keystone_auth_host) + ':35357' + str(keystone_auth_url_tokens)
        try:
            response = self.get_rest_api_response(keystone_auth_url,
                                                  self.keystone_auth_headers,
                                                  data=json.dumps(
                                                    self.get_ks_token_request()
                                                  ),
                                                  request_type="post")
        except Exception as e:
            auth_token = None
        else:
            header = response.headers
            token = header['X-Subject-Token']
            auth_token = token
        return auth_token

    def calculate_valid_api_server_ip(self, api_server_list):
        if self.auth_token and self.aaa_mode != "no-auth":
            self.contrail_auth_headers['X-Auth-Token'] = self.auth_token
        for test_ip in api_server_list:
            test_url = 'http://' + str(test_ip) + ':' + \
                str(self.api_server_port)
            try:
                self.get_rest_api_response(test_url,
                                           headers=self.contrail_auth_headers,
                                           request_type="get")
            except Exception as e:
                continue
            else:
                return test_ip
        return None

    def get_rest_api_response(self, url, headers, data=None, request_type=None):
        response = None
        if request_type == "post":
            response = requests.post(url, headers=headers, data=data)
        elif request_type == "get":
            response = requests.get(url, headers=headers, data=data)
        response.raise_for_status()
        return response

    def get_ip_for_contrail_node(self, instance_name, uuid, contrail_object,
                                 url, headers):
        node_url = url + str(contrail_object[:-1]) + "/" + str(uuid)
        response = self.get_rest_api_response(node_url,
                                              self.contrail_auth_headers,
                                              request_type="get")
        node_object_dict = response.json()
        node_object_dict = node_object_dict[contrail_object[:-1]]
        if "." in self.ip_role_map[contrail_object]:
            key = str(self.ip_role_map[contrail_object]).split('.')[0]
            second_key = str(self.ip_role_map[contrail_object]).split('.')[1]
        else:
            key = str(self.ip_role_map[contrail_object])
            second_key = None

        ip = node_object_dict[key]
        if second_key:
            ip = ip[second_key]
        return ip

    def discover_contrail_cluster(self, instances_nodes_dict,
                                  deleted_nodes_dict):
        self.contrail_auth_url = 'http://' + \
                                 str(self.api_server_ip) + \
                                 ':' + str(self.api_server_port) + '/'
        if self.auth_token and self.aaa_mode != "no-auth":
            self.contrail_auth_headers['X-Auth-Token'] = self.auth_token
        for contrail_object, contrail_role in \
            self.contrail_object_map.iteritems():

            contrail_object_url = self.contrail_auth_url + str(contrail_object)
            response = self.get_rest_api_response(contrail_object_url,
                                                  self.contrail_auth_headers,
                                                  request_type="get")
            object_dict = response.json()
            object_list = object_dict[contrail_object]
            vr_obj_list = []
            if contrail_role == 'vrouter':
                for vr_obj in object_list:
                     vr_href= vr_obj.get('href')
                     response = self.get_rest_api_response(vr_href,
                                                  self.contrail_auth_headers,
                                                  request_type="get")
                     vr_object_dict = response.json()
                     vr_dict = vr_object_dict.get('virtual-router')
                     vr_type = vr_dict.get('virtual_router_type')
                     if  vr_type == 'tor-agent':
                        tor_config = {}
                        toragent_fq_name = vr_dict.get('fq_name')[-1]
                        toragent_ip = vr_dict.get('virtual_router_ip_address')
                        pr_href = vr_dict['physical_router_back_refs'][0].get('href')
                        response = self.get_rest_api_response(pr_href,
                                                  self.contrail_auth_headers,
                                                  request_type="get")
                        pr_object_dict = response.json()
                        pr_name = pr_object_dict['physical-router']['name']
                        pr_vendor = pr_object_dict['physical-router']['physical_router_vendor_name']
                        tor_config['tor_name'] = pr_name
                        tor_config['pr_vendor'] = pr_vendor
                        tor_config['toragent_ip'] = toragent_ip
                        self.existing_tor_agents[toragent_fq_name] = tor_config
                     else:
                        vr_obj_list.append(vr_obj)
                object_list = vr_obj_list
            for object_to_process in object_list:
                if len(object_to_process.get("fq_name", [])) < 2:
                    continue
                instance_name = str(object_to_process.get("fq_name")[-1])
                fq_name = instance_name
                if '.' in instance_name:
                    instance_name = instance_name.split('.')[0]
                uuid = str(object_to_process.get("uuid"))
                ip_address = self.get_ip_for_contrail_node(
                    instance_name,
                    uuid,
                    contrail_object,
                    self.contrail_auth_url,
                    self.contrail_auth_headers)

                # Check if this is a deleted instance
                # Either not in instances.yml or has empty role list in instances
                if instance_name not in instances_nodes_dict:
                    instances_nodes_dict[instance_name] = {}
                    deleted_nodes_dict[fq_name] = ip_address
                elif 'instance_roles' not in instances_nodes_dict[
                    instance_name] or \
                        not len(instances_nodes_dict[instance_name][
                                    'instance_roles']):
                    if instance_name not in deleted_nodes_dict:
                        deleted_nodes_dict[fq_name] = \
                            self.node_name_ip_map[instance_name]

                if 'existing_roles' not in instances_nodes_dict[
                    instance_name]:
                    instances_nodes_dict[instance_name][
                        'existing_roles'] = list()
                instances_nodes_dict[instance_name][
                    'existing_roles'].append(contrail_role)

        return instances_nodes_dict, deleted_nodes_dict

    def calculate_contrail_roles(self, existing_dict, api_server_list,
                                 instances_dict, global_configuration, contrail_configuration):
        # don't calculate anything if global_configuration.ENABLE_DESTROY is not set
        empty_result = {"node_roles_dict": dict(),
                        "deleted_nodes_dict": dict(),
                        "api_server_ip": None}
        enable_destroy = global_configuration.get("ENABLE_DESTROY", True)
        if not isinstance(enable_destroy, bool):
            enable_destroy = str(enable_destroy).lower() == 'true'
        if not enable_destroy:
            return str(empty_result)

        instances_nodes_dict = {}
        deleted_nodes_dict = {}
        invalid_role = None
        cluster_role_set = set()

        for instance_name, instance_config in instances_dict.iteritems():
            instances_nodes_dict[instance_name] = {}
            self.node_name_ip_map[instance_name] = instance_config["ip"]
            self.node_ip_name_map[instance_config["ip"]] = instance_name
            if "roles" in instance_config \
                    and isinstance(instance_config["roles"], dict):
                instances_nodes_dict[instance_name]['instance_roles'] = \
                    list(
                        set(
                            instance_config["roles"].keys()
                        ).intersection(set(self.valid_roles))
                    )
                cluster_role_set.update(instance_config["roles"].keys())

        # Check if Controller Nodes was given
        if contrail_configuration.get('CONFIG_NODES', None):
            controller_node_list = contrail_configuration.get(
                'CONFIG_NODES').split(',')
        elif contrail_configuration.get('CONTROLLER_NODES', None):
            controller_node_list = contrail_configuration.get(
                'CONTROLLER_NODES').split(',')
        else:
            controller_node_list = None
        if isinstance(controller_node_list, list) and \
                len(controller_node_list):
            api_server_list = controller_node_list
        else:
            api_server_list = []

        if contrail_configuration.get("CLOUD_ORCHESTRATOR",None) == "openstack":
            self.auth_token = self.get_ks_auth_token(contrail_configuration)
            self.aaa_mode = contrail_configuration.get("AAA_MODE", None)

        # TODO: Implement other Auth Methods here

        if contrail_configuration.get('CONFIG_API_PORT', None):
            self.api_server_port = contrail_configuration.get('CONFIG_API_PORT')

        self.api_server_ip = self.calculate_valid_api_server_ip(api_server_list)

        if self.api_server_ip:
            instances_nodes_dict, deleted_nodes_dict = \
                self.discover_contrail_cluster(
                    instances_nodes_dict, deleted_nodes_dict)

        for server in instances_nodes_dict:
            if "instance_roles" not in instances_nodes_dict[server]:
                instances_nodes_dict[server]['instance_roles'] = []
            if "existing_roles" not in instances_nodes_dict[server]:
                instances_nodes_dict[server]['existing_roles'] = []
            instances_nodes_dict[server]['new_roles'] = list(set(
                instances_nodes_dict[server]['instance_roles']
            ).difference(
                set(instances_nodes_dict[server]['existing_roles'])
            ))
            instances_nodes_dict[server]['deleted_roles'] = list(set(
                instances_nodes_dict[server]['existing_roles']
            ).difference(
                set(instances_nodes_dict[server]['instance_roles'])
            ))

        if self.existing_tor_agents:
            for toragent in self.existing_tor_agents.keys():
                server = toragent.split('-')[0]
                tor_agent_id = toragent.split('-')[-1]
                toragent_roles = {}
                toragent_roles[('toragent_' + str(tor_agent_id))] = self.existing_tor_agents[toragent]
                if server in instances_nodes_dict.keys():
                    instances_nodes_dict[server]['existing_roles'].append(toragent_roles)
                elif server not in deleted_nodes_dict:
                    deleted_nodes_dict[server] = self.existing_tor_agents[toragent]['toragent_ip']

        return str({"node_roles_dict": instances_nodes_dict,
                    "deleted_nodes_dict": deleted_nodes_dict,
                    "api_server_ip": self.api_server_ip})

    def extract_roles(self, existing_roles, instance_data):
        existing_roles[instance_data["key"]] = dict()
        if not instance_data["value"]["roles"]:
            return existing_roles

        for role, data in instance_data["value"]["roles"].iteritems():
            ix_name = next((s for s in self.indexed_roles if s in role), None)
            if not ix_name:
                existing_roles[instance_data["key"]][role] = data
            else:
                # indexed role name must be equal to pattern ROLENAME_INDEX
                index = role[len(ix_name) + 1:]
                if index:
                    existing_roles[instance_data["key"]].setdefault(ix_name, dict())[index] = data

        return existing_roles

    def calculate_deleted_toragent_roles(self, cluster_roles_dict, instance_data):
        node_roles_dict = cluster_roles_dict['node_roles_dict']
        deleted_nodes_dict = cluster_roles_dict['deleted_nodes_dict']
        instance_roles = []
        if instance_data["value"]["roles"]:
           instance_roles = instance_data["value"]["roles"].keys()

        for role in node_roles_dict[instance_data['key']]['existing_roles']:
            if isinstance(role, dict):
                for key, value in role.items():
                    if key not in instance_roles:
                        node_roles_dict[instance_data['key']]['deleted_roles'].append(role)

        return str({"node_roles_dict": node_roles_dict,
                    "deleted_nodes_dict": deleted_nodes_dict,
                    "api_server_ip": cluster_roles_dict["api_server_ip"]})

    # Get a list of nodes on which tor agents are running and check if
    # tsn_haproxy is present in cluster
    def get_toragent_nodes(self, instances):
        node_list = []
        tsn_haproxy_enabled = False
        for host in instances.keys():
            roles_dict = instances[host].get('roles', None)
            if roles_dict:
                if [ role for role in roles_dict.keys() if 'toragent' in role]:
                    node_list.append(host)
                elif 'tsn_haproxy' in roles_dict.keys():
                    tsn_haproxy_enabled = True
        return (node_list, tsn_haproxy_enabled)
    #end get_toragent_nodes

    # Given a host_string and tor_name, return the standby tor-agent info
    # identified by indexed toragent role and host-string of where role is installed
    def get_standby_info(self, skip_host, match_tor_name, instances):
        tor_agent_host_list, tsn_haproxy_enabled = self.get_toragent_nodes(instances)
        for host in tor_agent_host_list:
            if host == skip_host:
                continue
            for role in instances[host]['roles'].keys():
                if 'toragent' in role:
                    tor_name= instances[host]['roles'][role].get('TOR_NAME', None)
                    if tor_name == match_tor_name:
                        return (role, host)
        return (None, None)
    #end get_standby_info

    def make_key(self, tsn1, tsn2):
        if tsn1 < tsn2:
            return tsn1 + "-" + tsn2
        return tsn2 + "-" + tsn1

    # Get HA proxy configuration for all TOR agents
    def calculate_tsn_haproxy_config(self, tsn_haproxy_config, instances):

        tor_agent_host_list, tsn_haproxy_enabled = self.get_toragent_nodes(instances)
        # Return empty tsn haproxy config if tsn_haproxy role is not present in cluster
        if not tsn_haproxy_enabled:
            return str({"tsn_haproxy_ip_list": [],
                        "tsn_haproxy_port_list": []})

        master_standby_dict = {}
        tsn_haproxy_ip_list = []
        tsn_haproxy_port_list = []

        for host in tor_agent_host_list:
            for role in instances[host]['roles'].keys():
                if 'toragent' in role:
                    tor_name= instances[host]['roles'][role].get('TOR_NAME', None)
                    tsn1 = instances[host]['roles'][role].get('TOR_TSN_IP', None)
                    port1 = instances[host]['roles'][role].get('TOR_OVS_PORT', None)
                    standby_tor_idx, standby_host = self.get_standby_info(host, tor_name, instances)
                    key = tsn1
                    if (standby_tor_idx != None and standby_host != None):
                        tsn2 = instances[standby_host]['roles'][standby_tor_idx].get('TOR_TSN_IP', None)
                        port2 = instances[standby_host]['roles'][standby_tor_idx].get('TOR_OVS_PORT', None)
                        if port1 == port2:
                            key = self.make_key(tsn1, tsn2)
                        else:
                            raise Exception("Tor Agents (%s, %s) and (%s, %s) \
                                   are configured as redundant agents but don't  \
                                   have same ovs_port" \
                                   %(host, role, standby_host, standby_tor_idx))
                    if not key in master_standby_dict:
                        master_standby_dict[key] = []
                    if not port1 in master_standby_dict[key]:
                        master_standby_dict[key].append(port1)

        for key in master_standby_dict.keys():
            tsn1 = key.split('-')[0]
            tsn2 = key.split('-')[1]
            for ovs_port in master_standby_dict[key]:
                tsn_haproxy_port_list.append(ovs_port)
                tsn_haproxy_ip_list.append(tsn1)
                tsn_haproxy_ip_list.append(tsn2)

        return str({"tsn_haproxy_ip_list": tsn_haproxy_ip_list,
                   "tsn_haproxy_port_list": tsn_haproxy_port_list})
