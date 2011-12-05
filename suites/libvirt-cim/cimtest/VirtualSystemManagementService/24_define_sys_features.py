#!/usr/bin/python
#
# Copyright 2009 IBM Corp.
#
# Authors:
#    Kaitlin Rupert <karupert@us.ibm.com>
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
from XenKvmLib import vxml
from CimTest.Globals import logger
from CimTest.ReturnCodes import FAIL, PASS
from XenKvmLib.const import do_main 

#Xen paravirt doesn't support ACPI, PAE, or APIC
sup_types = ['KVM', 'XenFV']
default_dom = 'features_domain'

@do_main(sup_types)
def main():
    options = main.options

    status = FAIL

    cxml = vxml.get_class(options.virt)(default_dom, pae=True, 
                                        acpi=True, apic=True)

    try:
        ret = cxml.cim_define(options.ip)
        if not ret:
            raise Exception("Failed to define the dom: %s" % default_dom)

        cxml.dumpxml(options.ip)

        if cxml.xml_get_pae() is None:
            raise Exception("Failed to set pae for dom: %s" % default_dom)

        if cxml.xml_get_acpi() is None:
            raise Exception("Failed to set acpi for dom: %s" % default_dom)

        if cxml.xml_get_apic() is None:
            raise Exception("Failed to set apic for dom: %s" % default_dom)

        status = PASS

    except Exception, details:
        logger.error(details)
        status = FAIL

    cxml.cim_destroy(options.ip)

    return status

if __name__ == "__main__":
    sys.exit(main())
    
