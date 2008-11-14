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
from CimTest import Globals, CimExt
from VirtLib import utils
from CimTest.Globals import logger


class CIM_CimtestClass(CIM_Instance):
    def __init__(self, host, ref):

        conn = pywbem.WBEMConnection('http://%s' % host,
                                     (Globals.CIM_USER, Globals.CIM_PASS),
                                     Globals.CIM_NS)
        try:
            inst = conn.GetInstance(ref)
        except pywbem.CIMError, arg:
            raise arg

        self.conn = conn
        self.inst = inst
        self.ref = ref

        CIM_Instance.__init__(self, inst)

    def __invoke(self, method, params):
        if method == "__iter__" or method == "items":
            return self.inst.items()
        if method == "__repr__":
            items = "" 
            for item in self.inst.items():
                items += "('%s' %s)," % item
            return items.rstrip(",")

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


def EnumNames(host, cn):
    '''Resolve the enumeration given the @cn.
    Return a list of CIMInstanceName objects.'''

    conn = pywbem.WBEMConnection('http://%s' % host,
                                 (Globals.CIM_USER, Globals.CIM_PASS),
                                 Globals.CIM_NS)

    names = []

    try:
        names = conn.EnumerateInstanceNames(cn)
    except pywbem.CIMError, arg:
        print arg[1]
        return names

    return names

def EnumInstances(host, cn, ret_cim_inst=False):
    '''Resolve the enumeration given the @cn.
    Return a list of CIMInstance objects.'''

    refs = []

    try:
        refs = EnumNames(host, cn)
    except pywbem.CIMError, arg:
        print arg[1]

    list = []

    for name in refs:
        inst = CIM_CimtestClass(host, name)
        if ret_cim_inst:
            inst = inst.inst
        list.append(inst)
 
    return list

def GetInstance(host, cn, keys, ret_cim_inst=False):
    '''Resolve the enumeration given the @cn.
    Return a list of CIMInstance objects.'''

    ref = CIMInstanceName(cn, keybindings=keys)
    inst = None 

    try:
        inst = CIM_CimtestClass(host, ref)

        if ret_cim_inst:
            inst = inst.inst
    except pywbem.CIMError, arg:
        print arg[1]

    return inst 

