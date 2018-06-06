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
            cur_ip = v['ip']

            # try to find instance specific value
            for i,j in v.get('roles', {}).iteritems():
                if j is None:
                    continue
                tmp_intf = j.get('kolla_external_vip_interface', None)
                if tmp_intf != None:
                    host_intf[cur_ip] = tmp_intf
                    break
            if host_intf.get(cur_ip):
                continue

            # then try to get global value
            tmp_intf = kolla_globals.get('kolla_external_vip_interface', None)
            if tmp_intf != None:
                host_intf[cur_ip] = tmp_intf
                continue

            # TODO: here must be derivation from kolla_external_vip_address if it is set
            # if kolla_external_vip_address is not set then this interface is not needed

            # TODO: this is not correct and must be removed
            for i in hostvars.get(cur_ip, {}).get('ansible_interfaces', []):
                if_str = 'ansible_' + i
                if_ipv4 = hostvars[cur_ip].get(if_str, {}).get('ipv4', None)
                if if_ipv4 and if_ipv4.get('address', None) == cur_ip:
                    host_intf[cur_ip] = i

        return host_intf
