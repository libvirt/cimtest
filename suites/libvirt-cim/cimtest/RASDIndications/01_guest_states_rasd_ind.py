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
# This testcase is used to verify the Created|Deleted 
# RASD Indications for a guest.
#
#                                                      Date : 21-09-2009
#

import sys
from signal import SIGKILL
from socket import gethostname
from os import kill, fork, _exit
from XenKvmLib.vxml import get_class
from XenKvmLib.xm_virt_util import active_domain_list
from CimTest.Globals import logger
from XenKvmLib.const import do_main, CIM_ENABLE, CIM_DISABLE, \
	                    get_provider_version
from CimTest.ReturnCodes import PASS, FAIL, SKIP
from XenKvmLib.common_util import poll_for_state_change 
from XenKvmLib.indications import sub_ind, handle_request, poll_for_ind

sup_types = ['KVM', 'Xen', 'XenFV']
libvirt_guest_rasd_indication_rev = 980

def create_guest(test_dom, ip, virt, cxml, ind_name):
    try:
        ret = cxml.cim_define(ip)
        if not ret:
            raise Exception("Failed to define domain %s" % test_dom)

        status, dom_cs = poll_for_state_change(ip, virt, test_dom,
                                               CIM_DISABLE)
        if status != PASS:
            raise Exception("Dom '%s' not in expected state '%s'" \
                            % (test_dom, CIM_DISABLE))

        ret = cxml.cim_start(ip)
        if ret:
            raise Exception("Failed to start the domain '%s'" % test_dom)
            cxml.undefine(ip)

        status, dom_cs = poll_for_state_change(ip, virt, test_dom,
                                               CIM_ENABLE)
        if status != PASS:
            raise Exception("Dom '%s' not in expected state '%s'" \
                            % (test_dom, CIM_ENABLE))

    except Exception, details:
        logger.error("Exception details: %s", details)
        return FAIL, cxml

    return PASS, cxml

def gen_indication(test_dom, s_sysname, virt, cxml, ind_name):
    status = FAIL
    try:
        active_doms = active_domain_list(s_sysname, virt)
        if test_dom not in active_doms:
            status, cxml = create_guest(test_dom, s_sysname, virt, cxml, ind_name)
            if status != PASS:
                raise Exception("Error setting up the guest '%s'" % test_dom)

        if ind_name == "delete":
            ret = cxml.cim_destroy(s_sysname)
            if not ret:
                raise Exception("Failed to destroy domain  '%s'"  % test_dom)

    except Exception, details:
        logger.error("Exception details :%s", details)
        return FAIL, cxml

    return PASS, cxml

@do_main(sup_types)
def main():
    options = main.options
    virt = options.virt
    s_sysname = options.ip

    cim_rev, changeset = get_provider_version(virt, s_sysname)
    if cim_rev < libvirt_guest_rasd_indication_rev:
        logger.info("Support for Guest Resource Indications is available in "
                    "Libvirt-CIM rev '%s'", libvirt_guest_rasd_indication_rev)
        return SKIP

    status = FAIL
    test_dom = 'VM_' + gethostname()
    ind_names = {
                 'create' : 'ResourceAllocationSettingDataCreatedIndication',
                 'delete' : 'ResourceAllocationSettingDataDeletedIndication' 
                }

    virt_xml = get_class(virt)
    cxml = virt_xml(test_dom)
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
                                                  virt, cxml, ind)
                    if status != PASS:
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
        
    #Make sure all subscriptions are really unsubscribed
    for ind, sub in sub_list.iteritems():
        sub.unsubscribe(dict['default_auth'])
        logger.info("Cancelling subscription for %s", ind_names[ind])

    active_doms = active_domain_list(s_sysname, virt)
    if test_dom in active_doms:
       ret = cxml.cim_destroy(s_sysname)
       if not ret:
           logger.error("Failed to Destroy the domain")
           return FAIL

    return status
if __name__ == "__main__":
    sys.exit(main())

