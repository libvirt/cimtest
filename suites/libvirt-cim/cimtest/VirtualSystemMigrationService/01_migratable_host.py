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
from XenKvmLib import vxml
from XenKvmLib.common_util import poll_for_state_change
from XenKvmLib import computersystem
from XenKvmLib import vsmigrations
from XenKvmLib.vsmigrations import check_possible_host_migration, migrate_guest_to_host, check_migration_job
from XenKvmLib import enumclass
from CimTest.Globals import logger, CIM_ERROR_ENUMERATE, do_main
from CimTest.ReturnCodes import PASS, FAIL, XFAIL

sup_types = ['Xen', 'XenFV']
dom_name = 'dom_migrate'

REQUESTED_STATE = 2

def start_guest_get_ref(ip, guest_name, virt):
    virt_xml = vxml.get_class(virt)
    cxml = virt_xml(guest_name)
    ret = cxml.create(ip)
    if not ret:
        logger.error("Error create domain %s" % guest_name)
        return FAIL

    status = poll_for_state_change(ip, virt, guest_name,
                                   REQUESTED_STATE)
    if status != PASS:
        raise Exception("%s didn't change state as expected" % guest_name)
        return FAIL

    classname = 'Xen_ComputerSystem'
    cs_ref = CIMInstanceName(classname, keybindings = {
                                        'Name':guest_name,
                                        'CreationClassName':classname})

    if cs_ref is None:
        return FAIL, None, cxml

    return PASS, cs_ref, cxml

@do_main(sup_types)
def main():
    options = main.options
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

    status, cs_ref, cxml = start_guest_get_ref(options.ip, dom_name, options.virt)
    if status != PASS:
        cxml.destroy(options.ip)
        cxml.undefine(options.ip)
        return FAIL

    guest_name = cs_ref['Name']

    status = check_possible_host_migration(service, cs_ref, target_ip) 
    if status != PASS:
        cxml.destroy(options.ip)
        cxml.undefine(options.ip)
        return FAIL

    status, ret = migrate_guest_to_host(service, cs_ref, target_ip)
    if status == FAIL:
        logger.error("MigrateVirtualSystemToHost: unexpected list length %s"
                     % len(ret))
        cxml.destroy(options.ip)
        cxml.undefine(options.ip)
        return status 
    elif len(ret) == 2:
        id = ret[1]['Job'].keybindings['InstanceID']

    status =  check_migration_job(options.ip, id, target_ip, 
                                  guest_name, local_migrate)

    cxml.destroy(options.ip)
    cxml.undefine(options.ip)

    return status

if __name__ == "__main__":
    sys.exit(main())
