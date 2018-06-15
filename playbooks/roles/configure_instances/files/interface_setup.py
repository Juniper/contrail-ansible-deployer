#!/usr/bin/env python
'''Provision Interface'''
#
# Copyright (c) 2013 Juniper Networks, Inc. All rights reserved.
#

__version__ = '1.0'

import os
import re
import sys
import argparse
import socket
import fcntl
import struct
import logging
import platform
import time
import json
import subprocess
from netaddr import IPNetwork
from tempfile import NamedTemporaryFile
from distutils.version import LooseVersion

logging.basicConfig(format='%(asctime)-15s:: %(funcName)s:%(levelname)s::\
                            %(message)s',
                    level=logging.INFO)
log = logging.getLogger(__name__)
(PLATFORM, VERSION, EXTRA) = platform.linux_distribution()

bond_opts_dict  = {'arp_interval' : 'int',
                   'arp_ip_target': 'ipaddr_list',
                   'arp_validate' : ['none', 'active', 'backup', 'all'],
                   'downdelay'    : 'int',
                   'fail_over_mac': 'macaddr',
                   'lacp_rate'    : ['slow', 'fast'],
                   'miimon'       : 'int',
                   'mode'         : ['balance-rr', 'active-backup',
                                     'balance-xor', 'broadcast', '802.3ad',
                                     'balance-tlb', 'balance-alb'],
                   'primary'      : 'string',
                   'updelay'      : 'int',
                   'use_carrier'  : 'int',
                   'xmit_hash_policy': ['layer2', 'layer2+3', 'layer3+4']
                  }

class BaseInterface(object):
    '''Base class containing common methods for configuring interface
    '''
    def __init__(self, **kwargs):
        self.device     = kwargs['device']
        self.members    = kwargs.get('members', [])
        self.ip         = kwargs.get('ip', None)
        self.gw         = kwargs.get('gw', None)
        self.vlan       = kwargs.get('vlan', None)
        self.dhcp       = kwargs.get('dhcp', None)
        self.no_restart_network = kwargs.get('no_restart_network', False)
        self.mtu        = kwargs.get('mtu', None)
        self.bond_opts  = {'miimon': '100', 'mode': '802.3ad',
                           'xmit_hash_policy': 'layer3+4'}
        try:
            self.bond_opts.update(json.loads(kwargs.get('bopts', {})))
        except ValueError:
            log.warn("No bonding options specified using default %s",
                                                       self.bond_opts)
        self.bond_opts_str = ''
        self.mac_list = {}
        self.tempfile = NamedTemporaryFile(delete=False)
        self.intf_mac_mapping = self.gen_intf_mac_mapping()
        self.populate_device()

    def gen_intf_mac_mapping(self):
        sys_dir = '/sys/class/net/'
        mac_map = {}
        for device in os.listdir(sys_dir):
            mac = os.popen('cat %s/%s/address'%(sys_dir, device)).read()
            mac_map[mac.strip().lower()] = device
        return mac_map

    def populate_device(self):
        if self.is_valid_mac(self.device):
            log.info("mac address is %s", self.device)
            self.device = self.intf_mac_mapping.get(self.device.lower(), '')
            if not self.device:
                log.error("mac address is not present in the system")
                exit()
        members = []
        for i in xrange(len(self.members)):
            if self.is_valid_mac(self.members[i]):
                log.info("bond member mac address is %s", self.members[i])
                self.members[i] = self.intf_mac_mapping.get(self.members[i].lower(), '')
                if not self.members[i]:
                    log.error("mac address is not present in the system")
                    exit()

    def validate_bond_opts(self):
        for key in list(self.bond_opts):
            if not self.is_valid_opts(key, self.bond_opts[key], bond_opts_dict):
                del self.bond_opts[key]
            else:
                self.bond_opts_str += '%s=%s '%(key, self.bond_opts[key])

    def is_valid_mac(self, mac):
        if re.match("[0-9a-f]{2}(:)[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$", mac.lower()):
            return True
        else:
            return False

    def is_valid_ipaddr_list(p):
        addr_list = ip.split(",")
        for addr in addr_list:
            socket.inet_pton(socket.AF_INET, addr)
        return True

    def is_valid_opts(self, key, value, compare_dict):
        if key in compare_dict:
          try:
            if (not isinstance(value, int) and value in compare_dict[key]) or\
               ('int' in compare_dict[key] and int(value)) or\
               ('macaddr' in compare_dict[key] and self.is_valid_mac(value)) or\
               ('ipaddr_list' in compare_dict[key] and
                                 self.is_valid_ipaddr_list(value)) or\
               ('string' in compare_dict[key] and isinstance(value,basestring)):
                return True
          except:
            log.warn("Caught Exception while processing (%s, %s)" %(key, value))
            log.warn("Supported options for key %s are %s" %(key,
                                                        str(compare_dict[key])))
        return False

    def write_network_script(self, device, cfg):
        '''Create an interface config file in network-scripts with given
            config
        '''
        nw_scripts = os.path.join(os.path.sep, 'etc', 'sysconfig', 
                                  'network-scripts')
        nwfile = os.path.join(nw_scripts, 'ifcfg-%s' %device)
        if os.path.isfile(nwfile):
            tmpfile = os.path.join(os.path.dirname(nwfile), \
                                  'moved-%s' %os.path.basename(nwfile))
            log.info('Backup existing file %s to %s' %(nwfile, tmpfile))
            os.system('sudo mv %s %s' %(nwfile, tmpfile))
        with open(self.tempfile.name, 'w') as fd:
            fd.write('\n'.join(['%s=%s' %(key, value) \
                          for key, value in cfg.items()]))
            fd.write('\n')
            fd.flush()
        os.system('sudo cp -f %s %s'%(self.tempfile.name, nwfile))

    def get_mac_addr(self, iface):
        '''Retrieve mac address for the given interface in the system'''
        macaddr = None
        if self.mac_list.has_key(iface):
            return self.mac_list[iface]
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            macinfo = fcntl.ioctl(sock.fileno(), 0x8927,
                                  struct.pack('256s', iface[:15]))
            macaddr = ''.join(['%02x:' % ord(each) for each in macinfo[18:24]])[:-1]
        except IOError, err:
            raise Exception('Unable to fetch MAC address of interface (%s)' %iface)
        return macaddr

    def create_vlan_interface(self):
        '''Create interface config for vlan sub interface'''
        vlanif = "%s.%s"%(self.device, self.vlan)
        log.info('Creating vlan interface: %s' %vlanif)
        cfg = {'DEVICE'        : vlanif,
               'ONBOOT'        : 'yes',
               'BOOTPROTO'     : 'none',
               'NM_CONTROLLED' : 'no',
               'VLAN'          : 'yes'
              }
        if self.ip:
            cfg.update({
               'NETMASK'       : self.netmask,
               'IPADDR'        : self.ipaddr})
        if self.gw:
            cfg['GATEWAY'] = self.gw
        if self.mtu:
            cfg['MTU'] = self.mtu
        self.write_network_script(vlanif, cfg)

    def create_bond_members(self):
        '''Create interface config for each bond members'''
        # create slave interface
        if not self.members:
            log.warn('No slaves are specified for bond interface. Please use --members')
        for each in self.members:
            log.info('Creating bond member: %s' %each)
            mac = self.get_mac_addr(each)
            cfg = {'DEVICE'        : each,
                   'ONBOOT'        : 'yes',
                   'BOOTPROTO'     : 'none',
                   'NM_CONTROLLED' : 'no',
                   'HWADDR'        : mac,
                   'MASTER'        : self.device,
                   'SLAVE'         : 'yes'
                  }
            self.write_network_script(each, cfg)

    def get_mac_from_bond_intf(self):
        output= os.popen("sudo cat /proc/net/bonding/%s"%self.device).read()
        device_list= re.findall('Slave Interface:\s+(\S+)$', output, flags=re.M)
        mac_list= re.findall('HW addr:\s+(\S+)$', output, flags=re.M)
        if len(device_list) == len(mac_list):
            for (device, mac) in zip(device_list, mac_list):
                self.mac_list[device]= mac.lower()

    def create_bonding_interface(self):
        '''Create interface config for bond master'''
        # create slave interface
        self.get_mac_from_bond_intf()
        self.create_bond_members()
        log.info('Creating bond master: %s' %self.device)
        cfg = {'DEVICE'        : self.device,
               'ONBOOT'        : 'yes',
               'BOOTPROTO'     : 'none',
               'NM_CONTROLLED' : 'no',
               'BONDING_MASTER': 'yes',
               'BONDING_OPTS'  : "\"%s\""%self.bond_opts_str.strip(),
               'SUBCHANNELS'   : '1,2,3'
              }
        if not self.vlan:
            if self.dhcp:
                cfg.update({'BOOTPROTO': 'dhcp'})
            elif self.ip:
                cfg.update({'NETMASK'       : self.netmask,
                            'IPADDR'        : self.ipaddr
                          })
            if self.gw:
                cfg['GATEWAY'] = self.gw
            if self.mtu:
                cfg['MTU'] = self.mtu
        else:
            self.create_vlan_interface()
        self.write_network_script(self.device, cfg)

    def create_interface(self):
        '''Create interface config for normal interface'''
        log.info('Creating Interface: %s' %self.device)
        mac = self.get_mac_addr(self.device)
        cfg = {'DEVICE'        : self.device,
               'ONBOOT'        : 'yes',
               'BOOTPROTO'     : 'none',
               'NM_CONTROLLED' : 'no',
               'HWADDR'        : mac}
        if self.mtu:
            cfg['MTU'] = self.mtu
        if not self.vlan:
            if self.dhcp:
                cfg.update({'BOOTPROTO': 'dhcp'})
            elif self.ip:
                cfg.update({'NETMASK'       : self.netmask,
                            'IPADDR'        : self.ipaddr
                            })
            if self.gw:
                cfg['GATEWAY'] = self.gw
        else:
            self.create_vlan_interface()
        self.write_network_script(self.device, cfg)

    def restart_service(self):
        '''Restart network service'''
        log.info('Restarting Network Services...')
        os.system('sudo service network restart')
        time.sleep(5)

    def post_conf(self):
        '''Execute commands after after interface configuration'''
        if not self.no_restart_network:
            self.restart_service()

    def pre_conf(self):
        '''Execute commands before interface configuration'''
        pass

    def setup(self):
        '''High level method to call individual methods to configure
            interface
        '''
        self.validate_bond_opts()
        self.pre_conf()
        if self.ip:
            ip = IPNetwork(self.ip)
            self.ipaddr = str(ip.ip)
            self.netmask = str(ip.netmask)
        if self.members:
            self.create_bonding_interface()
        elif self.vlan:
            self.create_vlan_interface()
        else:
            self.create_interface()
        #time.sleep(3)
        self.post_conf()

class UbuntuInterface(BaseInterface):
    def restart_service(self):
        '''Restart network service for Ubuntu'''
        log.info('Restarting Network Services...')
        if LooseVersion(VERSION) < LooseVersion("14.04"):
            subprocess.call('sudo /etc/init.d/networking restart', shell=True)
        else:
            subprocess.call('sudo ifdown -a && sudo ifup -a', shell=True)
        time.sleep(20)

    def remove_lines(self, ifaces, filename):
        '''Remove existing config related to given interface if the same
            needs to be re-configured
        '''
        log.info('Remove Existing Interface configs in %s' %filename)
        # read existing file
        if not filename:
            filename = os.path.join(os.path.sep, 'etc', 'network', 'interfaces')

        with open(filename, 'r') as fd:
            cfg_file = fd.read()

        # get blocks
        keywords = ['allow-', 'auto', 'iface', 'source', 'mapping']
        pattern = '\n\s*' + '|\n\s*'.join(keywords)
        iters = re.finditer(pattern, cfg_file)
        indices = [match.start() for match in iters]
        matches = map(cfg_file.__getslice__, indices, indices[1:] + [len(cfg_file)])

        # backup old file
        bckup = os.path.join(os.path.dirname(filename), 'orig.%s.%s' %(
                    os.path.basename(filename),time.strftime('%d%m%y%H%M%S')))
        os.system('sudo cp %s %s' %(filename, bckup))
        os.system('sudo cp %s %s' %(filename, self.tempfile.name))

        iface_pattern = '^\s*iface ' + " |^\s*iface ".join(ifaces) + ' '
        auto_pattern = '^\s*auto ' + "|^\s*auto ".join(ifaces)
        # write new file
        with open(self.tempfile.name, 'w') as fd:
            fd.write('%s\n' %cfg_file[0:indices[0]])
            for each in matches:
                each = each.strip()
                if re.match(auto_pattern, each) or re.match(iface_pattern, each):
                    continue
                else:
                    fd.write('%s\n' %each)
            fd.flush()
        os.system('sudo cp -f %s %s'%(self.tempfile.name, filename))

    def pre_conf(self):
        '''Execute commands before interface configuration for Ubuntu'''
        filename = os.path.join(os.path.sep, 'etc', 'network', 'interfaces')
        if self.vlan:
            ifaces = [self.device + '.' + self.vlan, 'vlan'+self.vlan]
        else:
            ifaces = [self.device] + self.members
        self.remove_lines(ifaces, filename)

    def validate_bond_opts(self):
        self.bond_opts_str = 'bond-slaves none\n'
        for key in list(self.bond_opts):
            if not self.is_valid_opts(key, self.bond_opts[key], bond_opts_dict):
                del self.bond_opts[key]
            else:
                self.bond_opts_str += 'bond-%s %s\n'%(key, self.bond_opts[key])

    def write_network_script(self, cfg):
        '''Append new configs to interfaces file'''
        interface_file = os.path.join(os.path.sep, 'etc', 'network', 'interfaces')
        os.system('sudo cp %s %s' %(interface_file, self.tempfile.name))

        # write new file
        with open(self.tempfile.name, 'a+') as fd:
            fd.write('\n%s\n' %cfg[0])
            fd.write('\n    '.join(cfg[1:]))
            fd.write('\n')
            fd.flush()
        os.system('sudo cp -f %s %s'%(self.tempfile.name, interface_file))

    def create_interface(self):
        '''Create interface config for normal interface for Ubuntu'''
        log.info('Creating Interface: %s' % self.device)

        if self.dhcp:
            cfg = ['auto %s' %self.device,
                   'iface %s inet dhcp' %self.device]
            if self.mtu:
                cfg.append('pre-up /sbin/ip link set %s mtu %s' % (self.device, self.mtu))
        else:
            if self.ip:
                option = "static"
            else:
                option = "manual"
            cfg = ['auto %s' %self.device,
                   'iface %s inet %s' %(self.device, option)]
            if self.ip:
                cfg.append('address %s' %self.ipaddr)
                cfg.append('netmask  %s' %self.netmask)
            if self.gw:
                cfg.append('gateway %s' %self.gw)
            if self.mtu:
                cfg.append('mtu %s' %self.mtu)
        self.write_network_script(cfg)

    def create_bond_members(self):
        '''Create interface config for each bond members for Ubuntu'''
        for each in self.members:
            log.info('Create Bond Members: %s' %each)
            cfg = ['auto %s' %each,
                   'iface %s inet manual' %each,
                   'down ip addr flush dev %s' %each,
                   'bond-master %s' %self.device]
            self.write_network_script(cfg)

    def create_vlan_interface(self):
        '''Create interface config for vlan sub interface'''
        interface = 'vlan'+self.vlan
        if self.dhcp:
            cfg = ['auto %s' %interface,
                   'iface %s inet dhcp' %interface,
                   'vlan-raw-device %s' %self.device]
        else:
            if self.ip:
                option = "static"
            else:
                option = "manual"
            cfg = ['auto %s' %interface,
                   'iface %s inet %s' %(interface, option)]
            if self.ip:
                cfg.append('address %s' %self.ipaddr)
                cfg.append('netmask  %s' %self.netmask)
            cfg.append('vlan-raw-device  %s' %self.device)
        if self.gw:
            cfg.append('gateway %s' %self.gw)
        if self.mtu:
            cfg.append('mtu %s' %self.mtu)
        self.write_network_script(cfg)

    def create_bonding_interface(self):
        '''Create interface config for bond master'''
        self.get_mac_from_bond_intf()
        self.create_bond_members()
        bond_mac = self.get_mac_addr(self.members[0])
        log.info('Creating bond master: %s with Mac Addr: %s' %
                 (self.device, bond_mac))
        if self.dhcp:
            cfg = ['auto %s' %self.device,
                   'iface %s inet dhcp' %self.device]
        else:
            if self.ip:
                option = "static"
            else:
                option = "manual"
            cfg = ['auto %s' %self.device,
                   'iface %s inet %s' %(self.device, option)]
            if self.ip:
                cfg.append('address %s' %self.ipaddr)
                cfg.append('netmask  %s' %self.netmask)
            cfg.append('hwaddress  %s' %bond_mac)
            if self.gw:
                cfg.append('gateway %s' %self.gw)
        if self.mtu:
            cfg.append('mtu %s' %self.mtu)
        cfg += self.bond_opts_str.split("\n")
        self.write_network_script(cfg)

def parse_cli(args):
    '''Define and Parser arguments for the script'''
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version', '-v',
                        action='version',
                        version=__version__,
                        help='Display version and exit')
    parser.add_argument('--device', 
                        action='store', 
                        required=True,
                        help='Interface Name or Mac address')
    parser.add_argument('--members', 
                        action='store',
                        default=[],
                        nargs='+',
                        help='Name of Member interfaces or Mac addresses')
    parser.add_argument('--ip', 
                        action='store',
                        help='IP address of the new Interface')
    parser.add_argument('--gw', 
                        action='store',
                        help='Gateway Address of the Interface')
    parser.add_argument('--bond-opts',
                        dest='bopts',
                        action='store',
                        default='',
                        help='Interface Bonding options')
    parser.add_argument('--vlan',
                        action='store',
                        help='vLAN ID')
    parser.add_argument('--dhcp',
                        action='store_true',
                        help='DHCP')
    parser.add_argument('--no-restart-network',
                        action='store_true',
                        default=False,
                        help='Disable network restart after configuring interfaces')
    parser.add_argument('--mtu',
                        action='store',
                        help='MTU size of interface')
    pargs = parser.parse_args(args)
    if len(args) == 0:
        parser.print_help()
        sys.exit(2)
    return dict(pargs._get_kwargs())

def main():
    pargs = parse_cli(sys.argv[1:])
    if PLATFORM.lower() == 'ubuntu':
        interface = UbuntuInterface(**pargs)
    else:
        interface = BaseInterface(**pargs)
    interface.setup()

if __name__ == '__main__':
    main()
