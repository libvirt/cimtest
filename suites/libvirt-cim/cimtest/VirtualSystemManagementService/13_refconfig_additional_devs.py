#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
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

import sys
import pywbem
from XenKvmLib.common_util import call_request_state_change, \
                                  poll_for_state_change, get_cs_instance
from XenKvmLib import vsms
from VirtLib import utils 
from CimTest.Globals import logger
from XenKvmLib.const import do_main, KVM_secondary_disk_path, \
                            Xen_secondary_disk_path
from CimTest.ReturnCodes import FAIL, PASS
from XenKvmLib.test_doms import destroy_and_undefine_domain 
from XenKvmLib.classes import get_typed_class
from XenKvmLib.assoc import AssociatorNames
from XenKvmLib.vxml import get_class

sup_types = ['Xen', 'XenFV', 'KVM']
test_dom = 'rstest_domain'
test_dom2 = 'rstest_domain2'
mac1 = '88:aa:bb:cc:ee:ff'
mac2 = '88:aa:bb:cc:ee:aa'

REQUESTED_STATE = 2
TIME = "00000000000000.000000:000"

def get_vssd_ref(ip, virt):
    rc, cs = get_cs_instance(test_dom, ip, virt)
    if rc != 0:
        return None

    cn = "ComputerSystem"
    ccn = get_typed_class(virt, cn)
    an = get_typed_class(virt, 'SettingsDefineState')
    vssd = AssociatorNames(ip, an, ccn, Name = test_dom, CreationClassName = ccn)

    if len(vssd) != 1:
        logger.error("Returned %i vssd insts for '%s'", len(vssd), test_dom)
        return None

    return vssd[0]

def verify_no_dups(ip, virt, cxml, dom):
       
        if cxml.xml_get_disk_source() != cxml.dasd.Address:
            logger.error("%s: Exp disk source %s", dom, cxml.dasd.Address)
            return FAIL

        if cxml.xml_get_disk_dev() != cxml.dasd.VirtualDevice:
            logger.error("%s: Exp disk dev %s", dom, cxml.dasd.VirtualDevice)
            return FAIL

        if cxml.xml_get_net_type() != cxml.nasd.NetworkType:
            logger.error("%s: Exp net type %d", dom, cxml.nasd.NetworkType)
            return FAIL

        if cxml.xml_get_net_mac() != cxml.nasd.Address:
            logger.error("%s: Exp net mac %s", dom, cxml.nasd.Address)
            return FAIL

        vcpus = cxml.xml_get_vcpu()
        if not vcpus.isdigit(): 
            logger.error("Unable to get vcpus value for %s", dom)
            return FAIL

        if int(vcpus) != cxml.pasd.VirtualQuantity:
            logger.error("%s: Exp vcpus %s", dom, cxml.pasd.VirtualQuantity)
            return FAIL

        mem = cxml.xml_get_mem()
        if not mem.isdigit(): 
            logger.error("Unable to get mem value for %s", dom)
            return FAIL

        if cxml.masd.AllocationUnits == "Bytes":
            shift = -10
        elif cxml.masd.AllocationUnits == "KiloBytes":
            shift = 0
        elif cxml.masd.AllocationUnits == "MegaBytes":
            shift = 10 
        elif cxml.masd.AllocationUnits == "GigaBytes":
            multi_by = 20
        else:
            shift = 0

        exp_mem = cxml.masd.VirtualQuantity
        if shift < 0:
            exp_mem >>= -shift
        else:
            exp_mem <<= shift

        if int(mem) != exp_mem:
            logger.error("%s: Exp mem %s", dom, exp_mem)
            return FAIL

        return PASS

@do_main(sup_types)
def main():
    options = main.options

    virt_xml = get_class(options.virt)
    cxml = virt_xml(test_dom, mac=mac1)
    if options.virt == 'Xen':
        test_disk = 'xvdb'
        disk_path = Xen_secondary_disk_path
    else:
        test_disk = 'vdb'
        disk_path = KVM_secondary_disk_path

    cxml2 = virt_xml(test_dom2, mac=mac2, 
                     disk=test_disk, disk_file_path=disk_path)

    try:
        rc = cxml.cim_define(options.ip)
        if not rc: 
            logger.error("Unable define domain %s", test_dom)
            raise Exception("Unable to define domain %s" % test_dom)

        ref = get_vssd_ref(options.ip, options.virt)
        if ref is None:
            raise Exception("Unable to get %s reference" % test_dom)

        rc = cxml2.cim_define(options.ip, ref_conf=ref)
        if not rc: 
            logger.error("Unable define domain %s", test_dom2)
            raise Exception("Unable to define %s" % test_dom2)

        rc = call_request_state_change(test_dom2, options.ip,
                                       REQUESTED_STATE, TIME, options.virt)
        if rc != 0:
            raise Exception("Unable to start %s" % test_dom2)

        status, dom_cs = poll_for_state_change(options.ip, options.virt, 
                                               test_dom2, REQUESTED_STATE)
        if status != PASS:
            raise Exception("%s didn't change state as expected" % test_dom2)

        status = verify_no_dups(options.ip, options.virt, cxml2, test_dom2)
        if status != PASS:
            raise Exception("%s devices not defined as expected" % test_dom2)

        status = PASS
      
    except Exception, details:
        logger.error(details)
        status = FAIL

    destroy_and_undefine_domain(test_dom, options.ip, options.virt)
    destroy_and_undefine_domain(test_dom2, options.ip, options.virt)

    return status 

if __name__ == "__main__":
    sys.exit(main())
    
