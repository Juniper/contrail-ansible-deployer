#!/usr/bin/env python
from os import system, path
from sys import exit
from threading import Thread
from time import sleep
from argparse import ArgumentParser
from getpass import getpass
import tarfile
import urllib2

from pyVim import connect
from pyVmomi import vim

def get_args():
    """
    Get CLI arguments.
    """
    parser = ArgumentParser(description='Arguments for talking to vCenter')

    parser.add_argument('-s', '--host',
                        required=True,
                        action='store',
                        help='vSphere service to connect to.')

    parser.add_argument('-o', '--port',
                        type=int,
                        default=443,
                        action='store',
                        help='Port to connect on.')

    parser.add_argument('-u', '--user',
                        required=True,
                        action='store',
                        help='Username to use.')

    parser.add_argument('-p', '--password',
                        required=False,
                        action='store',
                        help='Password to use.')

    parser.add_argument('--datastore_name',
                        required=False,
                        action='store',
                        default=None,
                        help='Datastore to be updated in AgentVM \
                          Settings.')

    parser.add_argument('--network_name',
                        required=False,
                        action='store',
                        default=None,
                        help='Network to be updated in AgentVM \
                          Settings.')

    parser.add_argument('--host_name',
                        required=True,
                        action='store',
                        help='Name of the host to update AgentVM Settings')

    args = parser.parse_args()

    if not args.password:
        args.password = getpass(prompt='Enter password: ')

    return args

def get_obj(content, vimtype, name):
    obj = None
    container = content.viewManager.CreateContainerView(content.rootFolder, vimtype, True)
    for c in container.view:
        if c.name == name:
            obj = c
            break
    return obj

def update_agent_vm_setting(content, hostname, datastore_name, network_name):
    host = get_obj(content, [vim.HostSystem], hostname)

    for datastore in host.datastore:
        if datastore.name == datastore_name:
           agent_datastore = datastore
           break

    for network in host.network:
        if network.name == network_name:
           agent_network = network
           break

    host_config = vim.host.EsxAgentHostManager.ConfigInfo(agentVmDatastore=agent_datastore,
                                                         agentVmNetwork=agent_network)
    host.configManager.esxAgentHostManager.EsxAgentHostManagerUpdateConfig(configInfo=host_config)

def main():
    args = get_args()

    try:
       ssl = __import__("ssl")
       context = ssl._create_unverified_context()

       si = connect.SmartConnect(host=args.host,
                                 user=args.user,
                                 pwd=args.password,
                                 port=args.port,
                                 sslContext=context)
    except Exception as e:
       si = connect.SmartConnect(host=args.host,
                                 user=args.user,
                                 pwd=args.password,
                                 port=args.port)
    except:
        print "Unable to connect to %s" % args.host
        exit(1)

    content = si.RetrieveContent()

    # Edit Agent VM Settings
    update_agent_vm_setting(content, args.host_name, args.datastore_name, args.network_name)

    connect.Disconnect(si)

if __name__ == "__main__":
    exit(main())
