#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
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

import sys
import pywbem
from pywbem.cim_obj import CIMInstanceName
from VirtLib import utils
from XenKvmLib import vsms
from XenKvmLib import vxml
from XenKvmLib.classes import get_typed_class
from CimTest.Globals import logger
from XenKvmLib.const import do_main
from CimTest.ReturnCodes import PASS, FAIL, XFAIL_RC

sup_types = ['Xen', 'KVM', 'XenFV', 'LXC']
exp_rc = 1 #CMPI_RC_ERR_FAILED
exp_desc = 'Unable to parse embedded object'

default_dom = 'rstest_domain'
bug = '90070'

@do_main(sup_types)
def main():
    options = main.options
    
    service = vsms.get_vsms_class(options.virt)(options.ip)
    cxml = vxml.get_class(options.virt)(default_dom)
    classname = get_typed_class(options.virt, 'VirtualSystemSettingData')
    vssd_ref = CIMInstanceName(classname, keybindings = {
                               'InstanceID' : 'Xen:%s' % default_dom,
                               'CreationClassName' : classname})
    status = PASS
    rc = -1
    try:
        cxml.define(options.ip)
        bad_inst = 'instance of what ever { dd = 3; //\ ]&'
        ret = service.AddResourceSettings(AffectedConfiguration=vssd_ref, 
                                    ResourceSettings=[bad_inst])
        logger.info('ret[0] = %s' % ret[0])
        if ret[0] == None:
            logger.error('AddRS should NOT return OK with wrong RS input')
            rc = 0
    except pywbem.CIMError, (rc, desc):
        if rc == exp_rc and desc.find(exp_desc) >= 0:
            logger.info('Got expected rc code and error string.')
            status = PASS
        else:
            logger.error('Unexpected rc code %s and description:\n %s' % 
                         (rc, desc))
            status = FAIL
    except Exception, details:
        logger.error('Error invoking AddRS')
        logger.error(details)
        status = FAIL

    cxml.undefine(options.ip)
    if rc == 0:
        return XFAIL_RC(bug)

    return status

if __name__ == "__main__":
    sys.exit(main())
    
