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
# This test case is used to verify the VSMS.DestroySystem with invalid vs.


import sys
import pywbem
from pywbem.cim_obj import CIMInstanceName
from XenKvmLib import vsms
from XenKvmLib.classes import get_typed_class
from CimTest.Globals import logger
from XenKvmLib.const import do_main, get_provider_version
from CimTest.ReturnCodes import FAIL, PASS, SKIP

sup_types = ['Xen', 'KVM', 'XenFV', 'LXC']
vsms_err_message = 814

def destroysystem_fail(tc, options):
    service = vsms.get_vsms_class(options.virt)(options.ip)
    
    classname = get_typed_class(options.virt, 'ComputerSystem')
    curr_cim_rev, changeset = get_provider_version(options.virt, options.ip)

    if tc == 'noname':
        cs_ref = CIMInstanceName(classname, 
                              keybindings = {'CreationClassName':classname})

        if curr_cim_rev >= vsms_err_message:
            exp_value = { 'rc'    : pywbem.CIM_ERR_NOT_FOUND,
                          'desc'  : 'Unable to retrieve domain name: Error 0'
                        }
        else:
            exp_value = { 'rc'    : pywbem.CIM_ERR_FAILED,
                          'desc'  : 'Unable to retrieve domain name.'
                        }

    elif tc == 'nonexistent':
        cs_ref = CIMInstanceName(classname,keybindings = {
                                'Name':'##@@!!cimtest_domain',
                                'CreationClassName':classname})

        if curr_cim_rev >= vsms_err_message:
            exp_value = { 'rc'   : pywbem.CIM_ERR_NOT_FOUND,
                          'desc' : "Referenced domain `##@@!!cimtest_domain'" \
                                   " does not exist: Domain not found"
                        }
        else:
            exp_value = { 'rc'   : pywbem.CIM_ERR_FAILED,
                          'desc' : 'Failed to find domain'
                        }

    try:
        ret = service.DestroySystem(AffectedSystem=cs_ref)

    except Exception, details:
        err_no   = details[0]
        err_desc = details[1]
        logger.info("For Invalid Scenario '%s'", tc)
        if err_no == exp_value['rc'] and err_desc.find(exp_value['desc']) >= 0:
            logger.info('Got expected error no: %s', err_no)
            logger.info('Got expected error desc: %s',err_desc)
            return PASS
        else:
            logger.error('Got error no %s, but expected no %s', 
                          err_no, exp_value['rc'])
            logger.error('Got error desc: %s, but expected desc: %s',
                          err_desc, exp_value['desc'])
            return FAIL

    logger.error('destroy_fail>> %s: Error executing DestroySystem', tc)
    return FAIL

@do_main(sup_types)
def main():
    options = main.options
    rc1 = destroysystem_fail('noname', options)
    rc2 = destroysystem_fail('nonexistent', options)
    
    status = FAIL
    if rc1 == PASS and rc2 == PASS:
        return PASS

    return status

if __name__ == "__main__":
    sys.exit(main())
