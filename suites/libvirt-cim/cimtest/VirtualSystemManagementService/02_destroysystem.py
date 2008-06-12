#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Guolian Yun <yunguol@cn.ibm.com>
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

import sys
import pywbem
from pywbem.cim_obj import CIMInstanceName
from VirtLib import utils
from VirtLib.live import domain_list, active_domain_list
from XenKvmLib import vsms, vxml
from XenKvmLib.classes import get_typed_class
from XenKvmLib.const import CIM_REV
from CimTest.Globals import do_main
from CimTest.Globals import logger
from CimTest.ReturnCodes import PASS, FAIL

sup_types = ['Xen', 'KVM', 'XenFV', 'LXC']
default_dom = 'test_domain'
rev = 528

@do_main(sup_types)
def main():
    options = main.options
    
    service = vsms.get_vsms_class(options.virt)(options.ip)
    cxml = vxml.get_class(options.virt)(default_dom)
    cxml.define(options.ip)
    cxml.start(options.ip)

    classname = get_typed_class(options.virt, 'ComputerSystem')
    cs_ref = CIMInstanceName(classname, keybindings = {
                                        'Name':default_dom,
                                        'CreationClassName':classname})
    if CIM_REV < rev:
        dl_func = active_domain_list
    else:
        dl_func = domain_list
    list_before = dl_func(options.ip, options.virt)
    status = PASS
    rc = -1
    
    try:
        service.DestroySystem(AffectedSystem=cs_ref)
        rc = 0
    except Exception, details:
        logger.error('Unknow exception happened')
        logger.error(details)
        status = FAIL

    list_after = dl_func(options.ip, options.virt)

    status = PASS
    if default_dom not in list_before:
        logger.error("Domain not started, check config")
        status = FAIL
    else:
        destroyed = set(list_before) - set(list_after)
        if len(destroyed) != 1:
            logger.error("Destroyed multiple domains")
            status = FAIL
        elif default_dom not in destroyed:
            logger.error("Wrong domain destroyed")
            status = FAIL

    cxml.undefine(options.ip)

    return status
     

if __name__ == "__main__":
    sys.exit(main())
    
