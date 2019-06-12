#!/usr/bin/python

"""
This filter plugin script takes instances file as input and
returns lists of new roles, existing roles, deleted roles and instances roles
for all the Openstack nodes in the instances file.
"""
import requests
import json

# class that handles parameters required to talk to openstack and detect
# existing roles
class OpenStackParams:

    # static params
    endpoint_port_role_map = {
        "5000": "control",
        "9696": "network",
        "8776": "storage",
        "3000": "monitoring",
        "8774": "compute"
    }

    ks_auth_url_endpoint_dict = {
        "/v3": "/auth/tokens",
        "/v2.0": "/auth/tokens"
    }

    openstack_controller_roles = [
        "openstack_control", "openstack_network", "openstack_storage",
        "openstack_monitoring"
    ]

    # Non-static data
    ks_auth_headers = {
        'Content-Type': 'application/json'
    }

    ks_auth_url = None
    os_hypervisors_url = None
    os_endpoints_url = None

    ks_auth_host = None
    ks_admin_password = ""
    ks_admin_tenant = ""
    ks_admin_user   = ""
    ks_auth_url_version = "/v3" # default for openstack queens is "/v3"
    auth_token = None
    aaa_mode = None

    def __init__(self, contrail_config, kolla_config):
        self.ks_auth_host = contrail_config.get("KEYSTONE_AUTH_HOST", None)
        if kolla_config is not None and kolla_config.get("kolla_globals"):
            self.ks_auth_host = kolla_config["kolla_globals"].get("kolla_external_vip_address",
                    self.ks_auth_host)
            if kolla_config["kolla_globals"].get("kolla_enable_tls_external", None):
                self.ks_auth_proto = "https://"
            else:
                self.ks_auth_proto = "http://"
        self.ks_admin_user = contrail_config.get(
            "KEYSTONE_AUTH_ADMIN_USER", "admin")
        self.ks_admin_password = contrail_config.get(
            "KEYSTONE_AUTH_ADMIN_PASSWORD", "contrail123")
        self.ks_admin_tenant = contrail_config.get(
            "KEYSTONE_AUTH_ADMIN_TENANT", "admin")
        self.ks_auth_url_version = contrail_config.get(
            "KEYSTONE_AUTH_URL_VERSION",
            "/v3")
        ks_tokens_url = self.ks_auth_url_endpoint_dict.get(self.ks_auth_url_version,
                self.ks_auth_url_endpoint_dict["/v3"])

        # TODO: Add support for https and non-default port
        if self.ks_auth_host:
            self.ks_auth_url = str(self.ks_auth_proto) + str(self.ks_auth_host) + \
                ':5000/v3' +\
                str(ks_tokens_url)
            self.os_endpoints_url = str(self.ks_auth_proto) + \
                                    str(self.ks_auth_host) + \
                                    ':5000' + str(self.ks_auth_url_version) \
                                    + '/endpoints'
            self.os_hypervisors_url = str(self.ks_auth_proto) + \
                                str(self.ks_auth_host) + \
                                ':8774/v2.1/os-hypervisors/detail'

        if contrail_config.get("CLOUD_ORCHESTRATOR") == "openstack":
            self.get_ks_auth_token(contrail_config)
            self.aaa_mode = contrail_config.get("AAA_MODE", None)


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
                                'id': 'default'
                            },
                            'name': self.ks_admin_user,
                            'password': self.ks_admin_password
                        }
                    }
                },
                'scope': {
                    'project': {
                        'domain': {
                            'name': 'default'
                        },
                        'name':  self.ks_admin_tenant
                    }
                }
            }
        }

        keystone_v2_token_request = {
        }
        return keystone_token_request

    def get_ks_auth_token(self, contrail_config):
        try:
            response = self.get_rest_api_response(self.ks_auth_url,
                                                  self.ks_auth_headers,
                                                  data=json.dumps(
                                                    self.get_ks_token_request()
                                                  ),
                                                  request_type="post")
        except Exception as e:
            self.auth_token = None
        else:
            header = response.headers
            self.auth_token = header['X-Subject-Token']
            if self.aaa_mode != "no-auth":
                self.ks_auth_headers['X-Auth-Token'] = self.auth_token

            try:
                # Check if endpoint URL is also reachable
                # To protect against re-run after failed provision
                endpoint_response = self.get_os_endpoints()
            except Exception as e:
                self.auth_token = None

    def get_rest_api_response(self, url, headers, data=None, request_type=None):
        response = None
        if request_type == "post":
            response = requests.post(url, headers=headers, data=data)
        elif request_type == "get":
            response = requests.get(url, headers=headers, data=data)
        response.raise_for_status()
        return response

    def get_os_hypervisors(self):
        return self.get_rest_api_response(
                self.os_hypervisors_url,
                self.ks_auth_headers,
                request_type="get")

    def get_os_endpoints(self):
        return self.get_rest_api_response(
                self.os_endpoints_url,
                self.ks_auth_headers,
                request_type="get")


class OpenstackCluster(object):
    # OpenStackParams object
    os_params = None
    e = None

    node_name_ip_map = {}
    node_ip_name_map = {}
    valid_roles = [
        "openstack_control", "openstack_network", "openstack_storage",
        "openstack_monitoring", "openstack_compute", "openstack"
    ]


    def __init__(self, instances, contrail_configuration, kolla_config):
        # Initialize the openstack params
        self.os_params = OpenStackParams(contrail_configuration, kolla_config)
        self.instances_dict = instances

    def discover_openstack_roles(self):
        instances_nodes_dict = {}
        deleted_nodes_dict = {}
        valid_cluster_node_lists = "yes"
        invalid_role = None
        cluster_role_set = set()

        for instance_name, instance_config in self.instances_dict.iteritems():
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

        try:
            instances_nodes_dict, deleted_nodes_dict = \
                self.discover_openstack_computes(instances_nodes_dict,
                                                 deleted_nodes_dict)
            #instances_nodes_dict, deleted_nodes_dict = \
            #    self.discover_openstack_controllers(instances_nodes_dict,
            #                                        deleted_nodes_dict)
        except Exception as e:
            return dict(), dict()

        for server in instances_nodes_dict:
            for role_list, list_of_roles in \
                    instances_nodes_dict[server].iteritems():
                if len(list_of_roles) and "openstack" in list_of_roles:
                    list_of_roles.remove("openstack")
                    list_of_roles += self.os_params.openstack_controller_roles
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

        self.node_roles_dict = instances_nodes_dict
        self.deleted_nodes_dict = deleted_nodes_dict
        return instances_nodes_dict, deleted_nodes_dict

    def get_ops_hostname(self, ip_address):
        return "fqdn"

    def discover_openstack_computes(self,instances_nodes_dict,
                                    deleted_nodes_dict):
        # Read Openstack Computes
        try:
            response = self.os_params.get_os_hypervisors()
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
        try:
            response = self.os_params.get_os_endpoints()
        except Exception as e:
            raise e
        else:
            response_dict = response.json()
            if "endpoints" in response_dict:
                for endpoint_dict in response_dict["endpoints"]:
                    endpoint_ip = endpoint_dict["url"].strip(
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


class FilterModule(object):

    # OpenstackCluster object
    os_roles = None

    def filters(self):
        return {
            'calculate_openstack_roles': self.calculate_openstack_roles
        }

    def calculate_openstack_roles(self, existing_dict,
            instances_dict, global_configuration, contrail_configuration,
            kolla_config):
        # don't calculate anything if global_configuration.ENABLE_DESTROY is not set
        empty_result = {"node_roles_dict": dict(),
                        "deleted_nodes_dict": dict()}
        enable_destroy = global_configuration.get("ENABLE_DESTROY", True)
        if not isinstance(enable_destroy, bool):
            enable_destroy = str(enable_destroy).lower() == 'true'
        if not enable_destroy:
            return str(empty_result)

        self.os_roles = OpenstackCluster(instances_dict, contrail_configuration,
                kolla_config)
        instances_nodes_dict, deleted_nodes_dict = \
                self.os_roles.discover_openstack_roles()
        if self.os_roles.e is not None:
            return str({"Exception": self.os_roles.e})

        return str({"node_roles_dict": instances_nodes_dict,
                    "deleted_nodes_dict": deleted_nodes_dict})

