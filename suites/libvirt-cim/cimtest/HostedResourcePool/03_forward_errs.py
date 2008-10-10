#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Guolian Yun <yunguol@cn.ibm.com>
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

import sys
import pywbem
from XenKvmLib import assoc
from XenKvmLib import enumclass
from XenKvmLib.common_util import get_host_info
from XenKvmLib.common_util import try_assoc
from CimTest import Globals
from CimTest.Globals import logger
from CimTest.ReturnCodes import PASS, FAIL, XFAIL_RC
from XenKvmLib.const import do_main
from XenKvmLib.classes import get_typed_class

bug = "00007"
expr_values = {
        "invalid_ccname" : {"rc" : pywbem.CIM_ERR_NOT_FOUND, 
                  "desc" : "No such instance (CreationClassName)"},
        "invalid_name"   : {"rc" : pywbem.CIM_ERR_NOT_FOUND, 
                  "desc" : "No such instance (Name)"}
             }

sup_types=['Xen', 'KVM', 'XenFV', 'LXC']
@do_main(sup_types)
def main():
    options = main.options
    keys = ['Name', 'CreationClassName']
    status, host_sys, host_cn = get_host_info(options.ip, options.virt)
    if status != PASS:
        logger.error("Error in calling get_host_info function")
        return FAIL

    conn = assoc.myWBEMConnection('http://%s' % options.ip,                                        
                                  (Globals.CIM_USER, Globals.CIM_PASS),
                                                       Globals.CIM_NS)
    classname = host_cn
    assoc_classname = get_typed_class(options.virt, "HostedResourcePool")
    keys = {"Name" : host_sys, "CreationClassName" : "wrong"}
    ret =  try_assoc(conn, classname, assoc_classname, keys, 
                     "Name", expr_values['invalid_ccname'], bug_no="")
    if ret != PASS:
        if host_cn == 'Linux_ComputerSystem':
            return XFAIL_RC(bug)
        else:
            logger.error("------ FAILED: Invalid CreationClassName Key Value.------")
            return FAIL

    keys = {"Name" : "wrong", "CreationClassName" : host_cn}
    ret = try_assoc(conn, classname, assoc_classname, keys, 
                  "CreationClassName", expr_values['invalid_name'], bug_no="")
    if ret != PASS:
        if host_cn == 'Linux_ComputerSystem':
            return XFAIL_RC(bug)
        else:
            logger.error("------ FAILED: Invalid Name Key Value.------")
            return FAIL

    return PASS
if __name__ == "__main__":
    sys.exit(main())
