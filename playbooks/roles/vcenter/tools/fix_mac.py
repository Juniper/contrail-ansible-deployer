#!/usr/bin/env python
from sys import exit
from time import sleep
from argparse import ArgumentParser

from pyVim import connect
from pyVmomi import vim
from manage_dvs_pg import wait_for_task, get_obj, is_xenial_or_above, get_dvs_pg_obj

def get_args():
    """
    Get CLI arguments.
    """
    parser = ArgumentParser(description='Arguments for talking to vCenter')

    parser.add_argument('-s', '--host', required=True, action='store', help='vSphere service to connect to.')

    parser.add_argument('-o', '--port', type=int, default=443, action='store', help='Port to connect on.')

    parser.add_argument('-u', '--user', required=True, action='store', help='Username to use.')

    parser.add_argument('-p', '--password', required=True, action='store', help='Password to use.')

    parser.add_argument('--nics', required=True, action='store', help='Mac address of the VM')
    parser.add_argument('--vm_name', required=True, action='store', help='Name of the VM')

    args = parser.parse_args()

    return args

def update_mac(nic, vm_obj, si_content):
    if nic:
        switch_name = nic.split('*')[3]
        switch_type = nic.split('*')[2]
        mac = nic.split('*')[1]
        pg = nic.split('*')[0]
    spec = vim.vm.ConfigSpec()
    nic_spec = vim.vm.device.VirtualDeviceSpec()
    nic_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.edit
    for dev in vm_obj.config.hardware.device:
        if isinstance(dev, vim.vm.device.VirtualEthernetCard):
            # if this std switch pg
            if isinstance(dev.backing,
                         vim.vm.device.VirtualEthernetCard.NetworkBackingInfo):
                if dev.deviceInfo.summary == pg.strip() or \
                  dev.macAddress == mac.strip():
                    nic_spec.device = dev
                    nic_spec.device.macAddress = mac.strip()
                    nic_spec.device.addressType = 'manual'
                    break
            elif isinstance(dev.backing,
                  vim.vm.device.VirtualEthernetCard.DistributedVirtualPortBackingInfo):
                # get dvs pg object and check if its supplied in args
                dvs_pg = get_dvs_pg_obj(si_content,
                                       [vim.dvs.DistributedVirtualPortgroup],
                                       pg, switch_name)
                if dvs_pg:
                    nic_spec.device = dev
                    nic_spec.device.macAddress = mac.strip()
                    nic_spec.device.addressType = 'manual'
                    break
    nic_update = [nic_spec]
    spec.deviceChange = nic_update
    return vm_obj.ReconfigVM_Task(spec=spec)

def main():
    args = get_args()
    try:
        if is_xenial_or_above():
            ssl = __import__("ssl")
            context = ssl._create_unverified_context()
            si = connect.SmartConnect(host=args.host,
                                      user=args.user,
                                      pwd=args.password,
                                      port=args.port, sslContext=context)
        else:
            si = connect.SmartConnect(host=args.host,
                                      user=args.user,
                                      pwd=args.password,
                                      port=args.port)
        si_content = si.RetrieveContent()
    except:
        print "Unable to connect to %s" % args.host
        exit(1)
    # get VM object
    vm_obj = get_obj(si_content, [vim.VirtualMachine], args.vm_name)
    if not vm_obj:
        print "VM %s not pressent" %(args.vm_name)
        exit(1)
    #net_obj = get_obj(si_content, [vim.Network], args.network_name)
    nics = args.nics.split(',')
    for nic in nics:
        if not nic:
           continue
        task = update_mac(nic, vm_obj, si_content)
        wait_for_task(task)
    connect.Disconnect(si)

if __name__ == "__main__":
    exit(main())
