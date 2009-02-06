#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Veerendra Chandrappa <vechandr@in.ibm.com>
#    Guolian Yun <yunguol@cn.ibm.com>
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

# This test case verifies whether a define guest has the appropriate 
# Memory instances associated with it. 
# Steps:
#  1. Define a guest using DefineSystem().
#  2. Get the CIM instance of the guest created using DefineSystem().
#  3. Get the Mem instances associated with the guest. 
#  4. Verify the DeviceId and domName with the instance info. 

import sys
from CimTest.ReturnCodes import PASS, FAIL
from XenKvmLib.devices import get_dom_mem_inst
from CimTest.Globals import logger
from XenKvmLib.const import do_main
from XenKvmLib.vxml import get_class

sup_types = ['Xen', 'KVM', 'XenFV', 'LXC']
default_dom = "domu"

def check_mem(memInst):
    for mem in memInst:
        if mem['SystemName'] != default_dom: 
            logger.error("Inst returned is for guest %s, expected guest %s.", 
                         mem['SystemName'], default_dom)
            return FAIL

        devid = "%s/%s" % (default_dom, "mem" )
       
        if mem['DeviceID'] != devid: 
            logger.error("DeviceID %s does not match expected %s.", 
                         mem['DeviceID'], devid)
            return FAIL

    logger.info("Verified domain %s having DeviceID %s", default_dom, devid) 

    return PASS 

@do_main(sup_types)
def main():
    options = main.options
    status = FAIL

    cxml = get_class(options.virt)(default_dom)
    try:
        ret = cxml.cim_define(options.ip)
        if not ret:
            raise Exception("Failed to define the guest: %s" % default_dom)

        memInst = get_dom_mem_inst(options.virt, options.ip, default_dom)
        if len(memInst) == 0:
            raise Exception("Failed to get mem instances for %s" % default_dom)

        status = check_mem(memInst)
        if status != PASS:
            raise Exception("Memory inst for %s not as expected." % default_dom)

    except Exception, detail:
        logger.error("Exception: %s", detail)
        status =  FAIL

    cxml.undefine(options.ip)

    return status

if __name__ == "__main__":
    sys.exit(main())
    
