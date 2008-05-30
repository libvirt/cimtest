#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Dan Smith <danms@us.ibm.com>
#    Guolian Yun <yunguol@cn.ibm.com>
#    Kaitlin Rupert <karupert@us.ibm.com>
#    Veerendra Chandrappa <vechandr@in.ibm.com>
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
from CimTest import CimExt
from CimTest import Globals
from XenKvmLib import assoc
from XenKvmLib.classes import get_typed_class

LinkTechnology_Ethernet = 2

class CIM_Instance:
    def __init__(self, inst):
        self.inst = inst


    def __getattr__(self, attr):
        return self.inst[attr]

    def __str__(self):
        print self.inst.items()

class CIM_LogicalDevice(CIM_Instance):
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

class CIM_LogicalDisk(CIM_LogicalDevice):
    pass

class CIM_NetworkPort(CIM_LogicalDevice):
    pass

class CIM_Memory(CIM_LogicalDevice):
    pass

class CIM_Processor(CIM_LogicalDevice):
    pass

class Xen_LogicalDisk(CIM_LogicalDisk):
    pass

class KVM_LogicalDisk(CIM_LogicalDisk):
    pass

class Xen_NetworkPort(CIM_NetworkPort):
    pass

class KVM_NetworkPort(CIM_NetworkPort):
    pass

class Xen_Memory(CIM_Memory):
    pass

class KVM_Memory(CIM_Memory):
    pass

class LXC_Memory(CIM_Memory):
    pass

class Xen_Processor(CIM_Processor):
    pass

class KVM_Processor(CIM_Processor):
    pass

def get_class(classname):
    return eval(classname)

def enumerate(server, basetype, keys, virt='Xen'):
    conn = pywbem.WBEMConnection('http://%s' % server,
                                 (Globals.CIM_USER, Globals.CIM_PASS),
                                 Globals.CIM_NS)

    list = []

    #FIXME - Remove once all tests are converted for KVM
    basetype = basetype.split('_', 1)[-1]
    
    devtype = eval(get_typed_class(virt, basetype))
    try:
        names = conn.EnumerateInstanceNames(devtype.__name__)
    except pywbem.CIMError, arg:
        print arg[1]
        return list

    for name in names:
        key_list = {}
        for item in keys:
            key_list[item] = name.keybindings[item]

        if len(key_list) == 0:
            return list

        list.append(devtype(server, key_list))

    return list

    
def device_of(server, key_list):
    t = eval(key_list["CreationClassName"])

    return t(server, key_list)

def get_dom_devs(vs_type, ip, dom_name):
    cn = "ComputerSystem"

    devs = assoc.AssociatorNames(ip, "SystemDevice",
                                 cn,
                                 vs_type,
                                 Name=dom_name,
                                 CreationClassName= get_typed_class(vs_type, cn))
    if devs == None:
        Globals.logger.error("System association failed")
        return 1
    elif len(devs) == 0:
        Globals.logger.error("No devices returned")
        return 1

    return (0, devs)

def get_dom_proc_insts(vs_type, ip, dom_name):
    cn = get_typed_class(vs_type, "Processor")
    proc_list = [] 
    
    rc, devs = get_dom_devs(vs_type, ip, dom_name)

    if rc != 0 or devs == None:
        return proc_list

    for item in devs:
        if item['CreationClassName'] == cn: 
            proc_list.append(item)

    return proc_list

def get_dom_mem_inst(vs_type, ip, dom_name):
    cn = get_typed_class(vs_type, "Memory")
    mem_list = [] 
    
    rc, devs = get_dom_devs(vs_type, ip, dom_name)

    if rc != 0 or devs == None:
        return mem_list

    for item in devs:
        if item['CreationClassName'] == cn: 
            mem_list.append(item)

    return mem_list

