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
# This test verifies the output of the ModifyResourceSettings() call.
# ModifyResourceSettings() returns an array of RASS references.  This reference
# should match the reference of the instance RASD we pass to the 
# ModifyResourceSettings() call. 

import sys
from pywbem import CIMInstanceName
from XenKvmLib.vsms import get_vsms_class, get_dasd_class 
from XenKvmLib import vxml
from CimTest.Globals import logger, CIM_NS
from XenKvmLib.const import do_main
from CimTest.ReturnCodes import PASS, FAIL
from XenKvmLib.vsms_util import call_modify_res 

sup_types = ['Xen', 'KVM', 'XenFV']
default_dom = 'rstest_domain'

@do_main(sup_types)
def main():
    options = main.options 

    cn = "KVM_DiskResourceAllocationSettingData"

    service = get_vsms_class(options.virt)(options.ip)
    cxml = vxml.get_class(options.virt)(default_dom)

    ndpath = cxml.secondary_disk_path
    dasd = get_dasd_class(options.virt)(dev=cxml.xml_get_disk_dev(),
                                        source=ndpath, 
                                        name=default_dom)
    status = FAIL
  
    try:
        ret = cxml.cim_define(options.ip)
        if not ret:
            raise Exception("Failed to define the dom: %s" % default_dom)

        status, out = call_modify_res(service, dasd)
        if status != PASS:
            raise Exception("Failed to modify %s's disk" % default_dom)

        keys = {"InstanceID" : dasd.InstanceID}
        ref = CIMInstanceName(cn, keybindings=keys, namespace=CIM_NS)

        if len(out) != 1:
            raise Exception("Expected 1 resulting RASD, got %d" % len(out))

        if out[0] != ref:
            raise Exception("Expected %s to be created, %s was instead" %  \
                            (ref, out[0]))

        status = PASS

    except Exception, details:
        logger.error(details)
        status = FAIL

    cxml.destroy(options.ip)
    cxml.undefine(options.ip)

    return status

if __name__ == "__main__":
    sys.exit(main())
 
