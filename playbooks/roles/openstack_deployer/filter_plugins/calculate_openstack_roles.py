#!/usr/bin/python

"""
This filter plugin script takes instances file as input and
returns lists of new roles, existing roles, deleted roles and instances roles
for all the Openstack nodes in the instances file.
"""
import requests
import json


class FilterModule(object):

    keystone_auth_host = ""
    keystone_admin_password = ""
    keystone_auth_url_version = "/v2.0"

    auth_token = None
    aaa_mode = None
    node_name_ip_map = {}
    node_ip_name_map = {}

    endpoint_port_role_map = {
        "5000": "control",
        "9696": "network",
        "8776": "storage",
        "3000": "monitoring",
        "8774": "compute"
    }
    openstack_controller_roles = [
        "openstack_control", "openstack_network", "openstack_storage",
        "openstack_monitoring"
    ]

    valid_roles = [
        "openstack_control", "openstack_network", "openstack_storage",
        "openstack_monitoring", "openstack_compute", "openstack"
    ]

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
        keystone_endpoint_url = 'http://' + str(self.keystone_auth_host) + \
                                ':35357' + str(self.keystone_auth_url_version) \
                                + '/endpoints'
        try:
            response = self.get_rest_api_response(keystone_auth_url,
                                                  self.keystone_auth_headers,
                                                  data=json.dumps(
                                                    self.get_ks_token_request()
                                                  ),
                                                  request_type="post")
            # Check if endpoint URL is also reachable
            # To protect against re-run after failed provision

            endpoint_response = self.get_rest_api_response(
                keystone_endpoint_url,
                self.keystone_auth_headers,
                request_type="get")
        except Exception as e:
            auth_token = None
        else:
            header = response.headers
            token = header['X-Subject-Token']
            auth_token = token
        return auth_token

    def filters(self):
        return {
            'calculate_openstack_roles': self.calculate_openstack_roles
        }

    def get_ops_hostname(self, ip_address):
        return "fqdn"

    def get_rest_api_response(self, url, headers, data=None, request_type=None):
        response = None
        if request_type == "post":
            response = requests.post(url, headers=headers, data=data)
        elif request_type == "get":
            response = requests.get(url, headers=headers, data=data)
        response.raise_for_status()
        return response

    def discover_openstack_computes(self,instances_nodes_dict,
                                    deleted_nodes_dict):
        # Read Openstack Computes
        keystone_auth_url = 'http://' + str(self.keystone_auth_host) + \
                            ':8774/v2.1/os-hypervisors/detail'
        try:
            response = self.get_rest_api_response(
                keystone_auth_url,
                self.keystone_auth_headers,
                request_type="get")
        except Exception as e:
            raise e
        else:
            response_dict = response.json()
            if "hypervisors" in response_dict:
                for hyp in response_dict["hypervisors"]:
                    if hyp["host_ip"] in self.node_ip_name_map:
                        server_name = self.node_ip_name_map[hyp["host_ip"]]
                        if "existing_roles" not \
                                in instances_nodes_dict[server_name]:
                            instances_nodes_dict[server_name][
                                'existing_roles'] = []
                        instances_nodes_dict[server_name][
                            'existing_roles'].append("openstack_compute")
                    else:
                        hostname = hyp["hypervisor_hostname"].split('.')[0]
                        deleted_nodes_dict[hostname] = hyp["host_ip"]
            return instances_nodes_dict, deleted_nodes_dict

    def discover_openstack_controllers(self, instances_nodes_dict,
                                    deleted_nodes_dict):
        # Read Openstack Controllers
        keystone_auth_url = 'http://' + str(self.keystone_auth_host) + \
                            ':35357' + str(self.keystone_auth_url_version) \
                            + '/endpoints'
        try:
            response = self.get_rest_api_response(
                keystone_auth_url,
                self.keystone_auth_headers,
                request_type="get")
        except Exception as e:
            raise e
        else:
            response_dict = response.json()
            if "endpoints" in response_dict:
                for endpoint_dict in response_dict["endpoints"]:
                    endpoint_ip = endpoint_dict["publicurl"].strip(
                        "http://").split(":")
                    endpoint_ip, endpoint_port = endpoint_ip
                    endpoint_port = endpoint_port.split("/")[0]
                    if endpoint_port in self.endpoint_port_role_map:
                        openstack_role = "openstack_" + \
                                         self.endpoint_port_role_map[
                                             endpoint_port]
                        if endpoint_ip in self.node_ip_name_map:
                            server_name = self.node_ip_name_map[endpoint_ip]
                            if "existing_roles" not \
                                    in instances_nodes_dict[server_name]:
                                instances_nodes_dict[server_name][
                                    'existing_roles'] = []
                            instances_nodes_dict[server_name][
                                'existing_roles'].append(openstack_role)
                        else:
                            # TODO: Implement
                            deleted_server_name = self.get_ops_hostname(
                                endpoint_ip
                            )
                            deleted_nodes_dict[deleted_server_name] = \
                                endpoint_ip
            return instances_nodes_dict, deleted_nodes_dict

    def calculate_openstack_roles(self, existing_dict,
            instances_dict, global_configuration, contrail_configuration):
        # don't calculate anything if global_configuration.ENABLE_DESTROY is not set
        empty_result = {"node_roles_dict": dict(),
                        "deleted_nodes_dict": dict()}
        enable_destroy = global_configuration.get("ENABLE_DESTROY", False)
        if not isinstance(enable_destroy, bool):
            enable_destroy = str(enable_destroy).lower() == 'true'
        if not enable_destroy:
            return str(empty_result)

        instances_nodes_dict = {}
        deleted_nodes_dict = {}
        valid_cluster_node_lists = "yes"
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

        if contrail_configuration.get("CLOUD_ORCHESTRATOR") == "openstack":
            self.auth_token = self.get_ks_auth_token(contrail_configuration)
            self.aaa_mode = contrail_configuration.get("AAA_MODE", None)

        if self.auth_token:
            if self.aaa_mode != "no-auth":
                self.keystone_auth_headers['X-Auth-Token'] = self.auth_token
            try:
                instances_nodes_dict, deleted_nodes_dict = \
                    self.discover_openstack_computes(instances_nodes_dict,
                                                     deleted_nodes_dict)
                instances_nodes_dict, deleted_nodes_dict = \
                    self.discover_openstack_controllers(instances_nodes_dict,
                                                        deleted_nodes_dict)
            except Exception as e:
                return str({"Exception": e.message})

        for server in instances_nodes_dict:
            for role_list, list_of_roles in \
                    instances_nodes_dict[server].iteritems():
                if len(list_of_roles) and "openstack" in list_of_roles:
                    list_of_roles.remove("openstack")
                    list_of_roles += self.openstack_controller_roles
                    instances_nodes_dict[server][role_list] = list_of_roles

            if "instance_roles" not in instances_nodes_dict[server]:
                instances_nodes_dict[server]['instance_roles'] = []
            if "existing_roles" not in instances_nodes_dict[server]:
                instances_nodes_dict[server]['existing_roles'] = []
            else:
                instances_nodes_dict[server]['existing_roles'] =\
                    list(set(instances_nodes_dict[server]['existing_roles']))

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

            if len(instances_nodes_dict[server]['deleted_roles']) and\
                    (instances_nodes_dict[server]['deleted_roles'] ==
                         instances_nodes_dict[server]['existing_roles']):
                deleted_nodes_dict[server] = self.node_name_ip_map[server]

        return str({"node_roles_dict": instances_nodes_dict,
                    "deleted_nodes_dict": deleted_nodes_dict})
