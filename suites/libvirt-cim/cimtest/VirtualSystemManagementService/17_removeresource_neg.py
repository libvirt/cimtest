#!/usr/bin/python
#
# Copyright 2009 IBM Corp.
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

import sys
import pywbem
from pywbem.cim_obj import CIMInstanceName
from XenKvmLib.vsms import get_vsms_class
from XenKvmLib.classes import get_typed_class
from XenKvmLib.vxml import get_class
from CimTest.Globals import logger
from XenKvmLib.const import do_main
from CimTest.ReturnCodes import FAIL, PASS

exp_rc = 6 #CIM_ERR_NOT_FOUND
exp_desc = 'No such instance (domain/invalid)'

sup_types = ['Xen', 'KVM', 'XenFV']
default_dom = 'domain'

@do_main(sup_types)
def main():
    options = main.options
    status = PASS

    cxml = get_class(options.virt)(default_dom)
    ret = cxml.cim_define(options.ip)
    if not ret:
        logger.error("Failed to define the dom: %s", default_dom)
        return FAIL

    rasd = get_typed_class(options.virt, 'DiskResourceAllocationSettingData')
    rasd_id = '%s/invalid' % default_dom
    keys = {'InstanceID' : rasd_id}

    try:
        bad_inst = CIMInstanceName(rasd, keybindings=keys)
        service = get_vsms_class(options.virt)(options.ip) 
        ret = service.RemoveResourceSettings(ResourceSettings=[bad_inst])
        if ret[0] == 0:
            logger.error('RemoveRS should NOT return OK with wrong RS input')
            status = FAIL
    except pywbem.CIMError, (rc, desc):
        if rc == exp_rc and desc.find(exp_desc) >= 0:
            logger.info('Got expected rc code and error string')
        else:
            logger.error('Unexpected rc code %s and description"\n %s',
                         rc, desc)
            status = FAIL
    except Exception, details:       
        logger.error(details)
        status = FAIL

    cxml.undefine(options.ip)
    return status

if __name__ == "__main__":
    sys.exit(main())
