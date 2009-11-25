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
# This testcase is used to verify the Created|Modified|Deleted 
# Migration Indications for offline VM Migration.
#
#                                                      Date : 06-07-2009
#

import sys
from signal import SIGKILL
from socket import gethostname
from os import kill, fork, _exit
from XenKvmLib.vxml import get_class
from XenKvmLib.xm_virt_util import domain_list, net_list
from CimTest.Globals import logger
from XenKvmLib.const import do_main, default_network_name
from CimTest.ReturnCodes import PASS, FAIL
from XenKvmLib.vsmigrations import check_mig_support, local_remote_migrate
from XenKvmLib.common_util import poll_for_state_change, create_netpool_conf,\
                                  destroy_netpool
from XenKvmLib.indications import sub_ind, handle_request, poll_for_ind

sup_types = ['KVM', 'Xen']

REQUESTED_STATE = 3

def setup_guest(test_dom, ip, virt):
    virt_xml = get_class(virt)
    cxml = virt_xml(test_dom)
    ret = cxml.cim_define(ip)
    if not ret:
        logger.error("Error define domain %s", test_dom)
        return FAIL, cxml

    status, dom_cs = poll_for_state_change(ip, virt, test_dom,
                                           REQUESTED_STATE)
    if status != PASS:
        cxml.undefine(test_dom)
        logger.error("'%s' didn't change state as expected" % test_dom)
        return FAIL, cxml

    return PASS, cxml

def cleanup_guest_netpool(virt, cxml, test_dom, t_sysname, 
                          s_sysname, clean_net=True):
    # Clean the domain on target machine.
    # This is req when migration is successful, also when migration is not
    # completely successful VM might be created on the target machine 
    # and hence need to clean.
    target_list = domain_list(t_sysname, virt)
    if target_list  != None and test_dom in target_list:
        ret_value = cxml.undefine(t_sysname)
        if not ret_value:
            logger.info("Failed to undefine the migrated domain '%s' on '%s'",
                         test_dom, t_sysname)

    if clean_net != True:
        return 

    if t_sysname != "localhost" and t_sysname not in s_sysname:
        # clean the networkpool created on the remote machine
        target_net_list = net_list(t_sysname, virt)
        if target_net_list != None and default_network_name in target_net_list:
            ret_value = destroy_netpool(t_sysname, virt, default_network_name)
            if ret_value != PASS:
                logger.info("Unable to destroy networkpool '%s' on '%s'",
                             default_network_name, t_sysname)

    # Remote Migration not Successful, clean the domain on src machine
    src_list = domain_list(s_sysname, virt)
    if src_list != None and test_dom in src_list:
        ret_value = cxml.undefine(s_sysname)
        if not ret_value:
            logger.info("Failed to undefine the domain '%s' on source '%s'",
                         test_dom, s_sysname)


def gen_indication(test_dom, s_sysname, virt, t_sysname):
    cxml = None
    try:
        status, cxml = setup_guest(test_dom, s_sysname, virt)
        if status != PASS:
            logger.error("Error setting up the guest")
            return status, None

        # create the networkpool used in the domain to be migrated 
        # on the target machine.
        t_net_list = net_list(t_sysname, virt)
        if t_net_list != None and default_network_name not in t_net_list:
            status, netpool = create_netpool_conf(t_sysname, virt, 
                                                  net_name=default_network_name)
            if status != PASS:
               raise Exception("Unable to create network pool '%s' on '%s'" 
                               % (default_network_name, t_sysname))

        # Migrate the test_dom to t_sysname.
        # Enable remote migration by setting remote_migrate=1
        status = local_remote_migrate(s_sysname, t_sysname, virt,
                                      remote_migrate=1, 
                                      guest_name=test_dom,
                                      mtype='offline')

    except Exception, details:
        logger.error("Exception details :%s", details)
        return FAIL, cxml

    return status, cxml

@do_main(sup_types)
def main():
    options = main.options
    virt = options.virt
    status, s_sysname, t_sysname = check_mig_support(virt, options)
    if status != PASS:
        return status

    status = FAIL
    test_dom = 'VM_frm_' + gethostname()
    ind_names = {
                 'create' : 'ComputerSystemMigrationJobCreatedIndication',
                 'modify' : 'ComputerSystemMigrationJobModifiedIndication', 
                 'delete' : 'ComputerSystemMigrationJobDeletedIndication' 
                }

    sub_list, ind_names, dict = sub_ind(s_sysname, virt, ind_names)
    for ind in ind_names.keys():
        sub = sub_list[ind]
        ind_name = ind_names[ind]
        logger.info("\n Verifying '%s' indications ....", ind_name)
        try:
            pid = fork()
            if pid == 0:
                status = handle_request(sub, ind_name, dict, 
                                        len(ind_names.keys()))
                if status != PASS:
                    _exit(1)

                _exit(0)
            else:
                try:
                    status, cxml = gen_indication(test_dom, s_sysname, 
                                                  virt, t_sysname)
                    if status != PASS:
                        kill(pid, SIGKILL)
                        raise Exception("Unable to generate indication") 

                    status = poll_for_ind(pid, ind_name)
                    if status != PASS:
                        raise Exception("Poll for indication Failed")

                except Exception, details:
                    kill(pid, SIGKILL)
                    raise Exception(details)

        except Exception, details:
            logger.error("Exception: %s", details)
            status = FAIL

        if status != PASS:
            break

        cleanup_guest_netpool(virt, cxml, test_dom, t_sysname, 
                              s_sysname, clean_net=False)


    #Make sure all subscriptions are really unsubscribed
    for ind, sub in sub_list.iteritems():
        sub.unsubscribe(dict['default_auth'])
        logger.info("Cancelling subscription for %s", ind_names[ind])

    cleanup_guest_netpool(virt, cxml, test_dom, t_sysname, 
                          s_sysname)
    return status


if __name__ == "__main__":
    sys.exit(main())

