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


class CIM_Instance:
    def __init__(self, inst):
        self.inst = inst


    def __getattr__(self, attr):
        return self.inst[attr]

    def __str__(self):
        print self.inst.items()


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

