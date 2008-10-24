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
from VirtLib.live import domain_list
from XenKvmLib.enumclass import EnumInstances
from CimTest.Globals import logger, CIM_ERROR_ENUMERATE
from XenKvmLib.classes import get_typed_class
from XenKvmLib.const import do_main 
from CimTest.ReturnCodes import PASS, FAIL
from XenKvmLib.common_util import get_host_info

SHAREMODE = 3
REDIRECTION_SER_TYPE = 3
MAX_SAP_SESSIONS = 65535

sup_types = ['Xen', 'KVM', 'XenFV', 'LXC']
@do_main(sup_types)
def main():
    virt = main.options.virt
    server = main.options.ip

    status, host_name, host_cn = get_host_info(server, virt)
    if status != PASS:
        return status

    cname = 'ConsoleRedirectionService'
    classname = get_typed_class(virt, cname)
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
                   'MaxConcurrentEnabledSAPs': MAX_SAP_SESSIONS
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
