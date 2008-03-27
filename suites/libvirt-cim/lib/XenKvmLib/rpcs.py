#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Guolian Yun <yunguol@cn.ibm.com>
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
from CimTest import Globals

class CIM_MyClass(CIM_Instance):
    def __init__(self, server, **key):
        conn = pywbem.WBEMConnection('http://%s' % server,
                                     (Globals.CIM_USER, Globals.CIM_PASS),
                                     Globals.CIM_NS)

        try:
            classname = self.__class__.__name__
            ref = CIMInstanceName(classname,
                                  keybindings=key)
            inst = conn.GetInstance(ref)
        except pywbem.CIMError, arg:
            raise arg

        CIM_Instance.__init__(self, inst)



class CIM_ResourcePoolConfigurationService(CIM_MyClass):
    pass

class Xen_ResourcePoolConfigurationService(CIM_ResourcePoolConfigurationService):
    pass

class KVM_ResourcePoolConfigurationService(CIM_ResourcePoolConfigurationService):
    pass


def enumerate(server, classname):
    conn = pywbem.WBEMConnection('http://%s' % server,
                                 (Globals.CIM_USER, Globals.CIM_PASS),
                                 Globals.CIM_NS)
   
    cn = eval(classname)

    try:
        instances = conn.EnumerateInstances(cn.__name__)
    except pywbem.CIMError, arg:
        print arg[1]
        return []

    list = []

    for instance in instances:
        list.append(cn(server,
                       Name = instance['Name'],
                       CreationClassName = instance['CreationClassName'],
                       SystemCreationClassName = instance['SystemCreationClassName'],
                       SystemName = instance['SystemName']))

    return list

