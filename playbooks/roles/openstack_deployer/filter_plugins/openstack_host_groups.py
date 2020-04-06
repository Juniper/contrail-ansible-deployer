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
        "aod-api": ["aodh"],
        "aod-evaluator": ["aodh"],
        "aod-listener": ["aodh"],
        "aod-notifier": ["aodh"],
        "aodh": ["control"],
        "barbican-api": ["barbican"],
        "barbican-keystone-listener": ["barbican"],
        "barbican-worker": ["barbican"],
        "barbican": ["control"],
        "baremetal": ['control', 'network', 'compute', 'storage', 'monitoring'],
        "blazar": ["control"],
        "ceilometer-api": ["ceilometer"],
        "ceilometer-central": ["ceilometer"],
        "ceilometer-collector": ["ceilometer"],
        "ceilometer-compute": ["compute"],
        "ceilometer-notification": ["ceilometer"],
        "ceilometer": ["control"],
        "ceph-mon": ["ceph"],
        "ceph-osd": ["storage"],
        "ceph-rgw": ["ceph"],
        "ceph": ["control"],
        "cinder-api": ["cinder"],
        "cinder-backup": ["storage"],
        "cinder-scheduler": ["cinder"],
        "cinder-volume": ["storage"],
        "cinder": ["control"],
        "cloudkitty-api": ["cloudkitty"],
        "cloudkitty-processor": ["cloudkitty"],
        "cloudkitty": ["control"],
        "collectd": ['compute'],
        "congress-api": ["congress"],
        "congress-datasource": ["congress"],
        "congress-policy-engine": ["congress"],
        "congress": ["control"],
        "designate-api": ["designate"],
        "designate-backend-bind9": ["designate"],
        "designate-central": ["designate"],
        "designate-mdns": ["designate"],
        "designate-sink": ["designate"],
        "designate-worker": ["designate"],
        "designate": ["control"],
        "elasticsearch": ["control"],
        "etcd": [ "control"],
        "freezer-api": ["freezer"],
        "freezer": ["control"],
        "glance-api": ["glance"],
        "glance-registry": ["glance"],
        "glance": ["control"],
        "gnocchi-api": ["gnocchi"],
        "gnocchi-metricd": ["gnocchi"],
        "gnocchi-statsd": ["gnocchi"],
        "gnocchi": ["control"],
        "grafana": [ "monitoring"],
        "haproxy": ["network"],
        "heat-api-cfn": ["heat"],
        "heat-api": ["heat"],
        "heat-engine": ["heat"],
        "heat": ["control"],
        "horizon": ["control"],
        "hyperv": [],
        "influxd": [ "monitoring"],
        "ironic-api": ["ironic"],
        "ironic-conductor": ["ironic"],
        "ironic-inspector": ["ironic"],
        "ironic-ipxe": ["ironic"],
        "ironic-neutron-agent": ["neutron"],
        "ironic-pxe": ["ironic"],
        "ironic": ["control"],
        "iscsid": ["compute", "storage", "ironic-conductor"],
        "kafka": ["control"],
        "karbor-api": ["karbor"],
        "karbor-operationengine": ["karbor"],
        "karbor-protection": ["karbor"],
        "karbor": [ "control"],
        "keystone": ["control"],
        "kibana": [ "control"],
        "magnum-api": ["magnum"],
        "magnum-conductor": ["magnum"],
        "magnum": ["control"],
        "manila-api": ["manila"],
        "manila-data": ["manila"],
        "manila-data": ["manila"],
        "manila-scheduler": ["manila"],
        "manila-share": ["manila"],
        "manila": ["control"],
        "mariadb": ["control"],
        "memcached": ["control"],
        "mistral-api": ["mistral"],
        "mistral-engine": ["mistral"],
        "mistral-executor": ["mistral"],
        "mistral": ["control"],
        "mongodb": ["control"],
        "multipathd": ["compute"],
        "murano-api": ["murano"],
        "murano-engine": ["murano"],
        "murano": ["control"],
        "neutron-bgp-dragent": ["neutron"],
        "neutron-dhcp-agent": ["neutron"],
        "neutron-infoblox-ipam-agent": ["neutron"],
        "neutron-l3-agent": ["neutron"],
        "neutron-lbaas-agent": ["neutron"],
        "neutron-metadata-agent": ["neutron"],
        "neutron-metering-agent": ["neutron"],
        "neutron-server": ["control"],
        "neutron-vpnaas-agent": ["neutron"],
        "neutron": ["network"],
        "nova-api": ["nova"],
        "nova-compute-ironic": ["nova"],
        "nova-conductor": ["nova"],
        "nova-super-conductor": ["nova"],
        "nova-consoleauth": ["nova"],
        "nova-novncproxy": ["nova"],
        "nova-scheduler": ["nova"],
        "nova-serialproxy": ["nova"],
        "nova-spicehtml5proxy": ["nova"],
        "nova": ["control"],
        "octavia-api": ["octavia"],
        "octavia-health-manager": ["octavia"],
        "octavia-housekeeping": ["octavia"],
        "octavia-worker": ["octavia"],
        "octavia": ["control"],
        "panko-api": ["panko"],
        "panko": ["control"],
        "placement-api": ["placement"],
        "placement": ["control"],
        "prometheus": ["monitoring"],
        "rabbitmq": ["control"],
        "rally": ["control"],
        "redis": ["control"],
        "sahara-api": ["sahara"],
        "sahara-engine": ["sahara"],
        "sahara": ["control"],
        "searchlight-api": ["searchlight"],
        "searchlight-listener": ["searchlight"],
        "searchlight": ["control"],
        "senlin-api": ["senlin"],
        "senlin-engine": ["senlin"],
        "senlin": ["control"],
        "skydive": ["monitoring"],
        "solum-api": ["solum"],
        "solum-conductor": ["solum"],
        "solum-deployer": ["solum"],
        "solum-worker": ["solum"],
        "solum": ["control"],
        "swift-account-server": ["storage"],
        "swift-container-server": ["storage"],
        "swift-object-server": ["storage"],
        "swift-proxy-server": ["swift"],
        "swift": ["control"],
        "tacker": ["control"],
        "telegraf": [ "compute","control","monitoring","network", "storage"],
        "tempest": ["control"],
        "tgtd": ["storage"],
        "trove-api": ["trove"],
        "trove-conductor": ["trove"],
        "trove-taskmanager": ["trove"],
        "trove": ["control"],
        "vmtp": ["control"],
        "watcher-api": ["watcher"],
        "watcher-applier": ["watcher"],
        "watcher-engine": ["watcher"],
        "watcher": ["control"],
        "zookeeper": ["control"],
        "zun": ["control"],
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
