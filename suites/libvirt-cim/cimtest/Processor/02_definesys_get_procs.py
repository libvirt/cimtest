#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Kaitlin Rupert <karupert@us.ibm.com>
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

# This test case verifies whether a define guest has the appropriate 
# Processor instances associated with it. 

# Steps:
#  1. Define a guest using DefineSystem().
#  2. Get the CIM instance of the guest created using DefineSystem().
#  3. Get the processor instances associated with the guest. 
#  4. Verify processor instance info. 
#

import sys
from XenKvmLib.vxml import get_class
from XenKvmLib.devices import get_dom_proc_insts
from CimTest.Globals import logger
from XenKvmLib.const import do_main
from CimTest.ReturnCodes import PASS, FAIL

sup_types = ['Xen', 'KVM', 'XenFV']

default_dom = 'test_domain'
test_vcpus = 1

def check_processors(procs):
    if len(procs) != test_vcpus:
        logger.error("%d vcpu instances were returned. %d expected", 
                     len(procs), test_vcpus)
        return FAIL

    for proc in procs:
        if proc['SystemName'] != default_dom: 
            logger.error("Inst returned is for guest %s, expected guest %s.", 
                         procs['SystemName'], default_dom)
            return FAIL

        devid = "%s/%s" % (default_dom, test_vcpus - 1)

        if proc['DeviceID'] != devid: 
            logger.error("DeviceID %s does not match expected %s.", 
                         procs['DeviceID'], devid)
            return FAIL

    return PASS
        
@do_main(sup_types)
def main():
    options = main.options
    status = FAIL 

    try:
        cxml = get_class(options.virt)(default_dom)
        ret = cxml.cim_define(options.ip)
        if not ret:
            raise Exception("Failed to define the guest: %s" % default_dom)

        proc_list = get_dom_proc_insts(options.virt, options.ip, default_dom)
        if len(proc_list) == 0:
            raise Exception("Failed to retrieve vcpu instances for %s" \
                            % default_dom)

        status = check_processors(proc_list)
        if status != PASS:
            raise Exception("Processor instances for %s are not as expected." \
                            % default_dom)
   
    except Exception, detail:
        logger.error("Exception: %s" % detail)
        status = FAIL

    cxml.undefine(options.ip)

    return status

if __name__ == "__main__":
    sys.exit(main())
    
