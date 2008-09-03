#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Deepti B. Kalakeri <dkalaker@in.ibm.com>
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
# Test Case Info:
# --------------
# This test case is used to verify the ResourceAllocationSettingData
# returns appropriate exceptions when invalid values are passed.
#
# 1) Test by passing Invalid InstanceID Key Name
# Input:
# ------
# wbemcli gi 'http://localhost:5988/root/virt:Xen_MemResourceAllocationSettingData.\
# Wrong="virt1/mem"' - 
#
# Output:
# -------
# error code  : CIM_ERR_FAILED 
# error desc  : "Missing InstanceID"
#
# 2) Test by giving invalid Invalid InstanceID Key Value
# Input:
# ------
# wbemcli gi 'http://localhost:5988/root/virt:Xen_MemResourceAllocationSettingData.\
# InstanceID="Wrong"' 
#
# Output:
# -------
# error code  : CIM_ERR_NOT_FOUND 
# error desc  : "No such instance"
#                                               
#  
#
#                                                                  Date : 26-03-2008
#


import sys
import pywbem
from XenKvmLib import assoc
from XenKvmLib.common_util import try_getinstance
from XenKvmLib.const import do_main
from XenKvmLib.test_doms import destroy_and_undefine_all
from XenKvmLib.vxml import get_class
from XenKvmLib.classes import get_typed_class
from CimTest.Globals import logger, CIM_USER, CIM_PASS, CIM_NS, CIM_ERROR_GETINSTANCE
from CimTest.ReturnCodes import PASS, FAIL
from XenKvmLib.const import default_network_name 

sup_types = ['Xen', 'KVM', 'XenFV', 'LXC']

test_dom    = "VSSDC_dom"
test_vcpus  = 1
test_mem    = 128
test_mac    = "00:11:22:33:44:aa"

expr_values = {
                'INVALID_Instid_KeyName'  : { 
                                                'rc'   : pywbem.CIM_ERR_FAILED, \
                                                'desc' : 'Missing InstanceID' 
                                             }, \
                'INVALID_Instid_KeyValue'  : { 
                                                'rc'   : pywbem.CIM_ERR_NOT_FOUND, \
                                                'desc' : 'No such instance' 
                                             }
              }

def init_list(virt="Xen"):
    disk = {
             'cn'     : get_typed_class(virt, "DiskResourceAllocationSettingData"), \
             'instid' : '%s/%s' %(test_dom, test_disk)
           }
    mem  = {
             'cn'     : get_typed_class(virt, "MemResourceAllocationSettingData"), \
             'instid' : '%s/%s' %(test_dom, "mem"), 
           }
    proc = {
             'cn'     : get_typed_class(virt, "ProcResourceAllocationSettingData"), \
             'instid' : '%s/%s' %(test_dom,0)
           } 
         
    net = {
             'cn'     : get_typed_class(virt, "NetResourceAllocationSettingData"), \
             'instid' : '%s/%s' %(test_dom,test_mac)
          }    
    
    if virt == 'LXC':
        rasd_values_list =[ mem ]
    else:
        rasd_values_list =[ disk, mem, proc, net ]
    return rasd_values_list

def verify_rasd_err(field, keys, rasd_type):
    status = PASS
    try:
        ret_value = try_getinstance(conn, rasd_type['cn'], keys, field_name=field, \
                                          expr_values=expr_values[field], bug_no="")
        if ret_value != PASS:
            logger.error("------ FAILED: to verify %s.------", field)
            status = ret_value
    except Exception, detail:
        logger.error(CIM_ERROR_GETINSTANCE, rasd_type['cn'])
        logger.error("Exception: %s", detail)
        status = FAIL
    return status

@do_main(sup_types)
def main():
    options = main.options
    global test_disk, vsxml 
    global virt, server, conn
    destroy_and_undefine_all(options.ip)
    server = options.ip 
    virt = options.virt

    if virt == "Xen":
        test_disk = "xvda"
    else:
        test_disk = "hda"
    if options.virt == 'LXC':
        vsxml = get_class(virt)(test_dom)
    else:
        vsxml = get_class(virt)(test_dom, \
                                mem=test_mem, \
                                vcpus = test_vcpus, \
                                mac = test_mac, \
                                disk = test_disk)
        bridge = vsxml.set_vbridge(server, default_network_name)
    try:
        ret = vsxml.define(options.ip)
        if not ret:
            logger.error("Failed to Define the domain: %s", test_dom)
            return FAIL 
    except Exception, details:
        logger.error("Exception : %s", details)
        return FAIL

    conn = assoc.myWBEMConnection('http://%s' % options.ip, (CIM_USER, CIM_PASS), CIM_NS)

    rasd_list = init_list()
    
    # Each Loop checks one of the RASD types [ Disk, Mem, Net, Proc ]
    for rasd_type in sorted(rasd_list):
        # Test RASD by passing Invalid InstanceID Key Name
        field = 'INVALID_Instid_KeyName'
        keys = { field : rasd_type['instid'] }
        status = verify_rasd_err(field, keys, rasd_type)
        if status != PASS:
            break

        # Test RASD by passing Invalid InstanceID Key Value
        field = 'INVALID_Instid_KeyValue'
        keys = { 'InstanceID' : field }
        status = verify_rasd_err(field, keys, rasd_type)
        if status != PASS:
            break
    try: 
        vsxml.undefine(server)
    except Exception, detail:
        logger.error("Failed to undefine domain %s", test_dom)
        logger.error("Exception: %s", detail)
    return status 

if __name__ == "__main__":
    sys.exit(main())
