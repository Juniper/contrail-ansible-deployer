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

    parser.add_argument('--datacenter',
                        required=False,
                        action='store',
                        default=None,
                        help='Name of the datacenter.')

    parser.add_argument('--cluster_list',
                        required=False,
                        action='store',
                        default=None,
                        help='Name of the cluster to deploy VM.')

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

def get_clusters_from_datacenter(datacenter):
    clusters = {}
    for child in datacenter.hostFolder.childEntity:
        if isinstance(child, vim.ClusterComputeResource):
            clusters[child.name] = child
    return clusters

def CreateAgencyConfig(si, args, scope):
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
    ovf_env_prop.value = args.host
    ovf_prop_list.append(ovf_env_prop)

    ovf_env_prop = eam.Agent.OvfEnvironmentInfo.OvfProperty()
    ovf_env_prop.key = "vcenter-username"
    ovf_env_prop.value = args.user
    ovf_prop_list.append(ovf_env_prop)

    ovf_env_prop = eam.Agent.OvfEnvironmentInfo.OvfProperty()
    ovf_env_prop.key = "vcenter-password"
    ovf_env_prop.value = args.password
    ovf_prop_list.append(ovf_env_prop)

    ovf_env_prop = eam.Agent.OvfEnvironmentInfo.OvfProperty()
    ovf_env_prop.key = "datacenter"
    ovf_env_prop.value = args.datacenter
    ovf_prop_list.append(ovf_env_prop)

    ovf_env.ovfProperty = ovf_prop_list

    agent_config.ovfEnvironment = ovf_env

    agent_config_list.append(agent_config)
    agency_config.agentConfig = agent_config_list

    agency_config.agentName = "ContrailVM"

    compute_scope = eam.Agency.ComputeResourceScope()
    datacenter = get_obj(content, [vim.Datacenter], args.datacenter)
    cluster_names = args.cluster_list.rstrip(',')
    cluster_names = cluster_names.split(',')
    clusters = get_clusters_from_datacenter(datacenter)
    for cluster_name in cluster_names:
        compute = clusters.get(cluster_name)
        if compute is None:
            print "Unable to find cluster %s in %s datacenter" % (cluster_name, args.datacenter)
            continue
        if scope and scope.computeResource:
           compute_scope = scope
           if compute not in scope.computeResource:
              compute_scope.computeResource.append(compute)
        else:
           compute_scope.computeResource.append(compute)
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

    # Connect to EAM endpoint
    eamCx = ConnectEAM(si, si._stub, context)

    # Query and find if ContrailVM-Agency is existing
    agencies = eamCx.QueryAgency()
    if agencies:
       for agency in agencies:
           agency_name = agency.QueryConfig().agencyName
           if agency_name == "ContrailVM-Agency":
              scope = agency.QueryConfig().scope
              agency_config = CreateAgencyConfig(si, args, scope)
              agency.Update(agency_config)
              return
           else:
              create_agency = True
    else:
       create_agency = True

    if create_agency:
       # Populate Agency and AgentVM configuration
       agency_config = CreateAgencyConfig(si, args, None)
       # Create Agency and spawn AgentVMs
       eamCx.CreateAgency(agency_config, "enabled")

    connect.Disconnect(si)
    return 0

# Start program
if __name__ == "__main__":
    main()
