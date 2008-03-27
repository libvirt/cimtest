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
from pywbem.cim_obj import CIMInstanceName
from CimTest import CimExt
from CimTest import Globals
from XenKvmLib.devices import CIM_Instance
from XenKvmLib.classes import get_typed_class, virt_types

class CIM_System(CIM_Instance):
    def __init__(self, server, name):
        conn = pywbem.WBEMConnection('http://%s' % server,
                                     (Globals.CIM_USER, Globals.CIM_PASS),
                                     Globals.CIM_NS)

        try:
            classname = self.__class__.__name__
            ref = CIMInstanceName(classname, keybindings={
                        "Name":name,
                        "CreationClassName":classname})
            inst = conn.GetInstance(ref)
        except pywbem.CIMError, arg:
            raise arg

        self.conn = conn
        self.inst = inst
        self.ref = ref 

        CIM_Instance.__init__(self, inst)

    def __invoke(self, method, params):
        try:
            return self.conn.InvokeMethod(method, 
                                          self.ref, 
                                          **params)
        except pywbem.CIMError, arg:
            print 'InvokeMethod(%s): %s' % (method, arg[1])
            raise

    def __getattr__(self, attr):
        if self.inst.has_key(attr):
            return self.inst[attr]
        else:
            return CimExt._Method(self.__invoke, attr)

class Xen_ComputerSystem(CIM_System):
    pass

class KVM_ComputerSystem(CIM_System):
    pass

def get_cs_class(virt):
    if virt in virt_types:
        return eval(get_typed_class(virt, 'ComputerSystem'))

def enumerate(server, virt='Xen'):
    conn = pywbem.WBEMConnection('http://%s' % server,
                                 (Globals.CIM_USER, Globals.CIM_PASS),
                                 Globals.CIM_NS)
    classname = get_typed_class(virt, 'ComputerSystem')

    try:
        instances = conn.EnumerateInstances(classname)
    except pywbem.CIMError, arg:
        print arg[1]
        return []

    list = []

    for instance in instances:
        list.append(get_cs_class(virt)(server, instance["Name"]))

    return list

def system_of(server, iname):
    t = eval(iname["CreationClassName"])

    return t(server, iname["Name"])
