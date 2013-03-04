#!/usr/bin/python
#
# Copyright 2009 IBM Corp.
#
# Authors:
#    Yogananth subramanian <anantyog@linux.vnet.ibm.com>
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
# This testcase verifies defining and starting domain with bridge interface
#

import sys
import random
from XenKvmLib import vxml
from CimTest.Globals import logger
from CimTest.ReturnCodes import FAIL, PASS
from XenKvmLib.const import default_network_name, do_main 
from XenKvmLib.common_util import create_netpool_conf, destroy_netpool

sup_types = ['Xen', 'KVM', 'XenFV']
default_dom = 'brgtest_domain'
nmac = '88:aa:bb:cc:ee:ff'
npool_name = default_network_name + str(random.randint(1, 100)) 
brg_name = "br" + str(random.randint(1, 100)) 

@do_main(sup_types)
def main():
    options = main.options

    status, net_name = create_netpool_conf(options.ip, options.virt,
                                           use_existing=False,
                                           net_name=npool_name,
                                           bridge_name=brg_name)
    if status != PASS:
        logger.error('Unable to create network pool')
        return FAIL
    cxml = vxml.get_class(options.virt)(default_dom, mac=nmac,
                                        ntype="bridge",
                                        net_name=brg_name)

    try:
        ret = cxml.cim_define(options.ip)
        if not ret:
            raise Exception("Failed to define the dom: %s" % default_dom)
        ret = cxml.cim_start(options.ip)
        if ret:
            cxml.undefine(options.ip)
            raise Exception("Failed to start the dom: %s" % default_dom)

        cxml.cim_destroy(options.ip)
        cxml.undefine(options.ip)

    except Exception, details:
        logger.error(details)
        status = FAIL

    destroy_netpool(options.ip, options.virt, net_name)

    return status

if __name__ == "__main__":
    sys.exit(main())
    
