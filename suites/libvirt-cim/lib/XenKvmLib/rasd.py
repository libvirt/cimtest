#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Deepti B. Kalakeri <dkalaker@in.ibm.com>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307  USA
#

import sys
from CimTest.Globals import logger
from CimTest.ReturnCodes import FAIL, PASS
from XenKvmLib import vxml
from XenKvmLib import const
from XenKvmLib.classes import get_typed_class, get_class_type
from XenKvmLib.enumclass import GetInstance, EnumInstances
from XenKvmLib.assoc import Associators 
from XenKvmLib.const import default_pool_name, default_network_name, \
                            get_provider_version, default_net_type
from XenKvmLib.pool import enum_volumes
from XenKvmLib.xm_virt_util import virsh_version
from XenKvmLib.common_util import parse_instance_id

pasd_cn = 'ProcResourceAllocationSettingData'
nasd_cn = 'NetResourceAllocationSettingData'
dasd_cn = 'DiskResourceAllocationSettingData'
masd_cn = 'MemResourceAllocationSettingData'
dcrasd_cn = 'GraphicsResourceAllocationSettingData'
irasd_cn = 'InputResourceAllocationSettingData'
dpasd_cn = 'DiskPoolResourceAllocationSettingData'
npasd_cn = 'NetPoolResourceAllocationSettingData'
svrasd_cn = 'StorageVolumeResourceAllocationSettingData'


proccn =  'Processor'
memcn  =  'Memory'
netcn  =  'NetworkPort'
diskcn =  'LogicalDisk'
dccn = 'DisplayController'
pdcn = 'PointingDevice'

libvirt_rasd_storagepool_changes = 934

def rasd_init_list(vsxml, virt, t_disk, t_dom, t_mac, t_mem, server):
    """
        Creating the lists that will be used for comparisons.
    """
    rasd_values =  { }
    proc_cn = get_typed_class(virt, proccn)
    mem_cn = get_typed_class(virt, memcn)
    net_cn = get_typed_class(virt, netcn)
    disk_cn = get_typed_class(virt, diskcn)
    dc_cn = get_typed_class(virt, dccn)
    pd_cn = get_typed_class(virt, pdcn)

    in_list = { 'proc'    :      proc_cn,
                'mem'     :      mem_cn,
                'net'     :      net_cn,
                'disk'    :      disk_cn,
                'display' :      dc_cn,
                'point'    :     pd_cn
               }
    try:

        disk_path = vsxml.xml_get_disk_source()
        if virt == 'LXC':
           disk_path = '/var/lib/libvirt/images/lxc_files'

        libvirt_version = virsh_version(server, virt)

        if virt == 'LXC' or (virt == 'XenFV' and libvirt_version < "0.6.3"):
           point_device = "%s/%s" %(t_dom, "mouse:usb")
        elif virt == 'Xen':
           point_device = "%s/%s" %(t_dom, "mouse:xen")
        else:
           point_device = "%s/%s" %(t_dom, "mouse:ps2")
        rasd_values = { 
                        proc_cn  : {
                                     "InstanceID"   : '%s/%s' %(t_dom, "proc"),
                                     "ResourceType" : 3,
                                    }, 
                        disk_cn  : {
                                     "InstanceID"   : '%s/%s' %(t_dom, t_disk), 
                                     "ResourceType" : 17, 
                                     "Address"      : disk_path, 
                                    }, 
                        net_cn   : {
                                    "InstanceID"   : '%s/%s' %(t_dom, t_mac), 
                                    "ResourceType" : 10 , 
                                    "ntype"        : [ 'bridge', 'user',
                                                         'network', 'ethernet'] 
                                      }, 
                        mem_cn   : {
                                    "InstanceID" : '%s/%s' %(t_dom, "mem"), 
                                    "ResourceType"    : 4, 
                                    "AllocationUnits" : "KiloBytes",
                                    "VirtualQuantity" : (t_mem * 1024),
                                  },
                        dc_cn   : {
                                    "InstanceID" : "%s/%s" %(t_dom, "vnc")
                                  },
                        pd_cn   : {
                                    "InstanceID" : point_device
                                  }
                      } 
    except Exception, details:
        logger.error("Exception: In fn rasd_init_list %s", details)
        return FAIL, rasd_values, in_list

    nettype   = vsxml.xml_get_net_type()
    if not nettype in rasd_values[net_cn]['ntype']:
        logger.info("Adding the %s net type", nettype)
        rasd_values[net_cn]['ntype'].append(nettype)

    return PASS, rasd_values, in_list

def CCN_err(assoc_info, list):
    logger.error("%s Mismatch", 'CreationClassName')
    logger.error("Returned %s instead of %s", 
                  assoc_info['CreationClassName'], list['CreationClassName'])
    
def RType_err(assoc_info, list):
    logger.error("%s Mismatch", 'ResourceType')
    logger.error("Returned %s instead of %s", 
                  assoc_info['ResourceType'], list['ResourceType'])

def InstId_err(assoc_info, list):
    logger.error("%s Mismatch", 'InstanceID')
    logger.error("Returned %s instead of %s", 
                  assoc_info['InstanceID'], list['InstanceID'])

def verify_displayrasd_values(assoc_info, displayrasd_list):
    status = PASS
    if assoc_info['InstanceID'] != displayrasd_list['InstanceID']:
        InstId_err(assoc_info, displayrasd_list)
        status = FAIL
    return status

def verify_inputrasd_values(assoc_info, inputrasd_list):
    status = PASS
    if assoc_info['InstanceID'] != inputrasd_list['InstanceID']:
        InstId_err(assoc_info, inputrasd_list)
        status = FAIL
    return status

def verify_procrasd_values(assoc_info, procrasd_list):
    status = PASS
    if assoc_info['InstanceID'] != procrasd_list['InstanceID']:
        InstId_err(assoc_info, procrasd_list)
        status = FAIL
    if assoc_info['ResourceType'] != procrasd_list['ResourceType']:
        RType_err(assoc_info, procrasd_list)
        status = FAIL
    return status

def verify_netrasd_values(assoc_info, netrasd_list):
    status = PASS
    if assoc_info['InstanceID'] != netrasd_list['InstanceID']:
        InstId_err(assoc_info, netrasd_list)
        status = FAIL
    if assoc_info['ResourceType'] != netrasd_list['ResourceType']:
        RType_err(assoc_info, netrasd_list)
        status = FAIL
    if not assoc_info['NetworkType'] in netrasd_list['ntype']:
        logger.error("%s Mismatch", 'NetworkType')
        logger.error("Returned '%s' instead of returning one of %s types",
                      assoc_info['NetworkType'], netrasd_list['ntype'])
        status = FAIL
    return status

def verify_diskrasd_values(assoc_info, diskrasd_list):
    status = PASS
    if assoc_info['InstanceID'] != diskrasd_list['InstanceID']:
        InstId_err(assoc_info, diskrasd_list)
        status = FAIL
    if assoc_info['ResourceType'] != diskrasd_list['ResourceType']:
        RType_err(assoc_info, diskrasd_list)
        status = FAIL
    if assoc_info['Address'] != diskrasd_list['Address']:
        logger.error("%s Mismatch", 'Address')
        logger.error("Returned %s instead of %s ", 
                      assoc_info['Address'], diskrasd_list['Address'])
        status = FAIL
    return status

def verify_memrasd_values(assoc_info, memrasd_list):
    status = PASS
    if assoc_info['InstanceID'] != memrasd_list['InstanceID']:
        InstId_err(assoc_info, memrasd_list)
        status = FAIL
    if assoc_info['ResourceType'] != memrasd_list['ResourceType']:
        RType_err(assoc_info, memrasd_list)
        status = FAIL
    if assoc_info['AllocationUnits'] != memrasd_list['AllocationUnits']:
        logger.error("%s Mismatch", 'AllocationUnits')
        logger.error("Returned %s instead of %s ", 
                     assoc_info['AllocationUnits'], 
                     memrasd_list['AllocationUnits'])
        status = FAIL 
    if assoc_info['VirtualQuantity'] != memrasd_list['VirtualQuantity']:
        logger.error("%s mismatch", 'VirtualQuantity')
        logger.error("Returned %s instead of %s ", 
                      assoc_info['VirtualQuantity'], 
                      memrasd_list['VirtualQuantity'])
        status = FAIL 
    return status

def get_rasd_templates(host_ip, type, pool_id):
    ac_cn = get_typed_class(type, "AllocationCapabilities")
    an_cn = get_typed_class(type, "SettingsDefineCapabilities")

    templates = []

    try:
        key_list = {"InstanceID" : pool_id }

        inst = GetInstance(host_ip, ac_cn, key_list)

        temps = Associators(host_ip, an_cn, ac_cn, InstanceID=inst.InstanceID)

        for temp in temps:
            templates.append(temp)

    except Exception, detail:
        logger.error("Exception: %s", detail)

    return templates

def get_default_rasds(host_ip, type):
    ac_id_list = [ "MemoryPool/0", 
                   "DiskPool/%s" % default_pool_name, 
                 ]

    if type == "LXC":
        if const.LXC_netns_support is True:
            ac_id_list.append("NetworkPool/%s" % default_network_name)
    else:
            ac_id_list.append("NetworkPool/%s" % default_network_name)
            ac_id_list.append("ProcessorPool/0")

    net_cn = "NetResourceAllocationSettingData"

    templates = [] 
    
    for id in ac_id_list:
        rasd_list = get_rasd_templates(host_ip, type, id)
        if len(rasd_list) < 1:
            logger.info("No RASD templates returned for %s", id)
            return []

        for rasd in rasd_list:
            if rasd['InstanceID'] == "Default":
                if rasd.classname.find(net_cn) > 0 and \
                   rasd['NetworkType'] != default_net_type:
                    continue
                templates.append(rasd)

    return templates

def get_default_rasd_mofs(host_ip, type):
    rasds = get_default_rasds(ip, virt)

    rasd_mofs = []

    #FIXME for libcmpiutil versions 0.4 and later, inst_to_mof() is needed.
    #This should be changed to rasd.tomof() once version 0.4 is obsolete.
    for rasd in rasds:
        rasd_mofs.append(inst_to_mof(rasd))

    return rasd_mofs

def rasd_cn_to_pool_cn(rasd_cn, virt):
    if rasd_cn.find('ProcResourceAllocationSettingData') >= 0:
        return get_typed_class(virt, "ProcessorPool")
    elif rasd_cn.find('NetResourceAllocationSettingData') >= 0:
        return get_typed_class(virt, "NetworkPool")
    elif rasd_cn.find('DiskResourceAllocationSettingData') >= 0:
        return get_typed_class(virt, "DiskPool")
    elif rasd_cn.find('MemResourceAllocationSettingData') >= 0:
        return get_typed_class(virt, "MemoryPool")
    elif rasd_cn.find('GraphicsResourceAllocationSettingData') >= 0:
        return get_typed_class(virt, "GraphicsPool")
    elif rasd_cn.find('InputResourceAllocationSettingData') >= 0:
        return get_typed_class(virt, "InputPool")
    else:
        return None 

def enum_rasds(virt, ip):
    rasd_insts = {}

    try:
        rasd_cn = get_typed_class(virt, 'ResourceAllocationSettingData')
        enum_list = EnumInstances(ip, rasd_cn)

        if enum_list < 1:
            logger.error("No RASD instances returned")
            return rasd_insts, FAIL

        for rasd in enum_list:
            if rasd.Classname not in rasd_insts.keys():
                rasd_insts[rasd.Classname] = []
            rasd_insts[rasd.Classname].append(rasd)

    except Exception, details:
        logger.error(details)
        return rasd_insts, FAIL

    return rasd_insts, PASS

def get_exp_disk_rasd_len(virt, ip, rev, id):
    libvirt_rasd_template_changes = 707
    libvirt_rasd_new_changes = 805
    libvirt_rasd_dpool_changes = 839
    libvirt_rasd_floppy_changes = 1023
    libvirt_rasd_stvol_unit_changes = 1025

    libvirt_ver = virsh_version(ip, virt)

    # For Diskpool, we have info 1 for each of Min, Max, Default, and Incr
    exp_base_num = 4
    exp_cdrom = 4

    # StoragePoolRASD record 1 for each of Min, Max, Default, and Incr
    exp_storagevol_rasd = 4
    exp_len = exp_base_num 
   
    # StoragePoolRASD record with AllocationUnits=G 1 for each \
    # of Min, Max, Default,  Incr
    exp_storagevol_unit_changes = 4

    # Floppy record 1 for each of Min, Max, Default, and Incr
    exp_floppy = 4

    if id == "DiskPool/0":
        pool_types = 7
        return exp_base_num * pool_types 
    
    if virt == 'Xen' or virt == 'XenFV':
        # For Xen and XenFV, there is a template for PV and FV, so you 
        # end up with double the number of templates
        xen_multi = 2

        if rev >= libvirt_rasd_template_changes and \
           rev < libvirt_rasd_new_changes:
            exp_len = exp_base_num + exp_cdrom

        elif rev >= libvirt_rasd_dpool_changes and libvirt_ver >= '0.4.1':
            volumes = enum_volumes(virt, ip)
            if rev >= libvirt_rasd_floppy_changes:
                exp_len = ((volumes * exp_base_num) + \
                           exp_cdrom + exp_floppy) * xen_multi
            else:
                exp_len = ((volumes * exp_base_num) + exp_cdrom) * xen_multi

        else:
            exp_len = (exp_base_num + exp_cdrom) * xen_multi 

    elif virt == 'KVM':
        if rev >= libvirt_rasd_new_changes and \
           rev < libvirt_rasd_dpool_changes:
            exp_len = exp_base_num + exp_cdrom

        elif rev >= libvirt_rasd_dpool_changes:
            id = parse_instance_id(id)
            volumes = enum_volumes(virt, ip, id[1])

            if rev >= libvirt_rasd_floppy_changes:
                exp_len = (volumes * exp_base_num) + exp_cdrom + exp_floppy
            else:
                exp_len = (volumes * exp_base_num) + exp_cdrom 


    if virt != 'LXC' and libvirt_ver >= '0.4.1':
        if rev >= libvirt_rasd_storagepool_changes:
            exp_len += exp_storagevol_rasd

        if rev >= libvirt_rasd_stvol_unit_changes:
            exp_len +=  exp_storagevol_unit_changes

    return exp_len

def get_exp_net_rasd_len(virt, rev, id):
    net_rasd_template_changes = 861 
    net_rasd_direct_nettype_changes = 1029
    net_rasd_vsi_nettype_changes = 1043

    # NetRASD record for Direct NetType 1 for each min, max, incr, default
    exp_direct = 4

    exp_base_num = 4
    dev_types = 2
    net_types = 3

    if id == "NetworkPool/0":
        pool_types = 3
        forward_modes = 2

        return (exp_base_num * pool_types) + (exp_base_num * forward_modes) 
    
    if rev >= net_rasd_template_changes:
        exp_base_num = exp_base_num * dev_types * net_types

    if rev >= net_rasd_direct_nettype_changes:
        exp_base_num += exp_direct

    if rev >= net_rasd_vsi_nettype_changes:
        exp_base_num = 4 * (dev_types * net_types + exp_direct)

    return exp_base_num

def get_exp_template_rasd_len(virt, ip, id):
    curr_cim_rev, changeset = get_provider_version(virt, ip)

    exp_len = 4 

    if 'DiskPool' in id:
        exp_len = get_exp_disk_rasd_len(virt, ip, curr_cim_rev, id)

    elif 'NetworkPool' in id:
        exp_len = get_exp_net_rasd_len(virt, curr_cim_rev, id)

    return exp_len


