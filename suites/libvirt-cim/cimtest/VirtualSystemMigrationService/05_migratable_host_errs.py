#!/usr/bin/python
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

import sys
import pywbem
from pywbem.cim_obj import CIMInstanceName
from VirtLib import utils
from XenKvmLib import vxml
from XenKvmLib import computersystem
from XenKvmLib import vsmigrations
from CimTest.Globals import logger, do_main
from CimTest.ReturnCodes import PASS, FAIL, XFAIL

sup_types = ['Xen', 'XenFV']

test_dom = 'dom_migration'
exp_rc = 1 #CIM_ERR_FAILED
exp_desc = 'Missing key (Name) in ComputerSystem'

@do_main(sup_types)
def main():
    options = main.options

    virt_xml = vxml.get_class(options.virt)
    cxml = virt_xml(test_dom)
    ret = cxml.create(options.ip)
    if not ret:
        logger.error("Error create domain %s" % test_dom )
        return FAIL

    status = FAIL 
    rc = -1
    
    try:
        service = vsmigrations.Xen_VirtualSystemMigrationService(options.ip)
    except Exception:
        logger.error("Error when go to the class of Xen_VirtualSystemMigrationService")
        return FAIL
        
    classname = 'Xen_ComputerSystem'
    cs_ref = CIMInstanceName(classname, keybindings = {
                                        'Wrong':test_dom,
                                        'CreationClassName':classname})
   
    try:
        service.CheckVirtualSystemIsMigratableToHost(ComputerSystem=cs_ref,
                                                     DestinationHost=options.ip)
        service.MigrateVirtualSystemToHost(ComputerSystem=cs_ref,
                                           DestinationHost=options.ip)
        rc = 0
    except pywbem.CIMError, (rc, desc):
        if rc == exp_rc and desc.find(exp_desc) >= 0:
            logger.info('Got expected rc code and error string.')
            status = PASS
        else:
            logger.error('Unexpected rc code %s and description:\n %s' % (rc, desc))
    except Exception, details:
        logger.error('Unknown exception happened')
        logger.error(details)

    if rc == 0:
        logger.error('Migrate to host method should NOT return OK with a wrong key input')

    cxml.destroy(options.ip)
    cxml.undefine(options.ip)

    return status

if __name__ == "__main__":
    sys.exit(main())
    
