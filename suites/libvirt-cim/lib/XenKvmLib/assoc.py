#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Dan Smith <danms@us.ibm.com>
#    Deepti B. Kalakeri <dkalaker@in.ibm.com>
#    Guolian Yun <yunguol@cn.ibm.com>
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
from CimTest import Globals
from VirtLib import utils
import pywbem
from pywbem.cim_obj import CIMInstanceName
from XenKvmLib.classes import get_typed_class
from CimTest.ReturnCodes import PASS, FAIL
from CimTest.Globals import logger

def AssociatorNames(host, assoc_cn, classname, **keys):
    '''Resolve the association specified by @type, given the
    known @obj and @keys. 
    Return a list of CIMInstanceName objects, if an valid
    @keys is provided, or CIMClassName objects, if no 
    @keys is provided, or None on failure'''

    conn = myWBEMConnection('http://%s' % host,
                            (Globals.CIM_USER, Globals.CIM_PASS),
                            Globals.CIM_NS)
    instanceref = CIMInstanceName(classname, keybindings=keys)
    
    names = []

    try:
        names = conn.AssociatorNames(instanceref, AssocClass=assoc_cn)
    except pywbem.CIMError, arg:
        print arg[1]
        return names
    
    return names

def Associators(host, assoc_cn, classname, **keys):
    '''Resolve the association specified by @type, given the
    known @obj and @keys. 
    Return a list of CIMInstanceName objects, if an valid
    @keys is provided, or CIMClassName objects, if no 
    @keys is provided, or None on failure'''

    conn = myWBEMConnection('http://%s' % host,
                            (Globals.CIM_USER, Globals.CIM_PASS),
                            Globals.CIM_NS)
    instanceref = CIMInstanceName(classname, keybindings=keys)
    
    names = []

    try:
        names = conn.Associators(instanceref, AssocClass=assoc_cn)
    except pywbem.CIMError, arg:
        print arg[1]

    return names
    

class myWBEMConnection(pywbem.WBEMConnection):
    '''Inherit the official pywbem.WBEMConnection to define our
    own AssociatorNames.'''

    def AssociatorNames(self, ObjectName, **params):
        '''Inherit most code from pywbem's official AssociatorNames
        with a little hack around the return statement.
        pywbem's method assume the returned XML stream contains the 
        namespace info. This is not true for sfcb. In that case, a 
        direct return of result[2] works.'''

        params = self._map_association_params(params)
        params = self._add_objectname_param(params, ObjectName)

        namespace = self.default_namespace

        if isinstance(ObjectName, CIMInstanceName) and \
           ObjectName.namespace is not None:
            namespace = ObjectName.namespace

        result = self.imethodcall('AssociatorNames',
                                  namespace,
                                  **params)

        if result is None or len(result[2]) == 0:
            return []

        if isinstance(result[2][0], CIMInstanceName):
            return result[2]
        else:
            return map(lambda x: x[2], result[2])
 
def filter_by_result_class(result_list, result_class):
    new_list = []
    if result_list == None or len(result_list) < 1:
        return new_list
   
    for item in result_list:
        if item['CreationClassName'] == result_class: 
            new_list.append(item)

    return new_list

def compare_all_prop(inst, exp_inst):
    prop_vals = inst.items()

    for i in range(0, len(prop_vals)):
        key = prop_vals[i][0]
        val = eval('exp_inst.' + key)

        if prop_vals[i][1] != val:
            logger.error("%s val mismatch: got %s, expected %s" % (key,
                         prop_vals[i][1], val))
            return FAIL

    return PASS

