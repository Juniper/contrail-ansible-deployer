#!/usr/bin/python

from ansible.errors import AnsibleFilterError
import ipaddress

class FilterModule(object):
    def filters(self):
        return {
            'kolla_external_intf_dict': self.kolla_external_intf_dict
        }

    def kolla_external_intf_dict(self, instances, contrail_config,
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
