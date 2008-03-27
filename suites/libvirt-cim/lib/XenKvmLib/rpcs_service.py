#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#     Deepti B. Kalakeri<dkalaker@in.ibm.com> 
#    
#    
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

class CIM_ResourcePoolConfigurationService(CIMMethodClass):
    conn = None
    inst = None

    def __init__(self, server):
        
        self.conn = pywbem.WBEMConnection('http://%s' % server,
                                          (Globals.CIM_USER, Globals.CIM_PASS),
                                          Globals.CIM_NS)
        
        self.inst = self.__class__.__name__


class Xen_ResourcePoolConfigurationService(CIM_ResourcePoolConfigurationService):
    pass

class KVM_ResourcePoolConfigurationService(CIM_ResourcePoolConfigurationService):
    pass
