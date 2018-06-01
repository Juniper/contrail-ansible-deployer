#!/usr/bin/env python
from sys import exit
from time import sleep
from argparse import ArgumentParser

from pyVim import connect
from pyVmomi import vim

from time import sleep

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

    parser.add_argument('--host_name',
                        required=True,
                        action='store',
                        help='Name of the host')

    args = parser.parse_args()

    if not args.password:
        args.password = getpass(prompt='Enter password: ')

    return args

def get_obj(si_content, vimtype, name):
    obj = None
    container = si_content.viewManager.CreateContainerView(si_content.rootFolder, vimtype, True)
    for c in container.view:
        if c.name == name:
            obj = c
            break
    return obj

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

    items = content.viewManager.CreateContainerView(content.rootFolder, [vim.HostSystem], True).view
    for obj in items:
        if obj.name == args.host_name:
            host = obj
            break

    container = host  # starting point to look into
    viewType = [vim.VirtualMachine]  # object types to look for
    recursive = True  # whether we should look into it recursively
    containerView = content.viewManager.CreateContainerView(
            container, viewType, recursive)

    children = containerView.view
    for child in children:
        if child.parent.name == 'ESX Agents':
           if child.guest.toolsStatus in {'toolsOk', 'toolsNotRunning'}:
              print "deployed"
              break

    connect.Disconnect(si)
 
if __name__ == "__main__":
    exit(main())

