#!/usr/bin/python

from ansible.errors import AnsibleFilterError
import ipaddress

class FilterModule(object):
    def filters(self):
        return {
            'ctrl_data_intf_dict': self.ctrl_data_intf_dict,
            'mgmt_intf_dict': self.mgmt_intf_dict
        }

    # Utility Function
    @staticmethod
    def get_host_ctrl_data_nw_if(my_ip, my_vars, cidr):
        ctrl_data_nw = ipaddress.ip_network(cidr)
        for iface in my_vars.get('ansible_interfaces',[]):
            if_str = 'ansible_' + iface
            if_ipv4 = my_vars.get(if_str, {}).get('ipv4', None)
            if if_ipv4 and \
                    ipaddress.ip_address(if_ipv4['network']) == \
                    ctrl_data_nw.network_address:
                return iface
        return None

    # Precedence 0 (least)
    @staticmethod
    def get_default_intf(hostvars, v):
        return hostvars.get(v['ip'], {}).get('ansible_default_ipv4',
                {}).get('interface', 'no_network_intf')

    # Precedence 1
    @staticmethod
    def get_intf_from_ctrl_data_net_list(in_intf, contrail_config, hostvars, v):
        subnet_list = None
        subnet_list_str = contrail_config.get('CONTROL_DATA_NET_LIST', None)
        if subnet_list_str:
            subnet_list = subnet_list_str.split(',')
        if subnet_list:
            for subnet in subnet_list:
                tmp_intf = FilterModule.get_host_ctrl_data_nw_if(v['ip'],
                        hostvars.get(v['ip'], {}), subnet)
                if tmp_intf != None:
                    return tmp_intf
        return in_intf

    # Precedence 2
    @staticmethod
    def get_intf_from_service_nodes(in_intf, contrail_config):
        service_nodes = contrail_config.get('CONFIG_NODES',
                contrail_config.get('CONTROL_NODES',
                    contrail_config.get('CONTROLLER_NODES', None)))
        if service_nodes == None:
            return in_intf

        node_ip = service_nodes.split(',')[0]
        intf = rt_output.split(' ')[2]
        return intf

    # Precedence 3
    @staticmethod
    def get_intf_from_kolla_config(in_intf, kolla_config, inst_value):
        if inst_value.get('roles', None) == None or \
                'openstack' in inst_value.get('roles', {}).keys():
            kolla_globals = kolla_config.get('kolla_globals', {})
            return kolla_globals.get('network_interface', in_intf)
        return in_intf

    # Precedence 255 (highest)
    @staticmethod
    def get_intf_from_roles(in_intf, inst_value):
        for i,j in inst_value.get('roles', {}).iteritems():
            if j is not None:
                tmp_intf = j.get('network_interface', None)
                if tmp_intf != None:
                    return tmp_intf
        return in_intf


    # Tries to detect control-data-intf for each host in the instances
    # definition. The host specific 'network_interface' takes the highest
    # precedence. Next, CONTROL_DATA_NET_LIST if defined (could be a list of
    # comma separated CIDR subnet definitions) will be used to pick the
    # interface corresponding to the IP address on each host that falls within
    # this subnet range.
    def ctrl_data_intf_dict(self, instances, contrail_config,
                            kolla_config, hostvars):
        host_intf = {}
        for k,v in instances.iteritems():

            nw_intf = FilterModule.get_default_intf(hostvars, v)
            nw_intf = FilterModule.get_intf_from_ctrl_data_net_list(nw_intf,
                    contrail_config, hostvars, v)
            nw_intf = FilterModule.get_intf_from_service_nodes(nw_intf,
                    contrail_config)
            nw_intf = FilterModule.get_intf_from_kolla_config(nw_intf,
                    kolla_config, v)
            nw_intf = FilterModule.get_intf_from_roles(nw_intf, v)

            host_intf[v['ip']] = nw_intf

        return host_intf

    def mgmt_intf_dict(self, instances, contrail_config,
                            kolla_config, hostvars):
        host_intf = {}
        kolla_globals = kolla_config.get('kolla_globals', {})
        for k,v in instances.iteritems():
            for i in hostvars.get(v['ip'], {}).get('ansible_interfaces', []):
                if_str = 'ansible_' + i
                if_ipv4 = hostvars[v['ip']].get(if_str, {}).get('ipv4', None)
                if if_ipv4 and if_ipv4.get('address', None) == v['ip']:
                    host_intf[v['ip']] = i

            tmp_intf = kolla_globals.get('kolla_external_vip_interface', None)
            if tmp_intf != None:
                host_intf[v['ip']] = tmp_intf

            for i,j in v.get('roles', {}).iteritems():
                if j is not None:
                    tmp_intf = j.get('kolla_external_vip_interface', None)
                    if tmp_intf != None:
                        host_intf[v['ip']] = tmp_intf

        return host_intf
