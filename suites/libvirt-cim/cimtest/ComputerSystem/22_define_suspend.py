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
from VirtLib import utils
from XenKvmLib import vxml
from XenKvmLib.test_doms import destroy_and_undefine_domain
from CimTest.Globals import logger
from XenKvmLib.const import do_main 
from CimTest.ReturnCodes import PASS, FAIL
from XenKvmLib.common_util import create_using_definesystem, \
                                  call_request_state_change, get_cs_instance

sup_types = ['Xen', 'KVM', 'XenFV', 'LXC']
test_dom = "domgst"

DEFINE_STATE = 3
SUSPND_STATE = 9
TIME        = "00000000000000.000000:000"

def chk_state(domain_name, ip, en_state, virt):
    rc, cs = get_cs_instance(domain_name, ip, virt)
    if rc != 0:
        return rc

    if cs.EnabledState != en_state:
        logger.error("EnabledState should be %d not %d",
                     en_state, cs.EnabledState)
        return FAIL

    return PASS

@do_main(sup_types)
def main():
    options = main.options

    try:
        # define the vs
        status = create_using_definesystem(test_dom, options.ip,
                                           virt=options.virt)
        if status != PASS:
            logger.error("Unable to define %s using DefineSystem()" % test_dom)
            return status

        # suspend the vs
        status = call_request_state_change(test_dom, options.ip, SUSPND_STATE,
                                           TIME, virt=options.virt)
        if status != PASS:
            logger.info("Suspending defined %s failed, as expected" % test_dom)
            status = PASS

            status = chk_state(test_dom, options.ip, DEFINE_STATE, options.virt)
            if status != PASS:
                logger.error("%s should have been in defined state" % test_dom)
                status = FAIL 
            
        else :
            logger.error("Suspending defined %s should have failed" % test_dom)
            status = FAIL 

    except Exception, detail:
        logger.error("Error: %s" % detail)
        status = FAIL 

    destroy_and_undefine_domain(test_dom, options.ip, options.virt)
    return status

if __name__ == "__main__":
    sys.exit(main())

