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
from XenKvmLib.test_doms import undefine_test_domain
from CimTest.Globals import logger
from CimTest.Globals import do_main
from CimTest.ReturnCodes import FAIL, PASS, SKIP

sup_types = ['Xen', 'KVM', 'XenFV']

def destroysystem_fail(tc, options):
    service = vsms.get_vsms_class(options.virt)(options.ip)
    
    classname = get_typed_class(options.virt, 'ComputerSystem')
    if tc == 'noname':
        exp_rc = 2 #IM_RC_FAILED
        cs_ref = CIMInstanceName(classname, 
                    keybindings = {'CreationClassName':classname})
    elif tc == 'nonexistent':
        exp_rc = 4 #IM_RC_SYS_NOT_FOUND
        cs_ref = CIMInstanceName(classname,keybindings = {
                    'Name':'##@@!!cimtest_domain',
                    'CreationClassName':classname})
    else:
        return SKIP

    status = FAIL
    try:
        ret = service.DestroySystem(AffectedSystem=cs_ref)
        if ret[0] == exp_rc:
            status = PASS
            logger.info('destroy_fail>>%s: Got expected return code %s' % (tc, exp_rc))
        else:
            status = FAIL
            logger.error('destroy_fail>>%s: Got rc: %s, but we expect %s' % (tc, ret[0], exp_rc))
    except Exception, details:
        logger.error('destroy_fail>>%s: Error executing DestroySystem, exception details below' % tc)
        logger.error(details)
        status = FAIL
    
    return status

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
    
