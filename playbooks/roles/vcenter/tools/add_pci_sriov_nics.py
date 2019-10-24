#!/usr/bin/env python

from sys import exit
from time import sleep
from argparse import ArgumentParser

from pyVim import connect
from pyVmomi import vim
import paramiko

def get_args():
    """
    Get CLI arguments.
    """
    parser = ArgumentParser(description='Arguments for talking to vCenter')

    parser.add_argument('-s', '--host', required=True, action='store', help='vSphere service to connect to.')
    parser.add_argument('-o', '--port', type=int, default=443, action='store', help='Port to connect on.')
    parser.add_argument('-u', '--user', required=True, action='store', help='Username to use.')
    parser.add_argument('-p', '--password', required=True, action='store', help='Password to use.')

    parser.add_argument('--esxi_host', action='store', help='esxi host ip')
    parser.add_argument('--esxi_user', action='store', help='esxi host username')
    parser.add_argument('--esxi_password', action='store', help='esxi host password.')

    parser.add_argument('--pci_nics', action='store', help='pci nic ids to use for the VM')
    parser.add_argument('--sriov_nics', action='store', help='sriov nics to use for the VM')
    parser.add_argument('--sriov_dvs', action='store', help='sriov dvswitch')
    parser.add_argument('--sriov_dvs_pg', action='store', help='sriov port group')
    parser.add_argument('--vm_name', required=True, action='store', help='Name of the VM')

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

def poweroffvm(vm_obj):
    task = vm_obj.PowerOff()
    wait_for_task(task)

def fix_sriov_pg(si, dvs, dvs_pg_name):
    dvs_pg_obj = get_dvs_pg_obj(si, [vim.dvs.DistributedVirtualPortgroup], 
                                                    dvs_pg_name, dvs.name)
    dv_pg_spec = vim.dvs.DistributedVirtualPortgroup.ConfigSpec()
    dv_pg_spec.name = dvs_pg_name
    dv_pg_spec.configVersion = dvs_pg_obj.config.configVersion
    dv_pg_spec.type = vim.dvs.DistributedVirtualPortgroup.PortgroupType.earlyBinding
    dv_pg_spec.defaultPortConfig = vim.dvs.VmwareDistributedVirtualSwitch.VmwarePortConfigPolicy()
    dv_pg_spec.defaultPortConfig.securityPolicy = vim.dvs.VmwareDistributedVirtualSwitch.SecurityPolicy()
    dv_pg_spec.defaultPortConfig.securityPolicy.allowPromiscuous = vim.BoolPolicy(value=False)
    dv_pg_spec.defaultPortConfig.securityPolicy.macChanges = vim.BoolPolicy(value=True)
    dv_pg_spec.defaultPortConfig.securityPolicy.forgedTransmits = vim.BoolPolicy(value=True)
    dv_pg_spec.defaultPortConfig.securityPolicy.inherited = False
    dv_pg_spec.defaultPortConfig.uplinkTeamingPolicy = vim.VmwareUplinkPortTeamingPolicy()
    dv_pg_spec.defaultPortConfig.uplinkTeamingPolicy.uplinkPortOrder = vim.VMwareUplinkPortOrderPolicy()
    dv_pg_spec.defaultPortConfig.uplinkTeamingPolicy.uplinkPortOrder.activeUplinkPort = None
    task = dvs_pg_obj.ReconfigureDVPortgroup_Task(dv_pg_spec)
    wait_for_task(task)

def add_sriov_nics(args, vm, si_content):
    dvs = get_obj(si_content, [vim.DistributedVirtualSwitch], args.sriov_dvs)
    fix_sriov_pg(si_content, dvs, args.sriov_dvs_pg)
    sr_iov_nic_list = args.sriov_nics.rstrip(',')
    sr_iov_nic_list = sr_iov_nic_list.split(',')

    if vm.runtime.powerState == vim.VirtualMachinePowerState.poweredOn:
        print "VM:%s is powered ON. Cannot do hot pci add now. Shutting it down" %(args.vm_name)
        poweroffvm(vm)
    # get pci id of the sriov nic
    ssh_handle = paramiko.SSHClient()
    ssh_handle.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_handle.connect(args.esxi_host,
                       username = args.esxi_user,
                       password = args.esxi_password)
    cmd = "vmware -v"
    stdin, stdout, stderr = ssh_handle.exec_command(cmd)
    err = stderr.read()
    op = stdout.read()
    if err:
        self.log_and_raise_exception(err)
    esxi_version = op.split()[2][:3]
    for sr_iov_nic in sr_iov_nic_list:
        cmd = "vmkchdev -l | grep %s" %sr_iov_nic
        stdin, stdout, stderr = ssh_handle.exec_command(cmd)
        err = stderr.read()
        op = stdout.read()
        if err:
            self.log_and_raise_exception(err)
        nic_info = str(op)
        if len(nic_info) == 0:
            raise Exception("Unable to add sriov interface for physical nic %s \
                             on esxi host %s" %(sr_iov_nic, args.esxi_host))
        pci_id = nic_info.split()[0]
        if (esxi_version == '5.5'):
            pci_id = pci_id[5:]
        mac_address = None
        devices = []
        nicspec = vim.vm.device.VirtualDeviceSpec()
        nicspec.device = vim.vm.device.VirtualSriovEthernetCard()
        nicspec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
        nicspec.device.wakeOnLanEnabled = True
        nicspec.device.allowGuestOSMtuChange = True
        nicspec.device.deviceInfo = vim.Description()
        pg_obj = get_obj(si_content, [vim.dvs.DistributedVirtualPortgroup], args.sriov_dvs_pg)
        dvs_port_connection = vim.dvs.PortConnection()
        dvs_port_connection.portgroupKey = pg_obj.key
        dvs_port_connection.switchUuid = pg_obj.config.distributedVirtualSwitch.uuid
        nicspec.device.backing = vim.vm.device.VirtualEthernetCard.DistributedVirtualPortBackingInfo()
        nicspec.device.backing.port = dvs_port_connection
        nicspec.device.sriovBacking = vim.vm.device.VirtualSriovEthernetCard.SriovBackingInfo()
        nicspec.device.sriovBacking.physicalFunctionBacking = vim.vm.device.VirtualPCIPassthrough.DeviceBackingInfo()
        nicspec.device.sriovBacking.physicalFunctionBacking.id = pci_id
        if (mac_address):
           nicspec.device.addressType = "Manual"
           nicspec.device.macAddress = mac_address
        devices.append(nicspec)
        vmconf = vim.vm.ConfigSpec(deviceChange=devices)
        task = vm.ReconfigVM_Task(vmconf)
        wait_for_task(task)
        if not mac_address:
            for device in vm.config.hardware.device:
                if isinstance(device, vim.vm.device.VirtualSriovEthernetCard):
                      devices = []
                      mac_address = device.macAddress
                      nicspec = vim.vm.device.VirtualDeviceSpec()
                      nicspec.operation = vim.vm.device.VirtualDeviceSpec.Operation.edit
                      nicspec.device = device
                      nicspec.device.addressType = "Manual"
                      nicspec.device.macAddress = mac_address
                      devices.append(nicspec)
                      vmconf = vim.vm.ConfigSpec(deviceChange=devices)
                      task = vm.ReconfigVM_Task(vmconf)
                      wait_for_task(task)

def add_pci_nics(args, vm):
    pci_id_list = args.pci_nics.rstrip(',')
    pci_id_list = pci_id_list.split(',')
    pci_id_list.sort()
    if vm.runtime.powerState == vim.VirtualMachinePowerState.poweredOn:
        print "VM:%s is powered ON. Cannot do hot pci add now. Shutting it down" %(args.vm_name)
        poweroffvm(vm);
    for pci_id in pci_id_list:
        device_config_list = []
        found = False
        for device_list in vm.config.hardware.device:
            if (isinstance(device_list, vim.vm.device.VirtualPCIPassthrough)) == True \
                and device_list.backing.id == pci_id:
                print "pci_device already present! Not adding the pci device."
                found = True
                break
            if found == True:
                continue
            pci_passthroughs = vm.environmentBrowser.QueryConfigTarget(host=None).pciPassthrough
            for pci_entry in pci_passthroughs:
                if pci_entry.pciDevice.id == pci_id:
                    found = True
                    print "Found the pci device %s in the host" %(pci_id)
                    break
            if found == False:
                print "Did not find the pci passthrough device %s on the host" %(pci_id)
                exit(1)
            print "Adding PCI device to Contrail VM: %s" %(args.vm_name)
            deviceId = hex(pci_entry.pciDevice.deviceId % 2**16).lstrip('0x')
            backing = vim.VirtualPCIPassthroughDeviceBackingInfo(deviceId=deviceId,
                         id=pci_entry.pciDevice.id,
                         systemId=pci_entry.systemId,
                         vendorId=pci_entry.pciDevice.vendorId,
                         deviceName=pci_entry.pciDevice.deviceName)
            hba_object = vim.VirtualPCIPassthrough(key=-100, backing=backing)
            new_device_config = vim.VirtualDeviceConfigSpec(device=hba_object)
            new_device_config.operation = "add"
            new_device_config.device.connectable = vim.vm.device.VirtualDevice.ConnectInfo()
            new_device_config.device.connectable.startConnected = True
            device_config_list.append(new_device_config)
            vm_spec=vim.vm.ConfigSpec()
            vm_spec.deviceChange=device_config_list
            task=vm.ReconfigVM_Task(spec=vm_spec)
            wait_for_task(task)

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

    # get VM object
    vm_obj = get_obj(si_content, [vim.VirtualMachine], args.vm_name)
    if not vm_obj:
        print "VM %s not pressent" %(args.vm_name)
        exit(1)

    if args.pci_nics:
       add_pci_nics(args, vm_obj)

    if args.sriov_nics:
       add_sriov_nics(args, vm_obj, si_content)

    connect.Disconnect(si)

if __name__ == "__main__":
    exit(main())
