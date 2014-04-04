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
from CimTest.ReturnCodes import PASS, FAIL
from CimTest.Globals import logger
from XenKvmLib import assoc
from XenKvmLib.classes import get_typed_class
from XenKvmLib.const import get_provider_version
from XenKvmLib.enumclass import EnumInstances

graphics_dev_rev = 725
input_dev_rev = 745
controller_dev_rev = 1310

def get_class(classname):
    return eval(classname)

def device_of(server, key_list):
    t = eval(key_list["CreationClassName"])

    return t(server, key_list)

def get_dom_devs(vs_type, ip, dom_name):
    cn = get_typed_class(vs_type, "ComputerSystem")
    an = get_typed_class(vs_type, "SystemDevice")
    devs = assoc.AssociatorNames(ip, an, cn, Name=dom_name,
                                 CreationClassName= cn)
    if devs == None:
        logger.error("System association failed")
        return 1
    elif len(devs) == 0:
        logger.error("No devices returned")
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

def dev_cn_to_rasd_cn(dev_cn, virt):
    if dev_cn.find('Processor') >= 0:
        return get_typed_class(virt, "ProcResourceAllocationSettingData")
    elif dev_cn.find('NetworkPort') >= 0:
        return get_typed_class(virt, "NetResourceAllocationSettingData")
    elif dev_cn.find('LogicalDisk') >= 0:
        return get_typed_class(virt, "DiskResourceAllocationSettingData")
    elif dev_cn.find('Memory') >= 0:
        return get_typed_class(virt, "MemResourceAllocationSettingData")
    elif dev_cn.find('DisplayController') >= 0:
        return get_typed_class(virt, "GraphicsResourceAllocationSettingData")
    elif dev_cn.find('PointingDevice') >= 0:
        return get_typed_class(virt, "InputResourceAllocationSettingData")
    elif dev_cn.find('Controller') >= 0:
        return get_typed_class(virt, "ControllerResourceAllocationSettingData")
    else:
        return None

def enum_dev(virt, ip):
    dev_list = ['Processor', 'Memory', 'NetworkPort', 'LogicalDisk']

    curr_cim_rev, changeset = get_provider_version(virt, ip)
    if curr_cim_rev >= graphics_dev_rev:
        dev_list.append('DisplayController')

    if curr_cim_rev >= input_dev_rev:
        dev_list.append('PointingDevice')

    if curr_cim_rev >= controller_dev_rev and virt == 'KVM':
        dev_list.append('Controller')

    dev_insts = {}

    try:
        for dev in dev_list:
            dev_cn = get_typed_class(virt, dev)
            list = EnumInstances(ip, dev_cn)

            if len(list) < 1:
                continue

            for dev in list:
                if dev.Classname not in dev_insts.keys():
                    dev_insts[dev.Classname] = []
                dev_insts[dev.Classname].append(dev)

    except Exception, details:
        logger.error(details)
        return dev_insts, FAIL

    return dev_insts, PASS

