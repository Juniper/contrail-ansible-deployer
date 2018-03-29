#!/usr/bin/python

from ansible.errors import AnsibleFilterError
import ipaddress

class FilterModule(object):
    def filters(self):
        return {
            'ctrl_data_intf_dict': self.ctrl_data_intf_dict,
            'mgmt_intf_dict': self.mgmt_intf_dict
        }

    @staticmethod
    def get_host_ctrl_data_nw_if(my_ip, my_vars, cidr):
        ctrl_data_nw = ipaddress.ip_network(cidr)
        for iface in my_vars.get('ansible_interfaces',[]):
            if_str = 'ansible_' + iface
            if_ipv4 = my_vars.get(if_str).get('ipv4', None)
            if if_ipv4 and \
                    ipaddress.ip_address(if_ipv4['network']) == \
                    ctrl_data_nw.network_address:
                return iface
        return None

    # Tries to detect control-data-intf for each host in the instances
    # definition. The host specific 'network_interface' takes the highest
    # precedence. Next, CONTROL_DATA_NET_LIST if defined (could be a list of
    # comma separated CIDR subnet definitions) will be used to pick the
    # interface corresponding to the IP address on each host that falls within
    # this subnet range.
    def ctrl_data_intf_dict(self, instances, contrail_config,
                            kolla_config, hostvars):
        host_intf = {}
        kolla_globals = kolla_config.get('kolla_globals', {})
        for k,v in instances.iteritems():
            tmp_intf = kolla_globals.get('network_interface', None)
            if tmp_intf != None:
                host_intf[v['ip']] = tmp_intf

            subnet_list = None
            subnet_list_str = contrail_config.get('CONTROL_DATA_NET_LIST', None)
            if subnet_list_str:
                subnet_list = subnet_list_str.split(',')
            if subnet_list:
                for subnet in subnet_list:
                    tmp_intf = FilterModule.get_host_ctrl_data_nw_if(v['ip'],
                            hostvars.get(v['ip'], {}), subnet)
                    if tmp_intf != None:
                        host_intf[v['ip']] = tmp_intf
                        break

            for i,j in v.get('roles', {}).iteritems():
                if j is not None:
                    tmp_intf = j.get('network_interface', None)
                    if tmp_intf != None:
                        host_intf[v['ip']] = tmp_intf

        return host_intf

    def mgmt_intf_dict(self, instances, contrail_config,
                            kolla_config, hostvars):
        host_intf = {}
        kolla_globals = kolla_config.get('kolla_globals', {})
        for k,v in instances.iteritems():
            for i in hostvars.get(v['ip'], {}).get('ansible_interfaces', []):
                if_str = 'ansible_' + i
                if_ipv4 = hostvars[v['ip']].get(if_str).get('ipv4', None)
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
