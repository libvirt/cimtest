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
import pywbem
from XenKvmLib.classes import get_typed_class
from XenKvmLib.vxml import XenXML, KVMXML, get_class
from XenKvmLib.test_doms import undefine_test_domain 
from XenKvmLib.common_util import create_using_definesystem 
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
            logger.error("Inst returned is for guesst %s, expected guest %s.", 
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
    status = PASS

    undefine_test_domain(default_dom, options.ip)

    try:
        rc = create_using_definesystem(default_dom, options.ip, params=None,
                                       ref_config=' ', exp_err=None, 
                                       virt=options.virt)
        if rc != 0:
            raise Exception("Unable create domain %s using DefineSystem()" \
                            % default_dom)

        proc_list = get_dom_proc_insts(options.virt, options.ip, default_dom)
        if len(proc_list) == 0:
            raise Exception("Failied to retrieve vcpu instances for %s" \
                            % default_dom)

        rc = check_processors(proc_list)
        if rc != 0:
            raise Exception("Processor instances for %s are not as expected." \
                            % default_dom)

    except Exception, detail:
        logger.error("Exception: %s" % detail)
        status = FAIL

    undefine_test_domain(default_dom, options.ip)

    return status

if __name__ == "__main__":
    sys.exit(main())
    
