#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Dan Smith <danms@us.ibm.com>
#    Kaitlin Rupert <karupert@us.ibm.com>
#    Zhengang Li <lizg@cn.ibm.com>
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

import pywbem
from CimTest.CimExt import CIMMethodClass, CIMClassMOF
from CimTest import Globals
from VirtLib import live
from XenKvmLib import const
from XenKvmLib.classes import get_typed_class, get_class_type, virt_types

RASD_TYPE_PROC = 3
RASD_TYPE_MEM = 4
RASD_TYPE_NET_ETHER = 10
RASD_TYPE_NET_OTHER = 11
RASD_TYPE_DISK = 17

VSSD_RECOVERY_NONE     = 2
VSSD_RECOVERY_RESTART  = 3
VSSD_RECOVERY_PRESERVE = 123

def eval_cls(basename):
    def func(f):
        def body(virt):
            if virt in virt_types:
                return eval(get_typed_class(virt, basename))
        return body
    return func

class CIM_VirtualSystemManagementService(CIMMethodClass):
    conn = None
    inst = None

    def __init__(self, server):
        
        self.conn = pywbem.WBEMConnection('http://%s' % server,
                                          (Globals.CIM_USER, Globals.CIM_PASS),
                                          Globals.CIM_NS)
        
        self.inst = self.__class__.__name__


class Xen_VirtualSystemManagementService(CIM_VirtualSystemManagementService):
    pass

class KVM_VirtualSystemManagementService(CIM_VirtualSystemManagementService):
    pass

class LXC_VirtualSystemManagementService(CIM_VirtualSystemManagementService):
    pass

@eval_cls('VirtualSystemManagementService')
def get_vsms_class(virt):
    pass

def enumerate_instances(server, virt='Xen'):
    conn = pywbem.WBEMConnection('http://%s' % server,
                                 (Globals.CIM_USER, Globals.CIM_PASS),
                                 Globals.CIM_NS)

    cn = get_typed_class(virt, 'VirtualSystemManagementService')
    try:
        instances = conn.EnumerateInstances(cn)
    except pywbem.CIMError, arg:
        print arg[1]
        return []

    return instances 

# classes to define VSSD parameters
class CIM_VirtualSystemSettingData(CIMClassMOF):
    def __init__(self, name, virt):
        type = get_class_type(self.__class__.__name__)
        self.InstanceID = '%s:%s' % (type, name)
        self.Caption = self.Description = 'Virtual System'
        self.VirtualSystemIdentifier = self.ElementName = name
        self.VirtualSystemType = type
        self.CreationClassName = self.__class__.__name__
        self.AutomaticShutdownAction = VSSD_RECOVERY_NONE
        self.AutomaticRecoveryAction = VSSD_RECOVERY_NONE

        self.isFullVirt = (type == 'KVM' or virt == 'XenFV')
        if self.isFullVirt:
            self.BootDevice = 'hd'
        elif type == 'LXC':
            self.InitPath = const.LXC_init_path
        else:
            self.Kernel = const.Xen_kernel_path
            self.Ramdisk = const.Xen_init_path
 

class Xen_VirtualSystemSettingData(CIM_VirtualSystemSettingData):
    pass

class KVM_VirtualSystemSettingData(CIM_VirtualSystemSettingData):
    pass

class LXC_VirtualSystemSettingData(CIM_VirtualSystemSettingData):
    pass

@eval_cls('VirtualSystemSettingData')
def get_vssd_class(virt):
    pass

# classes to define RASD parameters
class CIM_DiskResourceAllocationSettingData(CIMClassMOF):
    def __init__(self, dev, source, name):
        self.ResourceType = RASD_TYPE_DISK
        if dev != None:
            self.VirtualDevice = dev
            self.InstanceID = '%s/%s' % (name, dev)
        if source != None:
            self.Address = source

class Xen_DiskResourceAllocationSettingData(CIM_DiskResourceAllocationSettingData):
    pass

class KVM_DiskResourceAllocationSettingData(CIM_DiskResourceAllocationSettingData):
    pass

class LXC_DiskResourceAllocationSettingData(CIMClassMOF):
    def __init__(self, mountpoint, source, name):
        self.MountPoint = mountpoint
        self.Address = source
        self.InstanceID = '%s/%s' % (name, mountpoint)

@eval_cls('DiskResourceAllocationSettingData')
def get_dasd_class(virt):
    pass

class CIM_NetResourceAllocationSettingData(CIMClassMOF):
    def __init__(self, type, mac, name, virt_net=None): 
        self.Address = mac
        self.NetworkType = type
        self.ResourceType = RASD_TYPE_NET_ETHER

        if virt_net != None :
            self.PoolID = "NetworkPool/%s" % virt_net
        
        if mac != None:
            self.InstanceID = '%s/%s' % (name, mac)

class Xen_NetResourceAllocationSettingData(CIM_NetResourceAllocationSettingData):
    pass

class KVM_NetResourceAllocationSettingData(CIM_NetResourceAllocationSettingData):
    pass

class LXC_NetResourceAllocationSettingData(CIM_NetResourceAllocationSettingData):
    pass

@eval_cls('NetResourceAllocationSettingData')
def get_nasd_class(virt):
    pass

class CIM_ProcResourceAllocationSettingData(CIMClassMOF):
    def __init__(self, vcpu, name, weight=None, limit=None):
        self.ResourceType = RASD_TYPE_PROC
        
        if vcpu != None:
            self.VirtualQuantity = vcpu
        
        if name != None:
            self.InstanceID = '%s/proc' % name

        if weight != None:
            self.Weight = weight

        if limit != None:
            self.Limit = limit 

class Xen_ProcResourceAllocationSettingData(CIM_ProcResourceAllocationSettingData):
    pass

class KVM_ProcResourceAllocationSettingData(CIM_ProcResourceAllocationSettingData):
    pass

class LXC_ProcResourceAllocationSettingData(CIM_ProcResourceAllocationSettingData):
    pass

@eval_cls('ProcResourceAllocationSettingData')
def get_pasd_class(virt):
    pass

class CIM_MemResourceAllocationSettingData(CIMClassMOF):
    def __init__(self, name,  megabytes=512, mallocunits="MegaBytes"):
        self.ResourceType = RASD_TYPE_MEM
        
        if megabytes != None:
            self.VirtualQuantity = megabytes

        if mallocunits != None:
            self.AllocationUnits = mallocunits
        
        if name != None:
            self.InstanceID = '%s/mem' % name

class Xen_MemResourceAllocationSettingData(CIM_MemResourceAllocationSettingData):
    pass

class KVM_MemResourceAllocationSettingData(CIM_MemResourceAllocationSettingData):
    pass

class LXC_MemResourceAllocationSettingData(CIM_MemResourceAllocationSettingData):
    pass

@eval_cls('MemResourceAllocationSettingData')
def get_masd_class(virt):
    pass

def default_vssd_rasd_str(dom_name='test_domain', 
                          disk_dev='xvda',
                          disk_source=const.Xen_disk_path,
                          net_type='ethernet',
                          net_mac=const.Xen_default_mac,
                          proc_vcpu=1,
                          mem_mb=512,
                          malloc_units="MegaBytes",
                          virt='Xen'):
    class_vssd = get_vssd_class(virt)
    vssd = class_vssd(name=dom_name, virt=virt)

    # LXC only takes disk and memory device for now.
    # Only disk __init__ takes different params.
    if virt == 'LXC':
        d = LXC_DiskResourceAllocationSettingData(
                mountpoint=const.LXC_default_mp,
                source=const.LXC_default_source, name=dom_name)
    else:
        class_dasd = get_dasd_class(virt)
        if virt == 'KVM':
            disk_dev = 'hda'
            disk_source = const.KVM_disk_path
        elif virt == 'XenFV':
            disk_dev = 'hda'
            disk_source = const.XenFV_disk_path
        d = class_dasd(
                    dev=disk_dev, 
                    source=disk_source,
                    name=dom_name)
    
    class_masd = get_masd_class(virt)
    m = class_masd(
                megabytes=mem_mb,
                mallocunits=malloc_units,
                name=dom_name)
    if virt == 'LXC':
        return vssd.mof(), [d.mof(), m.mof()]
    
    class_nasd = get_nasd_class(virt)
    if virt == 'KVM':
        net_mac= const.KVM_default_mac
    elif virt == 'XenFV':
        net_mac = const.XenFV_default_mac
    n = class_nasd(
                type=net_type, 
                mac=net_mac,
                name=dom_name)
    class_pasd = get_pasd_class(virt)
    p = class_pasd(
                vcpu=proc_vcpu,
                name=dom_name)

    return vssd.mof(), [d.mof(), n.mof(), p.mof(), m.mof()]

