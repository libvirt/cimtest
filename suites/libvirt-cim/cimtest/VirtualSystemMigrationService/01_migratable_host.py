#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Dan Smith <danms@us.ibm.com>
#    Guolian Yun <yunguol@cn.ibm.com>
#    Kaitlin Rupert <karupert@us.ibm.com>
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
import time
import pywbem
from pywbem.cim_obj import CIMInstanceName
from VirtLib import utils
from XenKvmLib.test_doms import define_test_domain, start_test_domain, destroy_and_undefine_domain
from XenKvmLib.test_xml import *
from XenKvmLib import computersystem
from XenKvmLib import vsmigrations
from XenKvmLib.vsmigrations import check_possible_host_migration, migrate_guest_to_host, check_migration_job
from XenKvmLib import enumclass
from CimTest.Globals import log_param, logger, CIM_ERROR_ENUMERATE, do_main
from CimTest.ReturnCodes import PASS, FAIL, XFAIL

sup_types = ['Xen']
dom_name = 'dom_migrate'

def start_guest_get_ref(ip, guest_name):
    try:
        xmlfile = testxml(guest_name)   
        define_test_domain(xmlfile, ip)

        start_test_domain(guest_name, ip)
        time.sleep(10)
    except Exception:
        logger.error("Error creating domain %s" % guest_name)
        destroy_and_undefine_domain(guest_name, options.ip)
        return FAIL, None

    classname = 'Xen_ComputerSystem'
    cs_ref = CIMInstanceName(classname, keybindings = {
                                        'Name':guest_name,
                                        'CreationClassName':classname})

    return PASS, cs_ref

@do_main(sup_types)
def main():
    options = main.options
    log_param()
    status = PASS
    rc = -1
    
    try:
        service = vsmigrations.Xen_VirtualSystemMigrationService(options.ip)
    except Exception:
        logger.error("Error getting inst of Xen_VirtualSystemMigrationService")
        return FAIL

    #This value can be changed to a different target host.
    target_ip = options.ip 

    if target_ip != options.ip:
        local_migrate = 1
    else:
        local_migrate = 0

    status, cs_ref = start_guest_get_ref(options.ip, dom_name)
    if status != PASS:
        return FAIL

    guest_name = cs_ref['Name']

    status = check_possible_host_migration(service, cs_ref, target_ip) 
    if status != PASS:
        destroy_and_undefine_domain(dom_name, options.ip)   
        return FAIL

    status, ret = migrate_guest_to_host(service, cs_ref, target_ip)

    if status == FAIL:
        logger.error("MigrateVirtualSystemToHost: unexpected list length %s"
                     % len(ret))
        return status 
    elif len(ret) == 2:
        id = ret[1]['Job'].keybindings['InstanceID']

    status =  check_migration_job(options.ip, id, target_ip, 
                                  guest_name, local_migrate)


    destroy_and_undefine_domain(dom_name, options.ip)   

    return status

if __name__ == "__main__":
    sys.exit(main())
