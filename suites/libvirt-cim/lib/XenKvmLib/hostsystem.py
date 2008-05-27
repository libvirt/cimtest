#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Dan Smith <danms@us.ibm.com>
#    Guolian Yun <yunguol@cn.ibm.com>
#    Kaitlin Rupert <karupert@us.ibm.com>
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
from XenKvmLib.classes import get_typed_class

class CIM_System(CIM_Instance):
    def __init__(self, server, name):
        conn = pywbem.WBEMConnection('http://%s' % server,
                                     (Globals.CIM_USER, Globals.CIM_PASS),
                                     Globals.CIM_NS)

        try:
            classname = self.__class__.__name__
            ref = CIMInstanceName(classname,
                                  keybindings={"Name":name,
                                               "CreationClassName": classname})
            inst = conn.GetInstance(ref)
        except pywbem.CIMError, arg:
            raise arg

        CIM_Instance.__init__(self, inst)

class Xen_HostSystem(CIM_System):
    pass

class KVM_HostSystem(CIM_System):
    pass

class LXC_HostSystem(CIM_System):
    pass


def enumerate(server, virt='Xen'):
    conn = pywbem.WBEMConnection('http://%s' % server,
                                 (Globals.CIM_USER, Globals.CIM_PASS),
                                 Globals.CIM_NS)
    if virt == 'XenFV':
        virt = 'Xen'

    classname = get_typed_class(virt, 'HostSystem')

    try:
        instances = conn.EnumerateInstances(classname)
    except pywbem.CIMError, arg:
        print arg[1]
        return []
        
    list = []
       
    for instance in instances:
        list.append(eval(classname)(server, instance["Name"]))

    return list
