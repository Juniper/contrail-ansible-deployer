#!/usr/bin/python

from ansible.errors import AnsibleFilterError
import ipaddress

class FilterModule(object):
    def filters(self):
        return {
            'ctrl_data_intf_dict': self.ctrl_data_intf_dict
        }

    @staticmethod
    def get_host_ctrl_data_nw_if(my_ip, my_vars, cidr):
        ctrl_data_nw = ipaddress.ip_network(cidr)
        for iface in my_vars['ansible_interfaces']:
            if_str = 'ansible_' + iface
            if_ipv4 = my_vars.get(if_str).get('ipv4', None)
            if if_ipv4 and ipaddress.ip_address(if_ipv4['network']) == ctrl_data_nw.network_address:
                return iface
        return None

    def ctrl_data_intf_dict(self, instances, contrail_config,
                            kolla_config, hostvars):
        host_intf = {}
        kolla_globals = kolla_config.get('kolla_globals', {})
        for k,v in instances.iteritems():
            tmp_intf = contrail_config.get('PHYSICAL_INTERFACE', \
                    kolla_globals.get('network_interface', None))
            if tmp_intf != None:
                host_intf[v['ip']] = tmp_intf

            if contrail_config.get('CTRL_DATA_NETWORK'):
                tmp_intf = FilterModule.get_host_ctrl_data_nw_if(v['ip'], hostvars[v['ip']],
                        contrail_config.get('CTRL_DATA_NETWORK'))
                if tmp_intf != None:
                    host_intf[v['ip']] = tmp_intf

            for i,j in v.get('roles', {}).iteritems():
                if j is not None:
                    tmp_intf = j.get('PHYSICAL_INTERFACE', \
                            j.get('network_interface', None))
                    if tmp_intf != None:
                        host_intf[v['ip']] = tmp_intf

        return host_intf
