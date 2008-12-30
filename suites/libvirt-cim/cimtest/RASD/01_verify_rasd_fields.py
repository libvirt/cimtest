#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Deepti B. Kalakeri <dkalaker@in.ibm.com>
#    Guolian Yun <yunguol@cn.ibm.com>
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

# This test case is used to verify the ResourceAllocationSettingData
# properties in detail using the Xen_VirtualSystemSettingDataComponent
# association.
#
# Ex: 
# Command:
# wbemcli ai -ac Xen_VirtualSystemSettingDataComponent \
# 'http://localhost:5988/root/virt:Xen_VirtualSystemSettingData.\
#  InstanceID="Xen:domgst"'
#
# Output:
# localhost:5988/root/virt:Xen_ProcResourceAllocationSettingData.\
# InstanceID="domgst/0" .....
# localhost:5988/root/virt:Xen_NetResourceAllocationSettingData\
# .InstanceID="domgst/00:22:33:aa:bb:cc" ....
# localhost:5988/root/virt:Xen_DiskResourceAllocationSettingData.\
# InstanceID="domgst/xvda".....
# localhost:5988/root/virt:Xen_MemResourceAllocationSettingData.\
# InstanceID="domgst/mem".....
# 
# 
# 
# 
#                                               Date : 08-01-2008


import sys
from XenKvmLib.const import do_main
from XenKvmLib.assoc import compare_all_prop, Associators
from XenKvmLib.vxml import get_class
from XenKvmLib.classes import get_typed_class
from CimTest.Globals import logger, CIM_ERROR_ASSOCIATORS
from CimTest.ReturnCodes import PASS, FAIL
from XenKvmLib.rasd import enum_rasds
from XenKvmLib.common_util import parse_instance_id

sup_types = ['Xen', 'KVM', 'XenFV', 'LXC']

test_dom    = "VSSDC_dom"
test_vcpus  = 1
test_mem    = 128
test_mac    = "00:11:22:33:44:aa"

def init_rasd_list(virt, ip):
    rasd_insts = {}
    rasds, status = enum_rasds(virt, ip)
    if status != PASS:
        logger.error("Enum RASDs failed")
        return rasd_insts, status

    for rasd_cn, rasd_list in rasds.iteritems():
        for rasd in rasd_list:
            guest, dev, status = parse_instance_id(rasd.InstanceID)
            if status != PASS:
                logger.error("Unable to parse InstanceID: %s" % rasd.InstanceID)
                return rasd_insts, FAIL

            if guest == test_dom:
                rasd_insts[rasd.Classname] = rasd

    return rasd_insts, PASS

def verify_rasd(virt, ip, assoc_info):
    rasds, status = init_rasd_list(virt, ip)
    if status != PASS:
        return status

    if len(assoc_info) != len(rasds):
        logger.error("%d assoc_info != %d RASD insts", 
                      len(assoc_info), len(rasds))
        return FAIL

    for rasd in assoc_info:
        guest, dev, status = parse_instance_id(rasd['InstanceID'])
        if status != PASS:
           logger.error("Unable to parse InstanceID: %s", rasd['InstanceID'])
           return status

        if guest != test_dom:
           logger.error("VSSDC should not have returned info for dom %s",
                         guest)
           return FAIL
       
        logger.info("Verifying: %s", rasd.classname)
        exp_rasd = rasds[rasd.classname]
        status = compare_all_prop(rasd, exp_rasd)
        if status != PASS: 
            return status

    return PASS

@do_main(sup_types)
def main():
    options = main.options
    virt = options.virt
    server = options.ip
    status = FAIL 

    virt_xml = get_class(virt)
    if virt == 'LXC':
        cxml = virt_xml(test_dom)
    else:
        cxml = virt_xml(test_dom, mem=test_mem, vcpus = test_vcpus,
                        mac = test_mac)
                        
    ret = cxml.cim_define(server)
    if not ret:
        logger.error('Unable to define the domain %s', test_dom)
        return FAIL 

    status = cxml.cim_start(server)
    if status != PASS:
        logger.error('Unable to start the domain %s', test_dom)
        cxml.undefine(server)
        return FAIL 

    if virt == "XenFV":
        instIdval = "Xen:%s" % test_dom
    else:
        instIdval = "%s:%s" % (virt, test_dom)

    vssdc_cn = get_typed_class(virt, 'VirtualSystemSettingDataComponent')
    vssd_cn = get_typed_class(virt, 'VirtualSystemSettingData')
    try:
        assoc_info = Associators(server, vssdc_cn, vssd_cn, 
                                 InstanceID = instIdval)
        status = verify_rasd(virt, server, assoc_info)
    except  Exception, details:
        logger.error(CIM_ERROR_ASSOCIATORS, vssdc_cn)
        logger.error("Exception : %s" % details)
        status = FAIL 

    cxml.destroy(server)
    cxml.undefine(server)
    return status
if __name__ == "__main__":
    sys.exit(main())
