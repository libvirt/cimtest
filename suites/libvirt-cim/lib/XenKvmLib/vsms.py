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
from XenKvmLib import const
from XenKvmLib.classes import get_typed_class, get_class_type, virt_types

RASD_TYPE_PROC = 3
RASD_TYPE_MEM = 4
RASD_TYPE_NET_ETHER = 10
RASD_TYPE_NET_OTHER = 11
RASD_TYPE_DISK = 17
RASD_TYPE_GRAPHICS = 24
RASD_TYPE_INPUT = 13
RASD_TYPE_STOREVOL = 32768
RASD_TYPE_CONTROLLER = 32771

VIRT_DISK_TYPE_DISK = 0
VIRT_DISK_TYPE_CDROM = 1
VIRT_DISK_TYPE_FLOPPY = 2

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
    def __init__(self, name, virt, uuid=None, bldr=None, emulator=None,
                 pae=False, acpi=False, apic=False):
        type = get_class_type(self.__class__.__name__)
        self.InstanceID = '%s:%s' % (type, name)
        self.Caption = self.Description = 'Virtual System'
        self.VirtualSystemIdentifier = self.ElementName = name
        self.VirtualSystemType = type
        self.CreationClassName = self.__class__.__name__
        self.AutomaticShutdownAction = VSSD_RECOVERY_NONE
        self.AutomaticRecoveryAction = VSSD_RECOVERY_NONE

        if emulator is not None:
            self.Emulator = emulator 

        self.isFullVirt = (type == 'KVM' or virt == 'XenFV')
        if self.isFullVirt:
            self.BootDevice = 'hd'
        elif type == 'LXC':
            self.InitPath = const.LXC_init_path
        else:
            self.Kernel = const.Xen_kernel_path
            self.Ramdisk = const.Xen_init_path

        if bldr is not None:
            self.Bootloader = bldr
 
        if uuid is not None:
            self.UUID = uuid

        self.EnablePAE = pae 
        self.EnableACPI = acpi 
        self.EnableAPIC = apic

class Xen_VirtualSystemSettingData(CIM_VirtualSystemSettingData):
    pass

class KVM_VirtualSystemSettingData(CIM_VirtualSystemSettingData):
    pass

class LXC_VirtualSystemSettingData(CIM_VirtualSystemSettingData):
    pass

def get_vssd_mof(virt, dom_name, uuid=None, bldr=None, pae=False, acpi=False,
                 apic=False):
    vssd_cn = eval(get_typed_class(virt, "VirtualSystemSettingData"))
    vssd = vssd_cn(dom_name, virt, uuid=uuid, bldr=bldr, pae=pae, acpi=acpi,
                   apic=apic)
    return vssd.mof()

# classes to define RASD parameters
class CIM_DiskResourceAllocationSettingData(CIMClassMOF):
    def __init__(self, dev, source, name, instanceid=None, emu_type=None):
        self.ResourceType = RASD_TYPE_DISK
        if emu_type != None:
            self.EmulatedType = emu_type
        if dev != None:
            self.VirtualDevice = dev
            self.InstanceID = '%s/%s' % (name, dev)
        if instanceid != None:
            self.InstanceID = instanceid
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
        self.NetworkType = type
        self.ResourceType = RASD_TYPE_NET_ETHER

        if mac != None:
            self.Address = mac

        if virt_net != None :
            if type == 'network':
                self.PoolID = "NetworkPool/%s" % virt_net
            elif type == 'bridge':
                self.NetworkName = virt_net
        
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
    def __init__(self, name, vcpu=None, weight=None, limit=None):
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


class CIM_GraphicsResourceAllocationSettingData(CIMClassMOF):
    def __init__(self, name, res_sub_type="vnc", ip=None, ipv6_flag=None, 
                 lport='-1', keymap="en-us", vnc_passwd=None):
        self.InstanceID = '%s/graphics' %name
        self.ResourceType = RASD_TYPE_GRAPHICS

        if res_sub_type != None: 
            self.ResourceSubType = res_sub_type

        if ip != None and lport != None:
           self.Address = '%s:%s' % (ip, lport)

        else:
           self.Address = None

        if ipv6_flag != None:
           self.IsIPv6Only = ipv6_flag
        
        if keymap != None:
           self.KeyMap = keymap
        
        if vnc_passwd != None:
           self.Password = vnc_passwd
  

class Xen_GraphicsResourceAllocationSettingData(CIM_GraphicsResourceAllocationSettingData):
    pass

class KVM_GraphicsResourceAllocationSettingData(CIM_GraphicsResourceAllocationSettingData):
    pass

class LXC_GraphicsResourceAllocationSettingData(CIM_GraphicsResourceAllocationSettingData):
    pass

@eval_cls('GraphicsResourceAllocationSettingData')
def get_gasd_class(virt):
    pass

class CIM_InputResourceAllocationSettingData(CIMClassMOF):
    def __init__(self, name, res_sub_type=None, bus_type=None):
        self.InstanceID = '%s' % name
        self.ResourceType = RASD_TYPE_INPUT

        if res_sub_type != None: 
            self.ResourceSubType = res_sub_type
            self.InstanceID += '/%s' % res_sub_type

        if bus_type != None:
           self.BusType = bus_type
           self.InstanceID += ':%s' % bus_type

class Xen_InputResourceAllocationSettingData(CIM_InputResourceAllocationSettingData):
    pass

class KVM_InputResourceAllocationSettingData(CIM_InputResourceAllocationSettingData):
    pass

class LXC_InputResourceAllocationSettingData(CIM_InputResourceAllocationSettingData):
    pass

@eval_cls('InputResourceAllocationSettingData')
def get_iasd_class(virt):
    pass
  
class CIM_ControllerResourceAllocationSettingData(CIMClassMOF):
    def __init__(self, name, ctl_sub_type=None, ctl_index=-1, ctl_model=None):
        self.InstanceID = '%s/controller:' % name
        self.ResourceType = RASD_TYPE_CONTROLLER

        if ctl_sub_type is not None:
            self.ResourceSubType = ctl_sub_type
            self.InstanceID += '%s' % ctl_sub_type

        if ctl_index >= 0:
            self.Index = ctl_index
            self.InstanceID += ':%d' % ctl_index

        if ctl_model is not None:
            self.Model = ctl_model

class KVM_ControllerResourceAllocationSettingData(CIM_ControllerResourceAllocationSettingData):
    pass

@eval_cls('ControllerResourceAllocationSettingData')
def get_ctlasd_class(virt):
    pass

def default_vssd_rasd_str(dom_name='test_domain', 
                          disk_dev='xvda',
                          disk_source=const.Xen_disk_path,
                          net_type='ethernet',
                          net_mac=const.Xen_default_mac,
                          net_name=None,
                          proc_vcpu=1,
                          mem_mb=512,
                          malloc_units="MegaBytes",
                          emu_type=None,
                          virt='Xen'):
    vssd = get_vssd_mof(virt, dom_name)

    class_dasd = get_dasd_class(virt)
    if virt == 'KVM':
        disk_dev = 'vda'
        disk_source = const.KVM_disk_path
    elif virt == 'XenFV':
        disk_dev = 'hda'
        disk_source = const.XenFV_disk_path
    elif virt == 'LXC':
        disk_dev = const.LXC_default_mp
        disk_source = const.LXC_default_source

    #LXC guests do not need to set the EmulationType
    if virt == 'LXC':
        d = class_dasd(disk_dev, 
                       disk_source, 
                       dom_name)
    else:
        d = class_dasd(disk_dev, 
                       disk_source, 
                       dom_name, 
                       emu_type)
 
    class_masd = get_masd_class(virt)
    m = class_masd(megabytes=mem_mb,
                   mallocunits=malloc_units,
                   name=dom_name)

    class_gasd = get_gasd_class(virt)
    g = class_gasd(name=dom_name)

    # LXC only takes disk and memory device for now.
    if virt == 'LXC':
        return vssd, [d.mof(), m.mof(), g.mof()]
    
    class_nasd = get_nasd_class(virt)
    if net_mac != const.Xen_default_mac:
        pass
    elif virt == 'KVM':
        net_mac= const.KVM_default_mac
    elif virt == 'XenFV':
        net_mac = const.XenFV_default_mac
    elif virt == 'LXC':
        net_mac = const.LXC_default_mac
    n = class_nasd(type=net_type, 
                   mac=net_mac,
                   name=dom_name, 
                   virt_net=net_name)
    class_pasd = get_pasd_class(virt)
    p = class_pasd(vcpu=proc_vcpu,
                   name=dom_name)

    return vssd, [d.mof(), n.mof(), p.mof(), m.mof(), g.mof()]

