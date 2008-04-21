#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Kaitlin Rupert <karupert@us.ibm.com>
#    Veerendra Chandrappa <vechandr@in.ibm.com>
#    Zhengang Li <lizg@cn.ibm.com>
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

# This test case is used to verify the Virtual System State Transition
# information is captured in the RequestedState Property of the VS.
# The test is considered to be successful if 'Suspend' of the 'defined' domU
# is not possible
# Date: 14-12-2007

import sys
from XenKvmLib import computersystem
from VirtLib import utils
from XenKvmLib import vxml
from XenKvmLib.test_doms import destroy_and_undefine_all
from CimTest.Globals import do_main
from CimTest import Globals
from CimTest.ReturnCodes import PASS, FAIL

sup_types = ['Xen', 'KVM', 'XenFV']
test_dom = "domgst"

@do_main(sup_types)
def main():
    options = main.options
    status = FAIL
    
    cxml = vxml.get_class(options.virt)(test_dom)

#define VS
    try:
        ret = cxml.define(options.ip)
        if not ret:
            Globals.logger.error(Globals.VIRSH_ERROR_DEFINE % test_dom)
            return status
        
        cs = computersystem.get_cs_class(options.virt)(options.ip, test_dom)
        if not (cs.Name == test_dom) :
            Globals.logger.error("Error: VS %s not found" % test_dom)
            cxml.undefine(options.ip)
            return status

    except Exception, detail:
        Globals.logger.error("Errors: %s" % detail)

#Suspend the defined VS
    
    try:
        ret = cxml.run_virsh_cmd(options.ip, "suspend")
        if not ret :
            Globals.logger.info("Suspending defined VS %s failed, as expected" \
% test_dom)
            status = PASS
        else :
            Globals.logger.info("Error: Suspending defined VS %s should not \
have been allowed" % test_dom)
            status = FAIL 

    except Exception, detail:
        Globals.logger.error("Error: %s" % detail)

    ret = cxml.undefine(options.ip)
    return status

if __name__ == "__main__":
    sys.exit(main())

