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
from XenKvmLib.common_util import try_assoc
from CimTest import Globals
from CimTest.Globals import logger
from CimTest.ReturnCodes import PASS
from CimTest.Globals import do_main, platform_sup
from XenKvmLib.classes import get_typed_class

expr_values = {
                "Invalid_InstanceID_KeyName" : {
                                                  "rc"   : pywbem.CIM_ERR_FAILED, \
                                                  "desc" : "Missing InstanceID"
                                               }, \
                "Invalid_InstanceID_KeyValue" : {
                                                   "rc"  : pywbem.CIM_ERR_NOT_FOUND, \
                                                   "desc": "No such instance"
                                                }
              }

@do_main(platform_sup)
def main():
    options = main.options
    status = PASS

    assoc_classname = get_typed_class(options.virt, "HostedResourcePool")
    proc_cn  = get_typed_class(options.virt, "ProcessorPool")
    mem_cn   = get_typed_class(options.virt, "MemoryPool")
    conn = assoc.myWBEMConnection('http://%s' % options.ip,
                                  (Globals.CIM_USER, Globals.CIM_PASS),
                                                       Globals.CIM_NS)

    poollist = {mem_cn : "MemoryPool/0", proc_cn : "ProcessorPool/0"}
    for k, v in poollist.items():
        keys = { "Wrong" : v} 
        ret = try_assoc(conn, k, assoc_classname, keys, "InstanceID", \
                        expr_values['Invalid_InstanceID_KeyName'], bug_no="")
        if ret != PASS:
            logger.error("------ FAILED: Invalid InstanceID Key Name.------")
            status = ret

    poollist = {mem_cn : "wrong", proc_cn : "wrong"}
    for k, v in poollist.items():
        keys = { "InstanceID" : v} 
        ret = try_assoc(conn, k, assoc_classname, keys, "InstanceID", \
                        expr_values['Invalid_InstanceID_KeyValue'], bug_no="")
        if ret != PASS:
            logger.error("------ FAILED: Invalid Name Key Value.------")
            status = ret

    return status        
if __name__ == "__main__":
    sys.exit(main())
