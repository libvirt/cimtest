#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Guolian Yun <yunguol@cn.ibm.com>
#    Zhengang Li <lizg@cn.ibm.com>
#    Deepti B. Kalakeri <deeptik@linux.vnet.ibm.com>
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
# Test case to verify DestroySystem() of VSMS provider.
#
#

import sys
from XenKvmLib.xm_virt_util import domain_list, active_domain_list
from XenKvmLib import vxml
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
    
    cxml = vxml.get_class(options.virt)(default_dom)

    try:
        ret = cxml.cim_define(options.ip)
        if not ret:
            logger.error("Failed to define the domain '%s'", default_dom)
            return FAIL

        defined_domains = domain_list(options.ip, options.virt)
        if default_dom not in defined_domains:
            logger.error("Failed to find defined domain '%s'", default_dom)
            return FAIL

        ret = cxml.cim_start(options.ip)
        if ret:
            logger.error("Failed to start the domain '%s'", default_dom)
            cxml.undefine(options.ip)
            return FAIL

        list_before = active_domain_list(options.ip, options.virt)
        if default_dom not in list_before:
            raise Exception("Domain '%s' is not in active domain list" \
                             % default_dom)

        ret = cxml.cim_destroy(options.ip)
        if not ret:
            raise Exception("Failed to destroy domain '%s'" % default_dom)

        list_after = domain_list(options.ip, options.virt)
        if default_dom in list_after:
            raise Exception("DestroySystem() failed to destroy domain '%s'.." \
                            "Provider did not return any error" % default_dom)
        else:
            logger.info("DestroySystem() successfully destroyed and undefined"\
                        " domain '%s'", default_dom)

    except Exception, details:
        logger.error("Exception details: %s", details)
        cleanup_env(options.ip, cxml)
        return FAIL

    return PASS
     

if __name__ == "__main__":
    sys.exit(main())
    
