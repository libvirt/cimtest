#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Deepti B. Kalakeri <dkalaker@in.ibm.com>
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
# This test case is used to verify the RedirectionService
# properties in detail.
#
#                                               Date : 22-10-2008
#

import sys
from sets import Set
from XenKvmLib.xm_virt_util import domain_list, active_domain_list
from XenKvmLib.enumclass import EnumInstances
from CimTest.Globals import logger, CIM_ERROR_ENUMERATE
from XenKvmLib.classes import get_typed_class
from XenKvmLib.const import do_main 
from CimTest.ReturnCodes import PASS, FAIL, SKIP
from XenKvmLib.common_util import get_host_info
from XenKvmLib.const import get_provider_version 

SHAREMODE = 3
REDIRECTION_SER_TYPE = 3
CRS_MAX_SAP_REV = 724 
libvirtcim_hr_crs_changes = 688

sup_types = ['Xen', 'KVM', 'XenFV', 'LXC']
@do_main(sup_types)
def main():
    virt = main.options.virt
    server = main.options.ip

   # This check is required for libivirt-cim providers which do not have 
   # CRS changes in it and the CRS provider is available with revision >= 688.
    curr_cim_rev, changeset = get_provider_version(virt, server)
    if curr_cim_rev  < libvirtcim_hr_crs_changes:
        logger.info("ConsoleRedirectionService provider not supported, "
                    "hence skipping the tc ....")
        return SKIP 

    status, host_name, host_cn = get_host_info(server, virt)
    if status != PASS:
        return status

    cname = 'ConsoleRedirectionService'
    classname = get_typed_class(virt, cname)

    cim_rev, changeset = get_provider_version(virt, server)
    #  This branch should be removed once the F9 rpm has changes with
    #  Revision >= 724, and max_sap_sessions = 65535 should be used
    #  for verification.
    if cim_rev < CRS_MAX_SAP_REV:
        inactive_active_doms = domain_list(server, virt)
        active_doms = active_domain_list(server, virt)
        inactive_doms = len(Set(inactive_active_doms) - Set(active_doms))
        max_sap_sessions =  2 * inactive_doms
    else:
        max_sap_sessions = 65535

    crs_list =  {
                   'ElementName'             : cname,
                   'SystemCreationClassName' : host_cn, 
                   'SystemName'              : host_name,
                   'CreationClassName'       : classname,
                   'Name'                    : cname,
                   'RedirectionServiceType'  : [REDIRECTION_SER_TYPE],
                   'SharingMode'             : SHAREMODE,
                   'EnabledState'            : 2,
                   'EnabledDefault'          : 2,
                   'RequestedState'          : 12,
                   'MaxConcurrentEnabledSAPs': max_sap_sessions
                }

    try:
        crs = EnumInstances(server, classname)
    except Exception, detail:
        logger.error(CIM_ERROR_ENUMERATE, classname)
        logger.error("Exception: %s", detail)
        return FAIL

    if len(crs) != 1:
        logger.error("'%s' returned %i records, expected 1", classname, len(crs))
        return FAIL

    crs_val = crs[0]
    for k, exp_val in crs_list.iteritems():
        res_val = eval("crs_val." + k)
        if res_val != exp_val:
            logger.error("'%s' Mismatch", k)
            logger.error("Expected '%s', Got '%s'", exp_val, res_val)
            return FAIL
    return PASS

if __name__ == "__main__":
    sys.exit(main())
