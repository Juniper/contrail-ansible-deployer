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
from manage_dvs_pg import get_obj

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

    parser.add_argument('--datacenter_name',
                        required=False,
                        action='store',
                        default=None,
                        help='Name of the Datacenter you\
                          wish to use. If omitted, the first\
                          datacenter will be used.')

    parser.add_argument('--datastore_name',
                        required=False,
                        action='store',
                        default=None,
                        help='Datastore you wish the VM to be deployed to. \
                          If left blank, VM will be put on the first \
                          datastore found.')

    parser.add_argument('--cluster_name',
                        required=False,
                        action='store',
                        default=None,
                        help='Name of the cluster you wish the VM to\
                          end up on. If left blank the first cluster found\
                          will be used')

    parser.add_argument('-f', '--ova_path',
                        required=True,
                        action='store',
                        default=None,
                        help='Path of the OVA file to deploy.')

    parser.add_argument('--host_name', required=True, action='store', help='Name of the host to launch VM')
    parser.add_argument('--vm_name', required=True, action='store', help='Name of the VM')

    args = parser.parse_args()

    if not args.password:
        args.password = getpass(prompt='Enter password: ')

    return args


def get_ovf_descriptor(ovf_file):
    """
    Read in the OVF descriptor.
    """
    try:
        ovfd = ovf_file.read()
        return ovfd
    except:
        print "Could not read file: %s" % ovf_file
        exit(1)


def get_obj_in_list(obj_name, obj_list):
    """
    Gets an object out of a list (obj_list) whos name matches obj_name.
    """
    for o in obj_list:
        if o.name == obj_name:
            return o
    print ("Unable to find object by the name of %s in list:\n%s" %
           (o.name, map(lambda o: o.name, obj_list)))
    exit(1)


def get_objects(si, args):
    """
    Return a dict containing the necessary objects for deployment.
    """
    # Get datacenter object.
    datacenter_list = si.content.rootFolder.childEntity
    if args.datacenter_name:
        datacenter_obj = get_obj_in_list(args.datacenter_name, datacenter_list)
    else:
        datacenter_obj = datacenter_list[0]

    # Get datastore object.
    datastore_list = datacenter_obj.datastoreFolder.childEntity
    if args.datastore_name:
        datastore_obj = get_obj_in_list(args.datastore_name, datastore_list)
    elif len(datastore_list) > 0:
        datastore_obj = datastore_list[0]
    else:
        print "No datastores found in DC (%s)." % datacenter_obj.name

    # Get cluster object.
    cluster_list = datacenter_obj.hostFolder.childEntity
    if args.cluster_name:
        cluster_obj = get_obj_in_list(args.cluster_name, cluster_list)
    elif len(cluster_list) > 0:
        cluster_obj = cluster_list[0]
    else:
        print "No clusters found in DC (%s)." % datacenter_obj.name

    # Get host object
    hosts_list = cluster_obj.host
    host_obj = get_obj_in_list(args.host_name, hosts_list)

    # Get VM object

    # Generate resource pool.
    resource_pool_obj = cluster_obj.resourcePool

    return {"datacenter": datacenter_obj,
            "datastore": datastore_obj,
            "resource pool": resource_pool_obj,
            "host_obj": host_obj}

def keep_lease_alive(lease):
    """
    Keeps the lease alive while POSTing the VMDK.
    """
    while(True):
        sleep(5)
        try:
            # Choosing arbitrary percentage to keep the lease alive.
            lease.HttpNfcLeaseProgress(50)
            if (lease.state == vim.HttpNfcLease.State.done):
                return
            # If the lease is released, we get an exception.
            # Returning to kill the thread.
        except:
            return

def auto_start_vm(si, args, vm_obj):
    si_content = si.RetrieveContent()
    objs = get_objects(si, args)
    host = objs['host_obj']
    vm_obj = get_obj(si_content, [vim.VirtualMachine], args.vm_name)
    host_settings = vim.host.AutoStartManager.SystemDefaults()
    host_settings.enabled = True
    config = host.configManager.autoStartManager.config
    config.defaults = host_settings
    auto_power_info = vim.host.AutoStartManager.AutoPowerInfo()
    auto_power_info.key = vm_obj
    auto_power_info.startOrder = 1
    auto_power_info.startAction = "powerOn"
    auto_power_info.startDelay = -1
    auto_power_info.stopAction = "powerOff"
    auto_power_info.stopDelay = -1
    auto_power_info.waitForHeartbeat = 'no'
    config.powerInfo = [auto_power_info]
    host.configManager.autoStartManager.ReconfigureAutostart(config)

def main():
    args = get_args()
    t = tarfile.open(args.ova_path)
    ovffilename = list(filter(lambda x: x.endswith(".ovf"), t.getnames()))[0]
    ovffile = t.extractfile(ovffilename)
    ovfd = get_ovf_descriptor(ovffile)
    ovffile.close()

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

    objs = get_objects(si, args)
    # if VM already exists exit right away
    si_content = si.RetrieveContent()
    vm_obj = get_obj(si_content, [vim.VirtualMachine], args.vm_name) 
    if vm_obj:
        print "vm %s already exists" %args.vm_name
        exit(0)
    manager = si.content.ovfManager
    spec_params = vim.OvfManager.CreateImportSpecParams()
    # update spec_params to include host and name of the VM and possibly nics
    spec_params.hostSystem = objs['host_obj']
    spec_params.diskProvisioning = "thick"
    spec_params.entityName = args.vm_name
    import_spec = manager.CreateImportSpec(ovfd,
                                           objs["resource pool"],
                                           objs["datastore"],
                                           spec_params)
    lease = objs["resource pool"].ImportVApp(import_spec.importSpec,
                                             objs["datacenter"].vmFolder,
                                             objs['host_obj'])
    while(True):
        if lease.state == vim.HttpNfcLease.State.ready:
            # Spawn a thread to keep the lease active while POSTing
            # VMDK.
            keepalive_thread = Thread(target=keep_lease_alive, args=(lease,))
            keepalive_thread.daemon = True
            keepalive_thread.start()
            try:
                for deviceUrl in lease.info.deviceUrl:
                    url = deviceUrl.url.replace('*', args.host)
                    fileItem = list(filter(lambda x: x.deviceId ==
                                                     deviceUrl.importKey,
                                           import_spec.fileItem))[0]
                    ovffilename = list(filter(lambda x: x == fileItem.path,
                                              t.getnames()))[0]
                    ovffile = t.extractfile(ovffilename)
                    headers = { 'Content-length' : ovffile.size }
                    req = urllib2.Request(url, ovffile, headers)
                    try:
                        response = urllib2.urlopen(req, context = context)
                    except:
                        response = urllib2.urlopen(req)
                lease.HttpNfcLeaseComplete()
            except:
                raise
            keepalive_thread.join()
            auto_start_vm(si, args, vm_obj)
            connect.Disconnect(si)
            return 0
        elif lease.state == vim.HttpNfcLease.State.error:
            print "Lease error: %s" % lease.error
            connect.Disconnect(si)
            exit(1)

if __name__ == "__main__":
    exit(main())
