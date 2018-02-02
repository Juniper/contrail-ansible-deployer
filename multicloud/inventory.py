#!/usr/bin/env python

import argparse
import yaml
from inventory_build.setup_connections import create_connections


INVENTORY_FILE = 'inventory.yml'
COMMON_FILE = 'common.yml'
NEW_INVENTORY_FILE = 'new_inventory.yml'


class InvetoryMulticloud(object):

    def __init__(self):
        self._parse_args()
        self._bulid_inventory()
        self.settings()

    def _create_connections(self):
        with open(INVENTORY_FILE, 'r') as read_file:
            hosts = yaml.load(read_file.read())
            return create_connections(hosts)

    def _bulid_inventory(self):

        with open(COMMON_FILE, 'r') as read_file:
            common = yaml.load(read_file.read())
        host_connections = self._create_connections()

        self.inventory = {'all': {
                    'hosts': host_connections.keys(),
                    'vars': common
                },
                '_meta': {
                    'hostvars': host_connections
                }
        }

    def __str__(self):
        return yaml.dump(self.inventory)

    def _parse_args(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('--list', '-l', action='store_true', help='Show list hosts')
        parser.add_argument('--hosts', action='store_true', help='Show list common vars')
        parser.add_argument('--common', '-c', action='store_true', help='Show list common vars')
        parser.add_argument('--draw', '-d', action='store_true',
                            help='Draw topology from file {file}'.format(file=NEW_INVENTORY_FILE))
        self.args = parser.parse_args()

    def settings(self):
        if self.args.list:
            print self
        elif self.args.common:
            print yaml.dump(self.inventory['all']['vars'])
        elif self.args.hosts:
            print yaml.dump(self.inventory['all']['hosts'])
        elif self.args.draw:
            try:
                from inventory_build.build_topology import Topology
            except ImportError:
                print 'No installed module for build, run:\npip install -r inventory_build/requirements.txt'
                return 0
            topo = Topology(self.inventory)
            topo.build_graph()
            print topo
            topo.draw()
        else:
            print self


if __name__ == '__main__':

    InvetoryMulticloud()





