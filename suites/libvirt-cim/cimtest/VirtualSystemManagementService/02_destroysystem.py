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
from XenKvmLib.xm_virt_util import domain_list, active_domain_list
from XenKvmLib import vsms, vxml
from XenKvmLib.classes import get_typed_class
from XenKvmLib.const import do_main
from CimTest.Globals import logger
from CimTest.ReturnCodes import PASS, FAIL

sup_types = ['Xen', 'KVM', 'XenFV', 'LXC']
default_dom = 'test_domain'

def cleanup_env(ip, cxml):
    cxml.destroy(ip)
    cxml.undefine(ip)

@do_main(sup_types)
def main():
    options = main.options
    
    service = vsms.get_vsms_class(options.virt)(options.ip)
    cxml = vxml.get_class(options.virt)(default_dom)
    ret = cxml.cim_define(options.ip)
    if not ret:
        logger.error("Failed to define the dom: %s", default_dom)
        return FAIL
    ret = cxml.start(options.ip)
    if not ret:
        logger.error("Failed to start the dom: %s", default_dom)
        cleanup_env(options.ip, cxml)
        return FAIL

    classname = get_typed_class(options.virt, 'ComputerSystem')
    cs_ref = CIMInstanceName(classname, keybindings = {
                                        'Name':default_dom,
                                        'CreationClassName':classname})
    list_before = domain_list(options.ip, options.virt)
    if default_dom not in list_before:
        logger.error("Domain not in domain list")
        cleanup_env(options.ip, cxml)
        return FAIL
    
    try:
        service.DestroySystem(AffectedSystem=cs_ref)
    except Exception, details:
        logger.error('Unknow exception happened')
        logger.error(details)
        cleanup_env(options.ip, cxml)
        return FAIL

    list_after = domain_list(options.ip, options.virt)

    if default_dom in list_after:
        logger.error("Domain %s not destroyed: provider didn't return error" % \
                     default_dom)
        cleanup_env(options.ip, cxml)
        status = FAIL
    else:
        status = PASS

    return status
     

if __name__ == "__main__":
    sys.exit(main())
    
