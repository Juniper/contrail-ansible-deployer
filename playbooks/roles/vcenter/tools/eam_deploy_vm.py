#!/usr/bin/env python

from pyVmomi import vim, eam, VmomiSupport, SoapStubAdapter
from pyVim import connect
from argparse import ArgumentParser

import sys
import ssl

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

def CreateAgencyConfig(si, args):
    content = si.RetrieveContent()

    agency_config = eam.Agency.ConfigInfo()
    agency_config.agencyName = "ContrailVM-Agency"

    agent_config_list = []

    agent_config = eam.Agent.ConfigInfo()
    agent_config.dvFilterEnabled = False

    agent_config.ovfPackageUrl = args.ova_path 

    ovf_env = eam.Agent.OvfEnvironmentInfo()
    ovf_prop_list = []
    ovf_env_prop = eam.Agent.OvfEnvironmentInfo.OvfProperty()
    ovf_env_prop.key = "vcenter-ip"
    ovf_env_prop.value = "10.84.16.51"
    ovf_prop_list.append(ovf_env_prop)

    ovf_env_prop = eam.Agent.OvfEnvironmentInfo.OvfProperty()
    ovf_env_prop.key = "vcenter-username"
    ovf_env_prop.value = "administrator@vsphere.local"
    ovf_prop_list.append(ovf_env_prop)

    ovf_env_prop = eam.Agent.OvfEnvironmentInfo.OvfProperty()
    ovf_env_prop.key = "vcenter-password"
    ovf_env_prop.value = "Contrail123!"
    ovf_prop_list.append(ovf_env_prop)

    ovf_env_prop = eam.Agent.OvfEnvironmentInfo.OvfProperty()
    ovf_env_prop.key = "esxi-username"
    ovf_env_prop.value = "root"
    ovf_prop_list.append(ovf_env_prop)

    ovf_env_prop = eam.Agent.OvfEnvironmentInfo.OvfProperty()
    ovf_env_prop.key = "esxi-password"
    ovf_env_prop.value = "c0ntrail123"
    ovf_prop_list.append(ovf_env_prop)

    ovf_env.ovfProperty = ovf_prop_list

    agent_config.ovfEnvironment = ovf_env

    agent_config_list.append(agent_config)
    agency_config.agentConfig = agent_config_list

    agency_config.agentName = "ContrailVM"
    agency_config.manuallyMarkAgentVmAvailableAfterPowerOn = True
    agency_config.manuallyMarkAgentVmAvailableAfterProvisioning = True
    agency_config.optimizedDeploymentEnabled = False
    agency_config.preferHostConfiguration = True

    compute_host = get_obj(content, [vim.ClusterComputeResource], "amudha-cluster")
    compute_scope = eam.Agency.ComputeResourceScope()
    compute_scope.computeResource.append(compute_host)
    agency_config.scope = compute_scope

    return agency_config

def ConnectEAM(si, vpxdStub, sslContext):
    hostname = vpxdStub.host.split(":")[0]
   
    eamStub = SoapStubAdapter(host=hostname,
                                      version = "eam.version.version1",
                                      path = "/eam/sdk",
                                      poolSize=0,
                                      sslContext=sslContext)
    eamStub.cookie = vpxdStub.cookie
    eamCx = eam.EsxAgentManager("EsxAgentManager", eamStub)

    return eamCx

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

    # Populate Agency and AgentVM configuration
    agency_config = CreateAgencyConfig(si, args) 

    # Connect to EAM endpoint
    eamCx = ConnectEAM(si, si._stub, context)

    # Query and find if ContrailVM-Agency is existing
    agencies = eamCx.QueryAgency()
    if agencies:
       for agency in agencies:
           agency_name = agency.QueryConfig().agencyName
           if agency_name == "ContrailVM-Agency":
              agency.Update(agency_config)
              return
           else:
              create_agency = 1
    else:
       create_agency = 1

    if create_agency == 1:
       # Create Agency and spawn AgentVMs
       eamCx.CreateAgency(agency_config, "enabled")


# Start program
if __name__ == "__main__":
    main()
