#!/usr/bin/env python

import platform

from sys import exit
from time import sleep
from argparse import ArgumentParser
from distutils.version import LooseVersion
from pyVim import connect
from pyVmomi import vim

def get_args():
    """
    Get CLI arguments.
    """
    parser = ArgumentParser(description='Arguments for talking to vCenter')

    parser.add_argument('-s', '--host', required=True, action='store', help='vSphere service to connect to.')

    parser.add_argument('-o', '--port', type=int, default=443, action='store', help='Port to connect on.')

    parser.add_argument('-u', '--user', required=True, action='store', help='Username to use.')

    parser.add_argument('-p', '--password', required=True, action='store', help='Password to use.')

    parser.add_argument('--dv_pg_name', required=True, action='store', help='Name of the port-group')
    parser.add_argument('--num_ports', required=True, action='store', help='Name of ports to be added to port-group')
    parser.add_argument('--dvs_name', required=True, action='store', help='Name of the dv-switch to add portgroup to')

    args = parser.parse_args()

    return args

def get_dvs_pg_obj(si_content, vimtype, portgroup_name, dvs_name):
    obj = None
    container = si_content.viewManager.CreateContainerView(si_content.rootFolder, vimtype, True)
    for c in container.view:
        if c.name == portgroup_name:
            if c.config.distributedVirtualSwitch.name == dvs_name:
                obj = c
                break
    return obj

def get_obj(si_content, vimtype, name):
    obj = None
    container = si_content.viewManager.CreateContainerView(si_content.rootFolder, vimtype, True)
    for c in container.view:
        if c.name == name:
            obj = c
            break
    return obj

def wait_for_task(task, actionName='job', hideResult=False):
    while task.info.state == (vim.TaskInfo.State.running or vim.TaskInfo.State.queued):
        sleep(2)
    if task.info.state == vim.TaskInfo.State.success:
        if task.info.result is not None and not hideResult:
            out = '%s completed successfully, result: %s' % (actionName, task.info.result)
            print out
        else:
            out = '%s completed successfully.' % actionName
            print out
    elif task.info.state == vim.TaskInfo.State.error:
        out = 'Error - %s did not complete successfully: %s' % (actionName, task.info.error)
        raise ValueError(out)
    return task.info.result

def update_dv_pg(args, dv_pg):
    dv_pg_spec = vim.dvs.DistributedVirtualPortgroup.ConfigSpec()
    dv_pg_spec.name = args.dv_pg_name
    dv_pg_spec.numPorts = int(args.num_ports)
    dv_pg_spec.configVersion = dv_pg.config.configVersion
    dv_pg_spec.type = vim.dvs.DistributedVirtualPortgroup.PortgroupType.earlyBinding
    dv_pg_spec.defaultPortConfig = vim.dvs.VmwareDistributedVirtualSwitch.VmwarePortConfigPolicy()
    dv_pg_spec.defaultPortConfig.securityPolicy = vim.dvs.VmwareDistributedVirtualSwitch.SecurityPolicy()
    dv_pg_spec.defaultPortConfig.vlan = vim.dvs.VmwareDistributedVirtualSwitch.TrunkVlanSpec()
    dv_pg_spec.defaultPortConfig.vlan.vlanId = [vim.NumericRange(start=1, end=4094)]
    dv_pg_spec.defaultPortConfig.securityPolicy.allowPromiscuous = vim.BoolPolicy(value=True)
    dv_pg_spec.defaultPortConfig.securityPolicy.forgedTransmits = vim.BoolPolicy(value=True)
    dv_pg_spec.defaultPortConfig.vlan.inherited = False
    dv_pg_spec.defaultPortConfig.securityPolicy.macChanges = vim.BoolPolicy(value=False)
    dv_pg_spec.defaultPortConfig.securityPolicy.inherited = False
    task = dv_pg.ReconfigureDVPortgroup_Task(dv_pg_spec)
    wait_for_task(task)
    print "Successfully modified DV Port Group %s" %args.dv_pg_name

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

    si_content = si.RetrieveContent()
    # check if PG exists else return error
    dv_switch = get_obj(si_content, [vim.DistributedVirtualSwitch], args.dvs_name)
    if not dv_switch:
        print "dv switch %s not pressent" %(args.dvs_name)
        exit(1)
    dv_pg = get_dvs_pg_obj(si_content, [vim.dvs.DistributedVirtualPortgroup], args.dv_pg_name, args.dvs_name)
    if not dv_pg:
        print "port-group %s not present in dvs %s" %(args.dv_pg_name, args.dvs_name)
        exit(1)
    update_dv_pg(args, dv_pg)
    connect.Disconnect(si)

if __name__ == "__main__":
    exit(main())
