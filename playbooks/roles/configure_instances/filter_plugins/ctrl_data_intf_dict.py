#!/usr/bin/python

from ansible.errors import AnsibleFilterError

class FilterModule(object):
    def filters(self):
        return {
            'ctrl_data_intf_dict': self.ctrl_data_intf_dict
        }

    def ctrl_data_intf_dict(self, instances, contrail_config, kolla_config):
        host_intf = {}
        kolla_globals = kolla_config.get('kolla_globals', {})
        for k,v in instances.iteritems():
            tmp_intf = contrail_config.get('PHYSICAL_INTERFACE', \
                    kolla_globals.get('network_interface', None))
            if tmp_intf != None:
                host_intf[v['ip']] = tmp_intf

            for i,j in v.get('roles', {}).iteritems():
                if j is not None:
                    tmp_intf = j.get('PHYSICAL_INTERFACE', \
                            j.get('network_interface', None))
                    if tmp_intf != None:
                        host_intf[v['ip']] = tmp_intf

        return host_intf
