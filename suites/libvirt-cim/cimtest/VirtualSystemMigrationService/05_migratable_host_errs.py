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
from pywbem.cim_obj import CIMInstanceName
from XenKvmLib import vxml
from XenKvmLib import vsmigrations
from CimTest.Globals import logger
from XenKvmLib.const import do_main
from CimTest.ReturnCodes import PASS, FAIL

sup_types = ['Xen', 'XenFV']

test_dom = 'dom_migration'
exp_rc = 1 #CIM_ERR_FAILED
exp_desc = 'Missing key (Name) in ComputerSystem'

@do_main(sup_types)
def main():
    options = main.options
    server = options.ip

    virt_xml = vxml.get_class(options.virt)
    cxml = virt_xml(test_dom)
    ret = cxml.cim_define(server)
    if not ret:
        logger.error("Error define domain %s" % test_dom )
        return FAIL

    status = cxml.cim_start(server)
    if status != PASS:
        cxml.undefine(server)
        logger.error("Error start domain %s" % test_dom )
        return status 

    status = FAIL 
    mig_successful = False
    
    try:
        service = vsmigrations.Xen_VirtualSystemMigrationService(server)
    except Exception:
        logger.error("Error using Xen_VirtualSystemMigrationService")
        cxml.destroy(server)
        cxml.undefine(server)
        return FAIL
        
    classname = 'Xen_ComputerSystem'
    cs_ref = CIMInstanceName(classname, 
                             keybindings = { 'Wrong':test_dom,
                                            'CreationClassName':classname})
   
    try:
        service.CheckVirtualSystemIsMigratableToHost(ComputerSystem=cs_ref,
                                                     DestinationHost=server)
        service.MigrateVirtualSystemToHost(ComputerSystem=cs_ref,
                                           DestinationHost=server)
        mig_successful = True
    except Exception, (rc, desc):
        if rc == exp_rc and desc.find(exp_desc) >= 0:
            logger.info('Got expected rc code :%s', rc)
            logger.info('Got expected error string:%s', desc)
            status = PASS
        else:
            logger.error('Unexpected rc code %s and description: %s', rc, desc)

    if mig_successful == True:
        logger.error('Migrate to host method should NOT return OK '
                      'since wrong key was supplied')

    cxml.destroy(server)
    cxml.undefine(server)

    return status

if __name__ == "__main__":
    sys.exit(main())
    
