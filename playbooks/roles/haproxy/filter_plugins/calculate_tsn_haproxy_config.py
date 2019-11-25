#!/usr/bin/env python

"""
Filter to calculate port list and ip list
for tsn haproxy container
"""

class FilterModule(object):
    instances = {}
    contrail_configuration = {}
    toragent_hosts_list = []

    def filters(self):
        return {
            'calculate_tsn_haproxy_config': self.calculate_tsn_haproxy_config
        }

    # Get value for env variable for a role on a given host
    def get_env_value_for_role(self, host, role, key):
        if self.instances[host]['roles'][role].get(key, None):
            return self.instances[host]['roles'][role].get(key)
        elif (self.instances[host]['contrail_configuration'] and
              self.instances[host]['contrail_configuration'].get(key, None)):
            return self.instances[host]['contrail_configuration'].get(key)
        elif self.contrail_configuration:
            return self.contrail_configuration.get(key, None)

        return None

    # Given a host_string and tor_name, return the standby tor-agent info
    # identified by indexed toragent role and host-string of where role is installed
    def get_standby_info(self, skip_host, match_tor_name):
        for host in self.toragent_hosts_list:
            if host == skip_host:
                continue
            for role in self.instances[host]['roles']:
                if 'toragent' not in role:
                    continue
                tor_name = self.get_env_value_for_role(host, role, 'TOR_NAME')
                if tor_name == match_tor_name:
                    return (role, host)
        return (None, None)
    #end get_standby_info

    def make_key(self, tsn1, tsn2):
        if tsn1 < tsn2:
            return tsn1 + "-" + tsn2
        return tsn2 + "-" + tsn1

    # Get HA proxy configuration for all TOR agents
    def calculate_tsn_haproxy_config(self, tsn_haproxy_config, toragent_hosts_list, instances, contrail_configuration):
        self.instances = instances
        self.contrail_configuration = contrail_configuration
        self.toragent_hosts_list = toragent_hosts_list
        master_standby_dict = {}
        tsn_haproxy_ip_list = []
        tsn_haproxy_port_list = []

        for host in toragent_hosts_list:
            for role in instances[host]['roles']:
                if 'toragent' not in role:
                    continue
                tor_name= self.get_env_value_for_role(host, role, 'TOR_NAME')
                tsn1 = self.get_env_value_for_role(host, role, 'TOR_TSN_IP')
                port1 = self.get_env_value_for_role(host, role, 'TOR_OVS_PORT')
                standby_tor_idx, standby_host = self.get_standby_info(host, tor_name)
                key = tsn1
                if (standby_tor_idx != None and standby_host != None):
                    tsn2 = self.get_env_value_for_role(standby_host, standby_tor_idx, 'TOR_TSN_IP')
                    port2 = self.get_env_value_for_role(standby_host, standby_tor_idx, 'TOR_OVS_PORT')
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
        for key in master_standby_dict:
            tsn1 = key.split('-')[0]
            tsn2 = key.split('-')[1]
            for ovs_port in master_standby_dict[key]:
                tsn_haproxy_port_list.append(ovs_port)
                tsn_haproxy_ip_list.append(tsn1)
                tsn_haproxy_ip_list.append(tsn2)

        return str({"IP_LIST": tsn_haproxy_ip_list,
                   "PORT_LIST": tsn_haproxy_port_list})
