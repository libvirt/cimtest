#!/usr/bin/python
#
# Copyright 2009 IBM Corp.
#
# Authors:
#   Deepti B. Kalakeri <deeptik@linux.vnet.ibm.com> 
#    
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
#
# This testcase is used to verify the resume and restart remote migration.
#
#                                                      Date : 05-04-2009 
#

import sys
import os
from time import sleep
from  socket import gethostname
from XenKvmLib import vxml
from XenKvmLib.xm_virt_util import domain_list, net_list
from CimTest.Globals import logger
from XenKvmLib.const import do_main, default_network_name
from CimTest.ReturnCodes import PASS, FAIL, SKIP
from XenKvmLib.classes import get_typed_class
from XenKvmLib.vsmigrations import check_mig_support, local_remote_migrate, \
                                   cleanup_guest_netpool
from XenKvmLib.common_util import poll_for_state_change, create_netpool_conf

sup_types = ['KVM', 'Xen']

REQUESTED_STATE = 2

def setup_guest(test_dom, ip, virt):
    virt_xml = vxml.get_class(virt)
    cxml = virt_xml(test_dom)
    ret = cxml.cim_define(ip)
    if not ret:
        logger.error("Error define domain %s", test_dom)
        return FAIL, cxml

    status = cxml.cim_start(ip)
    if status != PASS:
        cxml.undefine(test_dom)
        logger.error("Error to start domain %s", test_dom)
        return FAIL, cxml

    status, dom_cs = poll_for_state_change(ip, virt, test_dom,
                                           REQUESTED_STATE)
    if status != PASS:
        cxml.cim_destroy(test_dom)
        cxml.undefine(test_dom)
        logger.error("'%s' didn't change state as expected" % test_dom)
        return FAIL, cxml

    return PASS, cxml

def cleanup_guest(virt, cxml, test_dom, t_sysname, s_sysname):
    status = PASS
    # Clean the domain on target machine.
    # This is req when migration is successful, also when migration is not
    # completely successful VM might be created on the target machine 
    # and hence need to clean.
    target_list = domain_list(t_sysname, virt)
    if target_list  != None and test_dom in target_list:
        ret_value = cxml.destroy(t_sysname)
        if not ret_value:
            logger.info("Failed to destroy the migrated domain '%s' on '%s'",
                         test_dom, t_sysname)
            status = FAIL

        ret_value = cxml.undefine(t_sysname)
        if not ret_value:
            logger.info("Failed to undefine the migrated domain '%s' on '%s'",
                         test_dom, t_sysname)
            status = FAIL

    # Remote Migration not Successful, clean the domain on src machine
    src_list = domain_list(s_sysname, virt)
    if src_list != None and test_dom in src_list:
        ret_value = cxml.cim_destroy(s_sysname)
        if not ret_value:
            logger.info("Failed to destroy the domain '%s' on the source '%s'",
                         test_dom, s_sysname)
            status = FAIL

        ret_value = cxml.undefine(s_sysname)
        if not ret_value:
            logger.info("Failed to undefine the domain '%s' on source '%s'",
                         test_dom, s_sysname)
            status = FAIL

    return status

def str_status(status):
    if status == PASS:
       return 'PASSED'
    else:
       return 'FAILED'

@do_main(sup_types)
def main():
    options = main.options
    virt = options.virt
    status, s_sysname, t_sysname = check_mig_support(virt, options)
    if status != PASS:
        return status
    
    status = FAIL
    test_dom = 'VM_frm_' + gethostname()
    net_pool_name = default_network_name
    mig_types = [ 'restart', 'resume' ]
    status_resume = status_restart = None
    cxml = None

    status_restart = -1 
    status_resume = -1 

    try:

        for mig_type in mig_types:
            logger.info("Executing '%s' migration for '%s' from '%s' to '%s'", 
                        mig_type, test_dom, s_sysname, t_sysname)
            status, cxml = setup_guest(test_dom, s_sysname, virt)
            if status != PASS:
                logger.error("Error setting up the guest")
                return status

            # Generally, having a test sleep is a bad choice, but we need to
            # give the guest some time to fully boot before we reboot it
            sleep(15)

            # create the networkpool used in the domain to be migrated 
            # on the target machine.
            t_net_list = net_list(t_sysname, virt)
            if t_net_list != None and net_pool_name not in t_net_list:
                status, netpool = create_netpool_conf(t_sysname, virt, 
                                                      net_name=net_pool_name)
                if status != PASS:
                   raise Exception("Unable to create network pool '%s' on '%s'"
                                   % (net_pool_name, t_sysname))

            # Migrate the test_dom to t_sysname.
            # Enable remote migration by setting remote_migrate=1
            status = local_remote_migrate(s_sysname, t_sysname, virt,
                                          remote_migrate=1, guest_name=test_dom,
                                          mtype=mig_type)

            logger.info("'%s' Migration for '%s %s' \n", 
                        mig_type, test_dom, str_status(status))
            if mig_type == 'restart' : 
                status_restart = status
            else:
                status_resume = status

            ret = cleanup_guest(virt, cxml, test_dom, t_sysname, s_sysname)
            if ret != PASS:
                logger.error("Cleanup failed after '%s' migration", mig_type)
                break

    except Exception, details:
        logger.error("Exception details is :%s", details)
        cleanup_guest(virt, cxml, test_dom, t_sysname, s_sysname)
        status = FAIL

    cleanup_guest_netpool(virt, cxml, test_dom, t_sysname, s_sysname)

    if status_restart == PASS and status_resume == PASS:
        status = PASS
    else:
        logger.error("Restart migration %d", status_restart)
        logger.error("Resume migration %d", status_resume)
        status = FAIL

    logger.info("Test case %s", str_status(status))
    return status

if __name__ == "__main__":
    sys.exit(main())

