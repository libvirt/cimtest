#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Dan Smith <danms@us.ibm.com>
#    Deepti B. Kalakeri <dkalaker@in.ibm.com>
#    Guolian Yun <yunguol@cn.ibm.com>
#    Kaitlin Rupert <karupert@us.ibm.com>
#    Veerendra Chandrappa <vechandr@in.ibm.com>
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
from pywbem.cim_obj import CIMInstanceName
from XenKvmLib.devices import CIM_Instance
from XenKvmLib.classes import get_typed_class
from CimTest import Globals

class CIM_MyClass(CIM_Instance):
    def __init__(self, server, keys):
        conn = pywbem.WBEMConnection('http://%s' % server,
                                     (Globals.CIM_USER, Globals.CIM_PASS),
                                     Globals.CIM_NS)

        try:
            classname = self.__class__.__name__
            ref = CIMInstanceName(classname,
                                  keybindings=keys)
            inst = conn.GetInstance(ref)
        except pywbem.CIMError, arg:
            raise arg

        CIM_Instance.__init__(self, inst)

class CIM_AllocationCapabilities(CIM_MyClass):
    pass

class CIM_RegisteredProfile(CIM_MyClass):
    pass

class CIM_LogicalDevice(CIM_MyClass):
    pass

class CIM_ResourcePool(CIM_MyClass):
    pass

class CIM_VirtualSystemManagementCapabilities(CIM_MyClass):
    pass

class CIM_ResourcePoolConfigurationCapabilities(CIM_MyClass):
    pass

class CIM_EnabledLogicalElementCapabilities(CIM_MyClass):
    pass

class Virt_VirtualSystemMigrationCapabilities(CIM_MyClass):
    pass

class CIM_VirtualSystemMigrationSettingData(CIM_MyClass):
    pass

class CIM_VirtualSystemSnapshotService(CIM_MyClass):
    pass

class CIM_VirtualSystemSnapshotServiceCapabilities(CIM_MyClass):
    pass

class CIM_NetResourceAllocationSettingData(CIM_MyClass):
    pass

class CIM_MemResourceAllocationSettingData(CIM_MyClass):
    pass

class CIM_ProcResourceAllocationSettingData(CIM_MyClass):
    pass

class CIM_DiskResourceAllocationSettingData(CIM_MyClass):
    pass



class Virt_MigrationJob(CIM_MyClass):
    pass

class Xen_RegisteredProfile(CIM_RegisteredProfile):
    pass

class KVM_RegisteredProfile(CIM_RegisteredProfile):
    pass

class Xen_VirtualSystemSettingData(CIM_MyClass):
    pass

class KVM_VirtualSystemSettingData(CIM_MyClass):
    pass

class Xen_LogicalDisk(CIM_LogicalDevice):
    pass 

class KVM_LogicalDisk(CIM_LogicalDevice):
    pass

class Xen_MemoryPool(CIM_ResourcePool):
    pass

class KVM_MemoryPool(CIM_ResourcePool):
    pass

class Xen_ProcessorPool(CIM_ResourcePool):
    pass

class KVM_ProcessorPool(CIM_ResourcePool):
    pass

class Xen_VirtualSystemManagementCapabilities(CIM_VirtualSystemManagementCapabilities):
    pass

class KVM_VirtualSystemManagementCapabilities(CIM_VirtualSystemManagementCapabilities):
    pass

class Xen_ResourcePoolConfigurationCapabilities(CIM_ResourcePoolConfigurationCapabilities):
    pass

class KVM_ResourcePoolConfigurationCapabilities(CIM_ResourcePoolConfigurationCapabilities):
    pass

class LXC_ResourcePoolConfigurationCapabilities(CIM_ResourcePoolConfigurationCapabilities):
    pass

class Xen_EnabledLogicalElementCapabilities(CIM_EnabledLogicalElementCapabilities):
    pass
    
class KVM_EnabledLogicalElementCapabilities(CIM_EnabledLogicalElementCapabilities):
    pass

class Xen_DiskPool(CIM_ResourcePool):
    pass

class KVM_DiskPool(CIM_ResourcePool):
    pass

class Xen_NetworkPool(CIM_ResourcePool):
    pass

class KVM_NetworkPool(CIM_ResourcePool):
    pass

class Xen_VirtualSystemMigrationCapabilities(Virt_VirtualSystemMigrationCapabilities):
    pass

class KVM_VirtualSystemMigrationCapabilities(Virt_VirtualSystemMigrationCapabilities):
    pass

class LXC_VirtualSystemMigrationCapabilities(Virt_VirtualSystemMigrationCapabilities):
    pass

class Xen_AllocationCapabilities(CIM_AllocationCapabilities):
    pass

class KVM_AllocationCapabilities(CIM_AllocationCapabilities):
    pass

class Xen_VirtualSystemMigrationSettingData(CIM_VirtualSystemMigrationSettingData):
    pass

class KVM_VirtualSystemMigrationSettingData(CIM_VirtualSystemMigrationSettingData):
    pass

class Xen_VirtualSystemSnapshotService(CIM_VirtualSystemSnapshotService):
    pass

class KVM_VirtualSystemSnapshotService(CIM_VirtualSystemSnapshotService):
    pass

class Xen_VirtualSystemSnapshotServiceCapabilities(CIM_VirtualSystemSnapshotServiceCapabilities):
    pass

class KVM_VirtualSystemSnapshotServiceCapabilities(CIM_VirtualSystemSnapshotServiceCapabilities):
    pass

class Xen_MemResourceAllocationSettingData(CIM_MemResourceAllocationSettingData):
    pass

class KVM_MemResourceAllocationSettingData(CIM_MemResourceAllocationSettingData):
    pass

class Xen_NetResourceAllocationSettingData(CIM_NetResourceAllocationSettingData):
    pass

class KVM_NetResourceAllocationSettingData(CIM_NetResourceAllocationSettingData):
    pass

class Xen_ProcResourceAllocationSettingData(CIM_ProcResourceAllocationSettingData):
    pass

class KVM_ProcResourceAllocationSettingData(CIM_ProcResourceAllocationSettingData):
    pass

class Xen_DiskResourceAllocationSettingData(CIM_DiskResourceAllocationSettingData):
    pass

class KVM_DiskResourceAllocationSettingData(CIM_DiskResourceAllocationSettingData):
    pass

# Generic function which can be used to get the enumerate instances of any 
# class when the following fields are specified
# classname = any class for which we want obtain the instances 
#             ex: Xen_RegisteredProfile
# keyname   = The keyvalue 
#             ex: InstanceID in case of Xen_RegisteredProfile
def enumerate_inst(server, classname, virt="Xen"):
    classname = "%s" % classname
    new_classname = classname.split('_')
    if len(new_classname) == 2:
        classname = new_classname[1]
    classname = eval(get_typed_class(virt, classname))
    instances = []
    conn = pywbem.WBEMConnection('http://%s' % server,
                                 (Globals.CIM_USER, Globals.CIM_PASS),
                                 Globals.CIM_NS)

    try:
        instances = conn.EnumerateInstances(classname.__name__)
    except pywbem.CIMError, arg:
        print arg[1]
        return []

    return instances 

def enumerate(server, basename, keys, virt="Xen"):
     #FIXME - Remove once all tests are converted for KVM
    basename = "%s" % basename
    new_base = basename.split('_')
    if len(new_base) == 2:
        basename = new_base[1]

    classname = eval(get_typed_class(virt, basename))
    instances = enumerate_inst(server, classname, virt)

    list = []

    for instance in instances:
        key_list = {}
        for item in keys:
            key_list[item] = instance[item] 

        if len(key_list) == 0:
            return list

        list.append(classname(server, key_list))

    return list

def getInstance(server, basename, keys, virt="Xen"):
    conn = pywbem.WBEMConnection('http://%s' % server,
                                 (Globals.CIM_USER, Globals.CIM_PASS),
                                 Globals.CIM_NS)

    #FIXME - Remove once all tests are converted for KVM
    basename = "%s" % basename
    new_base = basename.split('_')
    if len(new_base) == 2:
        basename = new_base[1]

    classname = eval(get_typed_class(virt, basename))
    try:
        inst = classname(server, keys)

    except pywbem.CIMError, arg:
        print arg[1]
        return []
        
    return inst
