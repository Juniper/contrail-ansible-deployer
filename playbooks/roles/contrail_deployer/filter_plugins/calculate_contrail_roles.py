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

            for object_to_process in object_list:
                if len(object_to_process.get("fq_name", [])) < 2:
                    continue
                instance_name = str(object_to_process.get("fq_name")[-1])
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
                    deleted_nodes_dict[instance_name] = ip_address
                elif 'instance_roles' not in instances_nodes_dict[
                    instance_name] or \
                        not len(instances_nodes_dict[instance_name][
                                    'instance_roles']):
                    if instance_name not in deleted_nodes_dict:
                        deleted_nodes_dict[instance_name] = \
                            self.node_name_ip_map[instance_name]

                if 'existing_roles' not in instances_nodes_dict[
                    instance_name]:
                    instances_nodes_dict[instance_name][
                        'existing_roles'] = list()
                instances_nodes_dict[instance_name][
                    'existing_roles'].append(contrail_role)

        return instances_nodes_dict, deleted_nodes_dict

    def calculate_contrail_roles(self, existing_dict, api_server_list,
                                 hostvars):
        # don't calculate anything if global_configuration.ENABLE_DESTROY is not set
        gc = hostvars.get("global_configuration")
        if not gc:
            return
        enable_destroy = gc.get("ENABLE_DESTROY", False)
        if not isinstance(enable_destroy, bool):
            enable_destroy = str(enable_destroy).lower() == 'true'
        if not enable_destroy:
            return str({"node_roles_dict": dict(),
                        "deleted_nodes_dict": dict(),
                        "api_server_ip": None})

        instances_nodes_dict = {}
        deleted_nodes_dict = {}
        invalid_role = None
        cluster_role_set = set()

        if hostvars.get("instances", None):
            instances_dict = hostvars["instances"]
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

        if hostvars.get("contrail_configuration", None):
            contrail_config = hostvars["contrail_configuration"]
            # Check if Controller Nodes was given
            if contrail_config.get('CONFIG_NODES', None):
                controller_node_list = contrail_config.get(
                    'CONFIG_NODES').split(',')
            elif contrail_config.get('CONTROLLER_NODES', None):
                controller_node_list = contrail_config.get(
                    'CONTROLLER_NODES').split(',')
            else:
                controller_node_list = None
            if isinstance(controller_node_list, list) and \
                    len(controller_node_list):
                api_server_list = controller_node_list
            else:
                api_server_list = []

            if contrail_config.get("CLOUD_ORCHESTRATOR",None) == "openstack":
                self.auth_token = self.get_ks_auth_token(contrail_config)
                self.aaa_mode = contrail_config.get("AAA_MODE", None)

            # TODO: Implement other Auth Methods here

            if contrail_config.get('CONFIG_API_PORT', None):
                self.api_server_port = contrail_config.get('CONFIG_API_PORT')

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

        return str({"node_roles_dict": instances_nodes_dict,
                    "deleted_nodes_dict": deleted_nodes_dict,
                    "api_server_ip": self.api_server_ip})

    def extract_roles(self, existing_roles, instance_data):
        existing_roles[instance_data["key"]] = dict()
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
