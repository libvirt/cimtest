#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
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
# This tc is used to verify the that the
# ResourceAllocationFromPool asscoiation returns error
# when guest is associated to a non-existing virtual network pool.
# 
# The does the following: 
# 1) creates a guest with a network device that is not part of a known pool, 
# 2) call ResourceAllocatedFromPool with the reference to that device.
# 3) Verifies for the following error:
# 
# Command:
# --------
# wbemcli ain -ac KVM_ResourceAllocationFromPool
# 'http://localhost:5988/root/virt:KVM_NetResourceAllocationSettingData.
# InstanceID="test-kvm/24:42:53:21:52:45"'
# 
# 
# Output:
# -------
# error no   : CIM_ERR_FAILED 
# error desc : "Unable to determine pool of `test-kvm/24:42:53:21:52:45';" 
#
#                                                        Date : 04-04-2008 
#
import sys
import pywbem
import random
from VirtLib import live
from XenKvmLib import assoc, enumclass
from XenKvmLib.common_util import try_assoc
from XenKvmLib.test_doms import destroy_and_undefine_all
from CimTest import Globals
from CimTest.Globals import logger, CIM_ERROR_ENUMERATE
from CimTest.ReturnCodes import PASS, FAIL
from CimTest.Globals import do_main, platform_sup
from XenKvmLib.vxml import get_class
from XenKvmLib.classes import get_typed_class

test_dom   = "RAPF_domain"
test_mac   = "00:11:22:33:44:aa"
test_vcpus = 1

def get_unique_bridge():
    bridge = "invalid-bridge"
    bridge_list = live.available_bridges(server) 
    while bridge in bridge_list:
        bridge = bridge + str(random.randint(1, 100))
  
    return bridge

def setup_env():
    vsxml_info = None
    if virt == "Xen":
        test_disk = "xvda"
    else:    
        test_disk = "hda"

    virt_xml =  get_class(virt)
    vsxml_info = virt_xml(test_dom, vcpus = test_vcpus, mac = test_mac, disk = test_disk)

    bridge = vsxml_info.xml_get_net_bridge()
    if bridge == None:
        bridge = vsxml_info.set_vbridge(server)

# Get a bridge name that is not used by any of the virtual network pool on the machine. 
    bridge_name = get_unique_bridge()

# Assigning the bridge that does not belong to any networkpool.
    vsxml_info.set_bridge_name(bridge_name)
    ret = vsxml_info.define(server)
    if not ret:
        Globals.logger.error("Failed to define the dom: %s", test_dom)
        return FAIL, vsxml_info

    return PASS, vsxml_info

def get_inst_from_list(vsxml, classname, rasd_list, filter_name, exp_val):
    status = PASS
    ret = FAIL
    inst = []

    for rec in rasd_list:
        record = rec[filter_name]
        if exp_val in record:
            inst.append(rec)
            ret = PASS

    if ret != PASS:
        logger.error("%s with %s was not returned" % (classname, exp_val))
        vsxml.undefine(server)
        status = FAIL

    return status, inst

def get_netrasd_instid(vsxml, classname):
    rasd_list = []
    status = PASS
    try:
        rasd_list = enumclass.enumerate_inst(server, classname, virt)
        if len(rasd_list) < 1:
            logger.error("%s returned %i instances, excepted atleast 1 instance", classname,
                                                                              len(rasd_list))
            status = FAIL
    except Exception, detail:
        logger.error(CIM_ERROR_ENUMERATE, classname)
        logger.error("Exception: %s", detail)
        status = FAIL
    
    if status != PASS:
        return status, rasd_list

    # Get the RASD info related to the domain "ONLY". 
    # We should get ONLY one record.
    rasd_info = []
    status, rasd_info = get_inst_from_list(vsxml, classname, rasd_list, "InstanceID", test_dom)

    return status, rasd_info

def verify_rapf_err(vsxml):
    status = PASS
    try:

        classname  = get_typed_class(virt, 'NetResourceAllocationSettingData')
        status, net_rasd_list = get_netrasd_instid(vsxml, classname)
        if status != PASS or len(net_rasd_list) == 0:
            return status 
        if len(net_rasd_list) != 1:
            logger.error("%s returned %i instances, excepted atleast 1 instance", classname,
                                                                          len(net_rasd_list))
            return FAIL

    
        conn = assoc.myWBEMConnection('http://%s' % server, 
                                         (Globals.CIM_USER, 
                                         Globals.CIM_PASS), 
                                            Globals.CIM_NS)
        assoc_classname = get_typed_class(virt, "ResourceAllocationFromPool")
        classname = net_rasd_list[0].classname 
        instid    = net_rasd_list[0]['InstanceID']
        keys = { "InstanceID" : instid }
        expr_values = { 
                        'rapf_err' : {
                                       'desc' : "Unable to determine pool of `%s'" %instid, 
                                         'rc' : pywbem.CIM_ERR_FAILED
                                     }
                      } 
        status = try_assoc(conn, classname, assoc_classname, keys, field_name="InstanceID", 
                                            expr_values=expr_values['rapf_err'], bug_no="")

    except Exception, detail:
        logger.error("Exception: %s", detail)
        status = FAIL

    return status 

@do_main(platform_sup)
def main():
    global virt, server 
    Globals.log_param()
    options = main.options
    server = options.ip
    virt = options.virt
    destroy_and_undefine_all(server)

    status, vsxml = setup_env()
    if status != PASS:
        logger.error("Failed to setup the domain")
        return status

    ret = verify_rapf_err(vsxml)
    if ret: 
        logger.error("------FAILED: to verify the RAFP.------")
        status = ret

    vsxml.undefine(server)
    return status
if __name__ == "__main__":
    sys.exit(main())
