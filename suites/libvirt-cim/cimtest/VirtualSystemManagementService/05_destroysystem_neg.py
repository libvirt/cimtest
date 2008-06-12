#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Guolian Yun <yunguol@cn.ibm.com>
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

import sys
import pywbem
from pywbem.cim_obj import CIMInstanceName
from VirtLib import utils
from XenKvmLib import vsms
from XenKvmLib.classes import get_typed_class
from XenKvmLib.const import CIM_REV
from XenKvmLib.test_doms import undefine_test_domain
from CimTest.Globals import logger
from CimTest.Globals import do_main
from CimTest.ReturnCodes import FAIL, PASS, SKIP

sup_types = ['Xen', 'KVM', 'XenFV', 'LXC']
vsms_status_version = 534

def destroysystem_fail(tc, options):
    service = vsms.get_vsms_class(options.virt)(options.ip)
    
    classname = get_typed_class(options.virt, 'ComputerSystem')

    if tc == 'noname':
        cs_ref = CIMInstanceName(classname, 
                              keybindings = {'CreationClassName':classname})

        if CIM_REV < vsms_status_version:
            exp_rc = 2 #IM_RC_FAILED
        else:
            exp_value = { 'rc'    : pywbem.CIM_ERR_FAILED,
                          'desc'  : 'CIM_ERR_FAILED: Unable to retrieve domain\
 name.'
                        }

    elif tc == 'nonexistent':
        cs_ref = CIMInstanceName(classname,keybindings = {
                                'Name':'##@@!!cimtest_domain',
                                'CreationClassName':classname})

        if CIM_REV < vsms_status_version:
            exp_rc = 4 #IM_RC_SYS_NOT_FOUND
        else:
            exp_value = { 'rc'   : pywbem.CIM_ERR_FAILED,
                          'desc' : 'CIM_ERR_FAILED: Failed to find domain' 
                        }

    else:
        return SKIP

    status = FAIL
    try:
        ret = service.DestroySystem(AffectedSystem=cs_ref)
        if CIM_REV < vsms_status_version:
            if ret[0] == exp_rc:
                logger.info('destroy_fail>>%s: Got expected return code %s', 
                            tc, exp_rc)
                return PASS 
            else:
                logger.error('destroy_fail>>%s: Got rc: %s, but we expect %s',
                            tc, ret[0], exp_rc)
                return FAIL 

    except Exception, details:
        if CIM_REV >= vsms_status_version:
            err_no   = details[0]
            err_desc = details[1]
            if err_no == exp_value['rc'] and err_desc == exp_value['desc']:
                logger.error("For Invalid Scenario '%s'", tc)
                logger.info('Got expected error no: %s', err_no)
                logger.info('Got expected error desc: %s',err_desc)
                return PASS

        logger.error('destroy_fail>> %s: Error executing DestroySystem' % tc)
        logger.error(details)
        return FAIL

@do_main(sup_types)
def main():
    options = main.options
    rc1 = destroysystem_fail('noname', options)
    rc2 = destroysystem_fail('nonexistent', options)

    status = FAIL
    if rc1 == PASS and rc2 == PASS:
        status = PASS
    else:
        rclist = [rc1, rc2]
        rclist.sort()
        if rclist[0] == PASS and rclist[1] == SKIP:
            status = PASS
    
    return status

if __name__ == "__main__":
    sys.exit(main())
    
