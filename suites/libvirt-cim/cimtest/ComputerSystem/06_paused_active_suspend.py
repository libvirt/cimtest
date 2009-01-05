#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Deepti B. Kalakeri <dkalaker@in.ibm.com>
#    Kaitlin Rupert <karupert@us.ibm.com>
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

# This test case is used to verify the Virtual System State Transition,
# information related to this is captured in the RequestedState Property
# of the VS.
# The test is considered to be successful if RequestedState Property 
# has a value of "9" when the VS is moved from active to paused state.
#
#						Date  :18-10-2007

import sys
from XenKvmLib.vxml import get_class 
from CimTest.Globals import logger
from XenKvmLib.const import do_main, CIM_ENABLE, CIM_PAUSE
from CimTest.ReturnCodes import PASS, FAIL, XFAIL_RC
from XenKvmLib.classes import get_typed_class
from XenKvmLib.enumclass import GetInstance

sup_types = ['Xen', 'KVM', 'XenFV', 'LXC']
test_dom = "DomST1"
bug_libvirt = "00011"

@do_main(sup_types)
def main():
    options = main.options
    status = FAIL
    server = options.ip
    virt = options.virt

    cxml = get_class(virt)(test_dom)

    #Create VS
    pause_failed = False
    try:
        ret = cxml.cim_define(server)
        if not ret:
            raise Exception("VS '%s' was not defined" % test_dom)

        status = cxml.cim_start(server)
        if status != PASS:
            raise Exception("Unable start dom '%s'" % test_dom)

        status = cxml.check_guest_state(options.ip, CIM_ENABLE)
        if status != PASS:
            raise Exception("%s not in expected state" % test_dom)

        #Pause the VS
        status = cxml.cim_pause(server)
        if status != PASS:
            pause_failed = True 
            raise Exception("Unable pause dom '%s'" % test_dom)

        status = cxml.check_guest_state(options.ip, CIM_PAUSE)
        if status != PASS:
            raise Exception("%s not in expected state" % test_dom)

    except Exception, detail:
        logger.error("Exception variable: %s" % detail)
        status = FAIL

    cxml.destroy(server)
    cxml.undefine(options.ip)

    if pause_failed and virt == 'LXC':
        return XFAIL_RC(bug_libvirt)
    
    return status
if __name__ == "__main__":
    sys.exit(main())
