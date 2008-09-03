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
import time
import pywbem
from pywbem.cim_obj import CIMInstanceName
from VirtLib import utils
from XenKvmLib import vxml
from XenKvmLib.common_util import poll_for_state_change
from XenKvmLib import vsmigrations
from XenKvmLib.vsmigrations import check_possible_host_migration, \
migrate_guest_to_host, check_migration_job
from XenKvmLib import enumclass
from CimTest.Globals import logger, CIM_ERROR_ENUMERATE, do_main
from CimTest.ReturnCodes import PASS, FAIL, XFAIL

sup_types = ['Xen', 'XenFV']

dom_name = 'dom_migrate'
REQUESTED_STATE = 2

def define_guest_get_ref(ip, guest_name, virt):
    try:
        virt_xml = vxml.get_class(virt)
        cxml = virt_xml(guest_name)
        cxml.define(ip)
    except Exception:
        logger.error("Error define domain %s" % guest_name)
        cxml.undefine(ip)
        return FAIL, None

    classname = 'Xen_ComputerSystem'
    cs_ref = CIMInstanceName(classname, keybindings = {
                                        'Name':guest_name,
                                        'CreationClassName':classname})

    return PASS, cs_ref

def setup_env(ip, migration_list, local_migrate, virt):
    ref_list = []

    if local_migrate == 1:
        for i in range(0, len(migration_list)):
            guest_name = "%s-%i" % (dom_name, i)
            status, ref = define_guest_get_ref(ip, guest_name, virt)
            if status != PASS:
                return FAIL, None
            ref_list.append(ref)
    else:
        status, ref = define_guest_get_ref(ip, dom_name, virt)
        if status != PASS:
            return FAIL, None
        ref_list.append(ref)

    return PASS, ref_list 

def get_msd_list(local_migrate):
    #Get default_msd and static_msd here
    default_msd = vsmigrations.default_msd_str()
    static_msd = vsmigrations.default_msd_str(mtype=4)
    
    migration_list = {}

    if local_migrate == 1:
        offline_msd = vsmigrations.default_msd_str(mtype=1)
        migration_list['Offline'] = offline_msd

    #The syntax here is weird - want to ensure offline is in the list
    #first because it needs a guest that hasn't been started yet.
    migration_list['Default'] = default_msd 
    migration_list['Static'] = static_msd 

    return migration_list

def start_guest(ip, guest_name, type, virt):
    if type != "Offline":
        try:
            virt_xml = vxml.get_class(virt)
            cxml = virt_xml(guest_name)
            cxml.start(ip)

            status, dom_cs = poll_for_state_change(ip, virt, guest_name,
                                                   REQUESTED_STATE)
            if status != PASS:
                raise Exception("%s didn't change state as expected" % guest_name)
                return FAIL, None
        
        except Exception:
            logger.error("Error start domain %s" % guest_name)
            return FAIL, None

    return PASS, cxml

@do_main(sup_types)
def main():
    options = main.options
    status = PASS
    rc = -1
    virt = options.virt
    
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

    mlist = get_msd_list(local_migrate)
        
    ref_list = []
    cs_ref = None

    status, ref_list = setup_env(options.ip, mlist, local_migrate, virt)
    if status != PASS or len(ref_list) < 1:
        return FAIL

    cs_ref = ref_list[0]

    for type, item in mlist.iteritems():
        guest_name = cs_ref['Name']

        status, cxml = start_guest(options.ip, guest_name, type, virt)
        if status != PASS:
            break

        status = check_possible_host_migration(service, cs_ref, target_ip) 
        if status != PASS:
            break

        logger.info("Migrating guest with the following options:")
        logger.info("%s" % item)
        status, ret = migrate_guest_to_host(service, cs_ref, target_ip, item)
        if status == FAIL:
            logger.error("MigrateVirtualSystemToHost: unexpected list length %s"
                         % len(ret))
            cxml.destroy(options.ip)
            cxml.undefine(options.ip)
            return status 
        elif len(ret) == 2:
            id = ret[1]['Job'].keybindings['InstanceID']

        status =  check_migration_job(options.ip, id, target_ip, 
                                      guest_name, local_migrate, virt)
        if status != PASS:
            break

        #Get new ref
        if local_migrate == 1:
            cxml.destroy(options.ip)
            cxml.undefine(options.ip)
            ref_list.remove(cs_ref)
            if len(ref_list) > 0:
                cs_ref = ref_list[0]

    if local_migrate == 0:
        cxml.destroy(options.ip)
        cxml.undefine(options.ip)

    return status

if __name__ == "__main__":
    sys.exit(main())
