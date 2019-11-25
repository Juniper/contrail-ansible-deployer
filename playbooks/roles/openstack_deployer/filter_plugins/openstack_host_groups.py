#!/usr/bin/env python
class FilterModule(object):

    openstack_role_groups = {
        'openstack_nodes': ['openstack_control', 'openstack_network',
            'openstack_compute', 'openstack_monitoring',
            'openstack_storage', 'openstack'],
        'control': ['openstack_control', 'openstack'],
        'network': ['openstack_network', 'openstack'],
        'compute': ['openstack_compute'],
        'monitoring': ['openstack_monitoring', 'openstack'],
        'storage': ['openstack_storage', 'openstack']
    }

    openstack_role_subgroups = {
        "baremetal": ['control', 'network', 'compute', 'storage', 'monitoring'],
        "collectd": ['compute'],
        "grafana": [ "monitoring"],
        "etcd": [ "control"],
        "influxd": [ "monitoring"],
        "karbor": [ "control"],
        "kibana": [ "control"],
        "telegraf": [ "compute","control","monitoring","network", "storage"],
        "elasticsearch": ["control"],
        "haproxy": ["network"],
        "mariadb": ["control"],
        "rabbitmq": ["control"],
        "mongodb": ["control"],
        "keystone": ["control"],
        "glance": ["control"],
        "nova": ["control"],
        "neutron": ["network"],
        "cinder": ["control"],
        "cloudkitty": ["control"],
        "freezer": ["control"],
        "memcached": ["control"],
        "horizon": ["control"],
        "swift": ["control"],
        "barbican": ["control"],
        "heat": ["control"],
        "murano": ["control"],
        "solum": ["control"],
        "ironic": ["control"],
        "ceph": ["control"],
        "magnum": ["control"],
        "sahara": ["control"],
        "mistral": ["control"],
        "manila": ["control"],
        "ceilometer": ["control"],
        "aodh": ["control"],
        "congress": ["control"],
        "panko": ["control"],
        "gnocchi": ["control"],
        "tacker": ["control"],
        "trove": ["control"],
        "tempest": ["control"],
        "senlin": ["control"],
        "vmtp": ["control"],
        "watcher": ["control"],
        "rally": ["control"],
        "searchlight": ["control"],
        "octavia": ["control"],
        "designate": ["control"],
        "placement": ["control"],
        "glance-api": ["glance"],
        "glance-registry": ["glance"],
        "nova-api": ["nova"],
        "nova-conductor": ["nova"],
        "nova-consoleauth": ["nova"],
        "nova-novncproxy": ["nova"],
        "nova-scheduler": ["nova"],
        "nova-spicehtml5proxy": ["nova"],
        "nova-compute-ironic": ["nova"],
        "nova-serialproxy": ["nova"],
        "neutron-server": ["control"],
        "neutron-dhcp-agent": ["neutron"],
        "neutron-l3-agent": ["neutron"],
        "ironic-neutron-agent": ["neutron"],
        "neutron-infoblox-ipam-agent": ["neutron"],
        "neutron-lbaas-agent": ["neutron"],
        "neutron-metadata-agent": ["neutron"],
        "neutron-vpnaas-agent": ["neutron"],
        "neutron-bgp-dragent": ["neutron"],
        "ceph-mon": ["ceph"],
        "ceph-rgw": ["ceph"],
        "ceph-osd": ["storage"],
        "cinder-api": ["cinder"],
        "cinder-backup": ["storage"],
        "cinder-scheduler": ["cinder"],
        "cinder-volume": ["storage"],
        "cloudkitty-api": ["cloudkitty"],
        "cloudkitty-processor": ["cloudkitty"],
        "freezer-api": ["freezer"],
        "iscsid": ["compute", "storage", "ironic-conductor"],
        "tgtd": ["storage"],
        "karbor-api": ["karbor"],
        "karbor-protection": ["karbor"],
        "karbor-operationengine": ["karbor"],
        "manila-api": ["manila"],
        "manila-scheduler": ["manila"],
        "manila-share": ["manila"],
        "manila-data": ["manila"],
        "swift-proxy-server": ["swift"],
        "swift-account-server": ["storage"],
        "swift-container-server": ["storage"],
        "swift-object-server": ["storage"],
        "barbican-api": ["barbican"],
        "barbican-keystone-listener": ["barbican"],
        "barbican-worker": ["barbican"],
        "heat-api": ["heat"],
        "heat-api-cfn": ["heat"],
        "heat-engine": ["heat"],
        "manila-data": ["manila"],
        "murano-api": ["murano"],
        "murano-engine": ["murano"],
        "ironic-api": ["ironic"],
        "ironic-conductor": ["ironic"],
        "ironic-inspector": ["ironic"],
        "ironic-pxe": ["ironic"],
        "ironic-ipxe": ["ironic"],
        "magnum-api": ["magnum"],
        "magnum-conductor": ["magnum"],
        "sahara-api": ["sahara"],
        "sahara-engine": ["sahara"],
        "solum-api": ["solum"],
        "solum-worker": ["solum"],
        "solum-deployer": ["solum"],
        "solum-conductor": ["solum"],
        "mistral-api": ["mistral"],
        "mistral-executor": ["mistral"],
        "mistral-engine": ["mistral"],
        "ceilometer-api": ["ceilometer"],
        "ceilometer-central": ["ceilometer"],
        "ceilometer-notification": ["ceilometer"],
        "ceilometer-collector": ["ceilometer"],
        "ceilometer-compute": ["compute"],
        "aod-api": ["aodh"],
        "aod-evaluator": ["aodh"],
        "aod-listener": ["aodh"],
        "aod-notifier": ["aodh"],
        "congress-api": ["congress"],
        "congress-datasource": ["congress"],
        "congress-policy-engine": ["congress"],
        "panko-api": ["panko"],
        "gnocchi-api": ["gnocchi"],
        "gnocchi-statsd": ["gnocchi"],
        "gnocchi-metricd": ["gnocchi"],
        "trove-api": ["trove"],
        "trove-conductor": ["trove"],
        "trove-taskmanager": ["trove"],
        "multipathd": ["compute"],
        "watcher-api": ["watcher"],
        "watcher-engine": ["watcher"],
        "watcher-applier": ["watcher"],
        "senlin-api": ["senlin"],
        "senlin-engine": ["senlin"],
        "searchlight-api": ["searchlight"],
        "searchlight-listener": ["searchlight"],
        "octavia-api": ["octavia"],
        "octavia-health-manager": ["octavia"],
        "octavia-housekeeping": ["octavia"],
        "octavia-worker": ["octavia"],
        "designate-api": ["designate"],
        "designate-central": ["designate"],
        "designate-mdns": ["designate"],
        "designate-worker": ["designate"],
        "designate-sink": ["designate"],
        "designate-backend-bind9": ["designate"],
        "placement-api": ["placement"],

    }

    def filters(self):
        return {
            'openstack_host_groups': self.openstack_host_groups
        }

    def openstack_host_groups(self, instances, ip):

        for k,v in instances.items():
            grp_list = []
            if v['ip'] != ip:
                continue

            if not v.get('roles'):
                return grp_list

            for role in v.get('roles'):
                for i, j in self.openstack_role_groups.items():
                    if role in j:
                        grp_list.append(i)
            sub_grps = []
            for i, j in self.openstack_role_subgroups.items():
                for grp in grp_list:
                    if grp in j:
                        sub_grps.append(i)
                        if i not in self.openstack_role_groups:
                            for k, v in self.openstack_role_subgroups.items():
                                if i in v:
                                    sub_grps.append(k)

            grp_list = grp_list + sub_grps

            return grp_list
