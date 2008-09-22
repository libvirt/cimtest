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
from XenKvmLib.const import do_main
from XenKvmLib import vxml
from XenKvmLib.classes import get_typed_class
from XenKvmLib.const import default_network_name
from XenKvmLib.common_util import create_netpool_conf, destroy_netpool

test_dom   = "RAPF_domain"
test_mac   = "00:11:22:33:44:aa"
test_vcpus = 1
npool_name = default_network_name + str(random.randint(1, 100))
sup_types = ['KVM', 'Xen', 'XenFV']

def setup_env(server, virt, net_name, nettype='network'):
    vsxml_info = None
    if virt == "Xen":
        test_disk = "xvda"
    else:    
        test_disk = "hda"

    virt_xml =  vxml.get_class(virt)
    vsxml_info = virt_xml(test_dom, vcpus = test_vcpus, 
                          mac = test_mac, disk = test_disk, 
                          ntype = nettype, net_name=net_name)

    ret = vsxml_info.cim_define(server)
    if not ret:
        logger.error("Failed to define the dom '%s' for '%s' type"
                      " interface", test_dom, nettype)
        if virt != 'KVM':
            status = destroy_netpool(server, virt, net_name)
            if status != PASS:
                logger.error("Failed to destroy the networkpool %s", net_name)
        return FAIL, vsxml_info

    return PASS, vsxml_info

def get_inst_from_list(server, vsxml, classname, rasd_list, filter_name, 
                       exp_val):
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

def get_netrasd_instid(server, virt, vsxml, classname):
    rasd_list = []
    status = PASS
    try:
        rasd_list = enumclass.enumerate_inst(server, classname, virt)
        if len(rasd_list) < 1:
            logger.error("%s returned %i instances, excepted atleast 1 "
                         "instance", classname, len(rasd_list))
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
    status, rasd_info = get_inst_from_list(server, vsxml, classname, 
                                           rasd_list, "InstanceID", test_dom)

    return status, rasd_info

def verify_rapf_err(server, virt, vsxml):
    status = PASS
    try:

        classname  = get_typed_class(virt, 'NetResourceAllocationSettingData')
        status, net_rasd_list = get_netrasd_instid(server, virt, vsxml, classname)
        if status != PASS or len(net_rasd_list) == 0:
            return status 
        if len(net_rasd_list) != 1:
            logger.error("%s returned %i instances, excepted atleast 1 "
                         "instance", classname, len(net_rasd_list))
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
                                       'desc' : "Unable to determine pool of " \
                                                 "`%s'" %instid, 
                                         'rc' : pywbem.CIM_ERR_FAILED
                                     }
                      } 
        status = try_assoc(conn, classname, assoc_classname, keys,
                           field_name="InstanceID", 
                           expr_values=expr_values['rapf_err'], bug_no="")

    except Exception, detail:
        logger.error("Exception: %s", detail)
        status = FAIL

    return status 

@do_main(sup_types)
def main():
    options = main.options
    server = options.ip
    virt = options.virt
    destroy_and_undefine_all(server)
    in_list =  'network' 

    # libvirt does not allow to define a guest with invalid networkpool info
    # for Xen and XenFV, but it does not restrict to do so for KVM.
    # Hence passing wrong networkpool for KVM and a valid networkpool for 
    # Xen and XenFV otherwise.
    if virt == 'KVM':
        int_name = 'wrong-int'
    else:
        status, int_name = create_netpool_conf(options.ip, options.virt,
                                               use_existing=False,
                                               net_name=npool_name)
        if status != PASS:
            logger.error('Unable to create network pool')
            return FAIL


    # Since we cannot create a Xen/XenFV guest with invalid networkpool info,
    # we first create a guest with valid networkpool info and then 
    # then destroy the networkpool info as a work around to, verify if the 
    # provider returns an exception for Xen/XenFV guest when its networkpool 
    # does not exist anymore on the machine.
    status, vsxml = setup_env(server, virt, int_name, in_list)
    if status != PASS:
        logger.error("Failed to setup the domain")
        vsxml.undefine(server)
        return status

    if virt != 'KVM':
        status = destroy_netpool(server, virt, int_name)
        if status != PASS:
            logger.error("Failed to destroy the virtual network %s", net_name)
            vsxml.undefine(server)
            return status

    status = verify_rapf_err(server, virt, vsxml)
    if status != PASS: 
        logger.error("------FAILED: to verify the RAFP.------")

    vsxml.undefine(server)
    return status
if __name__ == "__main__":
    sys.exit(main())
