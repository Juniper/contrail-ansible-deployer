#!/usr/bin/python
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
    node_name_ip_map = {}
    node_ip_name_map = {}

    valid_roles = ["config", "control", "analytics_database",
                   "analytics", "vrouter"]

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
        "analytics-nodes": "analytics"
    }

    ip_role_map = {
        "virtual-routers": "virtual_router_ip_address",
        "config-nodes": "config_node_ip_address",
        "database-nodes": "database_node_ip_address",
        "bgp-routers": "bgp_router_parameters.address",
        "analytics-nodes": "analytics_node_ip_address"
    }

    def filters(self):
        return {
            'calculate_contrail_roles': self.calculate_contrail_roles
        }

    def calculate_valid_api_server_ip(self, api_server_list, auth_token):
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
        try:
            response = self.get_rest_api_response(node_url,
                                                  self.contrail_auth_headers,
                                                  request_type="get")
        except Exception as e:
            raise e
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

    def calculate_contrail_roles(self, existing_dict, hostvars):
        instances_nodes_dict = {}
        deleted_nodes_dict = {}
        valid_cluster_node_lists = "yes"
        role_server_dict = {}
        invalid_role = None
        cluster_role_set = set()
        api_server_list = None

        for role in self.valid_roles:
            role_server_dict[role] = None

        for k,v in hostvars.iteritems():

            if k == "instances":
                instances_dict = v
                for instance_name, instance_config in instances_dict.iteritems():
                    instances_nodes_dict[instance_name] = {}
                    self.node_name_ip_map[instance_name] = instance_config["ip"]
                    self.node_ip_name_map[instance_config["ip"]] = instance_name
                    instances_nodes_dict[instance_name]['instance_roles'] = \
                        list(set(instance_config["roles"].keys()).intersection(set(self.valid_roles)))
                    cluster_role_set.update(instance_config["roles"].keys())
            elif k == "contrail_configuration":
                contrail_config = v

                # Check if Controller Nodes was given
                controller_role_list = contrail_config.get('CONTROLLER_NODES', None).split(' ')

                for config_key, config_value in contrail_config.iteritems():
                    if "_NODES" in config_key:
                        contrail_role = config_key.strip('_NODES').lower()
                        contrail_role_list = config_value.split(' ')
                        if contrail_role in self.valid_roles:
                            role_server_dict[contrail_role] = contrail_role_list
                            if len(contrail_role_list) and (len(contrail_role_list) % 2) != 1:
                                valid_cluster_node_lists = "no"
                                invalid_role = contrail_role

                for role in cluster_role_set:
                    if role in self.valid_roles and not role_server_dict[role]:
                        role_server_dict[role] = controller_role_list

                api_server_list = role_server_dict["config"]

                if "AUTH_MODE" in v and v["AUTH_MODE"] == "keystone":
                    self.keystone_auth_host = v.get("KEYSTONE_AUTH_HOST","")
                    self.keystone_admin_password = v.get("KEYSTONE_AUTH_ADMIN_PASSWORD","")
                    keystone_auth_url_version = v.get("KEYSTONE_AUTH_URL_VERSION","")
                    keystone_auth_url = 'http://' + str(self.keystone_auth_host) + ':35357' + \
                                        str(keystone_auth_url_version) + '/auth/tokens'
                    try:
                        response = self.get_rest_api_response(keystone_auth_url,
                                                              self.keystone_auth_headers,
                                                              data=json.dumps(
                                                                  self.get_ks_token_request()
                                                              ),
                                                              request_type="post")
                    except Exception as e:
                        self.auth_token = None
                    else:
                        header = response.headers
                        token = header['X-Subject-Token']
                        self.auth_token = token

                # TODO: Implement other Auth Methods here

                if v.get('CONFIG_API_PORT', None):
                    self.api_server_port = v.get('CONFIG_API_PORT')

        if valid_cluster_node_lists == "no":
            return str(
                {
                    "Exception":
                        "There are an invalid number of contrail nodes for a role in this cluster: " +\
                        invalid_role
                 }
            )

        if api_server_list:
            self.api_server_ip = \
                self.calculate_valid_api_server_ip(api_server_list,
                                                   self.auth_token)

        if self.auth_token and self.api_server_ip:
            self.contrail_auth_url = 'http://' + str(self.api_server_ip) + ':' + str(self.api_server_port) + '/'
            self.contrail_auth_headers['X-Auth-Token'] = self.auth_token

            for contrail_object, contrail_role in self.contrail_object_map.iteritems():
                contrail_object_url = self.contrail_auth_url + str(contrail_object)
                try:
                    response = self.get_rest_api_response(contrail_object_url,
                                                          self.contrail_auth_headers,
                                                          request_type="get")
                except Exception as e:
                    return str({"Exception": e.message})
                object_dict = response.json()
                object_list = object_dict[contrail_object]

                for object_to_process in object_list:
                    if len(object_to_process.get("fq_name",[])) >= 2:
                        instance_name = str(object_to_process.get("fq_name")[-1])
                        uuid = str(object_to_process.get("uuid"))
                        try:
                            ip_address = self.get_ip_for_contrail_node(instance_name,
                                                                       uuid,
                                                                       contrail_object,
                                                                       self.contrail_auth_url,
                                                                       self.contrail_auth_headers)
                        except Exception as e:
                            return str({"Exception": e.message})
                        if instance_name not in instances_nodes_dict:
                            instances_nodes_dict[instance_name] = {}
                            deleted_nodes_dict[instance_name] = ip_address
                        if 'existing_roles' not in instances_nodes_dict[instance_name]:
                            instances_nodes_dict[instance_name]['existing_roles'] = list()
                        instances_nodes_dict[instance_name]['existing_roles'].append(contrail_role)

        re_provision = "yes"

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

            if len(instances_nodes_dict[server]['new_roles']) != 0 \
                    or len(instances_nodes_dict[server]['deleted_roles']) != 0:
                re_provision = "no"

        return str({"node_roles_dict": instances_nodes_dict,
                    "deleted_nodes_dict": deleted_nodes_dict,
                    "api_server_ip": self.api_server_ip,
                    "reprovision": re_provision})
