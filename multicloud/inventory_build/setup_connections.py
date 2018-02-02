#!/usr/bin/env python

from collections import namedtuple


def clean_protocols(protocols):
    return [protocol if isinstance(protocol, str) else protocol.keys()[0] for protocol in protocols]


def possibility_connection(host_protocols, remote_host_protocols):
    host_protocols, remote_host_protocols = clean_protocols(host_protocols), clean_protocols(remote_host_protocols)
    possibility = []
    if 'openvpn_server' in host_protocols and 'openvpn_client' in remote_host_protocols:
        possibility.append('openvpn_remote_host')
    if 'openvpn_client' in host_protocols and 'openvpn_server' in remote_host_protocols:
        possibility.append('openvpn_host_remote')
    if 'ipsec_server' in host_protocols and 'ipsec_client' in remote_host_protocols:
        possibility.append('ipsec_remote_host')
    if 'ipsec_client' in host_protocols and 'ipsec_server' in remote_host_protocols:
        possibility.append('ipsec_host_remote')
    return possibility


def choice_connection_type(possibility, host_id, remote_host_id, prefer='ipsec'):
    if not possibility:
        return None
    matrix = []
    option_tuple = namedtuple('option', ['name', 'id_value', 'protocol_value'])
    for option in possibility:
        id_value = host_id - remote_host_id if option[-6:] == 'remote' else remote_host_id - host_id
        protocol_value = 1 if option[:len(prefer)] == prefer else 0
        matrix.append(option_tuple(option , id_value, protocol_value))
    matrix.sort(key = lambda l: (l[1], l[2]), reverse=True)
    return matrix[0].name


def create_connections(inventory):
    for host, host_vars in inventory.iteritems():
        host_vars['openvpn_clients'], host_vars['openvpn_servers'] = [],  []
        host_vars['ipsec_clients'], host_vars['ipsec_servers'] = [], []

        remote_hosts = inventory.copy()
        remote_hosts.pop(host)
        if 'hubs' in host_vars and host_vars['hubs']:
            [remote_hosts.pop(key) for key in remote_hosts.keys() if key not in host_vars['hubs']]

        for remote_host, remote_host_vars in remote_hosts.iteritems():
            if 'hubs' in remote_host_vars and not host in remote_host_vars['hubs']:
                # print '{host} NOT in hubs {remote_host}'.format(host=host, remote_host=remote_host)
                continue
            possibility = possibility_connection(host_vars['protocols'], remote_host_vars['protocols'])
            connection_type = choice_connection_type(possibility, host_vars['id'], remote_host_vars['id'])
            #TODO if cluster use ip_local and ALWAYS IPSEC(ignore protocols)
            remote_ip = remote_host_vars['ip_public'] if host_vars['cluster'] != remote_host_vars['cluster'] else remote_host_vars['ip_local']
            if 'openvpn' in connection_type:
                if connection_type[-6:] == 'remote':
                    host_vars['openvpn_clients'].append(remote_ip)
                else:
                    host_vars['openvpn_servers'].append(remote_ip)
            elif 'ipsec' in connection_type:
                if connection_type[-6:] == 'remote':
                    host_vars['ipsec_clients'].append(remote_ip)
                else:
                    host_vars['ipsec_servers'].append(remote_ip)

        inventory[host].update(host_vars)
    return inventory
