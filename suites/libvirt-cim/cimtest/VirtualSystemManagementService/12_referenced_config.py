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
from XenKvmLib.common_util import create_using_definesystem, \
                                  call_request_state_change, \
                                  poll_for_state_change, get_cs_instance
from XenKvmLib import vsms
from VirtLib import utils 
from CimTest.Globals import logger
from XenKvmLib.const import do_main
from CimTest.ReturnCodes import FAIL, PASS
from XenKvmLib.test_doms import destroy_and_undefine_domain 
from XenKvmLib.classes import get_typed_class
from XenKvmLib.assoc import AssociatorNames
from XenKvmLib.test_xml import dumpxml

sup_types = ['Xen', 'XenFV', 'KVM', 'LXC']
test_dom = 'rstest_domain'
test_dom2 = 'rstest_domain2'

mac = "aa:aa:aa:00:00:00"

REQUESTED_STATE = 2
TIME = "00000000000000.000000:000"

def setup_first_guest(ip, virt):
    status = create_using_definesystem(test_dom, ip, virt=virt)
    if status != PASS:
        logger.error("Unable to define %s using DefineSystem()" % test_dom)
        return FAIL

    rc = call_request_state_change(test_dom, ip, REQUESTED_STATE, TIME, virt)
    if rc != 0:
        logger.error("Unable to start %s" % test_dom)
        return FAIL

    status, cs = poll_for_state_change(ip, virt, test_dom, REQUESTED_STATE)
    if status != PASS:
        logger.error("Unable to start %s" % test_dom)
        return FAIL

    return PASS

def get_vssd_ref(ip, virt):
    rc, cs = get_cs_instance(test_dom, ip, virt)
    if rc != 0:
        return None

    cn = "ComputerSystem"
    ccn = get_typed_class(virt, cn)
    vssd = AssociatorNames(ip, 'SettingsDefineState', cn, virt=virt,
                           Name = test_dom, CreationClassName = ccn)

    if len(vssd) != 1:
        logger.error("Returned %i vssd insts for '%s'", len(vssd), test_dom)
        return None

    return vssd[0]

def get_vssd_rasd(virt):
    vssd, def_rasd = vsms.default_vssd_rasd_str(dom_name=test_dom2,
                                                net_type='network',
                                                net_mac=mac, virt=virt)

    rasd = []
    for inst in def_rasd:
        cn = get_typed_class(virt, "NetResourceAllocationSettingData")
        if cn in inst:
            rasd.append(inst)

    params = {} 

    if len(rasd) != 1:
        return params 

    params['vssd'] = vssd
    params['rasd'] = rasd

    return params 

def get_dom_macs(server, dom, virt):
    mac_list = []

    myxml = dumpxml(dom, server, virt=virt)

    lines = myxml.splitlines()
    for l in lines:
        if l.find("mac address=") != -1:
            mac = l.split('=')[1]
            mac = mac.lstrip('\'')
            mac = mac.rstrip('\'/>')
            mac_list.append(mac)
   
    return mac_list 

@do_main(sup_types)
def main():
    options = main.options

    try:
        status = setup_first_guest(options.ip, options.virt)
        if status != PASS:
            raise Exception("Unable to start %s" % test_dom)

        ref = get_vssd_ref(options.ip, options.virt)
        if ref is None:
            raise Exception("Unable to get %s reference" % test_dom)

        define_params = get_vssd_rasd(options.virt)
        if len(define_params) != 2:
            raise Exception("Unable to build VSSD and RASD instances for %s" % \
                            test_dom2)

        status = create_using_definesystem(test_dom2, options.ip, 
                                           params=define_params, ref_config=ref,
                                           virt=options.virt)
        if status != PASS:
            raise Exception("Unable to define %s" % test_dom2)

        dom1_mac_list = get_dom_macs(options.ip, test_dom, options.virt)
        if len(dom1_mac_list) != 1:
            raise Exception("%s has %d macs, expected 1" % (test_dom, 
                            len(dom1_mac_list)))

        dom2_mac_list = get_dom_macs(options.ip, test_dom2, options.virt)
        if len(dom2_mac_list) != 2:
            raise Exception("%s has %d macs, expected 2" % (test_dom2, 
                            len(dom2_mac_list)))

        for item in dom2_mac_list:
            if item != mac and item != dom1_mac_list[0]:
                raise Exception("%s has unexpected mac value, exp: %s %s" % \
                                (item, mac, dom1_mac_list[0]))

        status = PASS
      
    except Exception, details:
        logger.error(details)
        status = FAIL

    destroy_and_undefine_domain(test_dom, options.ip, options.virt)
    destroy_and_undefine_domain(test_dom2, options.ip, options.virt)

    return status 

if __name__ == "__main__":
    sys.exit(main())
    
