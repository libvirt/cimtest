#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Deepti B. Kalakeri <dkalaker@in.ibm.com>
#    Guolian Yun <yunguol@cn.ibm.com>
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

# This tc is used to verify if appropriate exceptions are 
# returned by Xen_ElementAllocatedFromPool asscoiation 
# on giving invalid inputs.
#
#                                                Date : 30-12-2007

import sys
import pywbem
from XenKvmLib import assoc
from CimTest import Globals
from XenKvmLib.test_doms import destroy_and_undefine_all
from XenKvmLib.common_util import try_assoc
from XenKvmLib.const import CIM_REV
from CimTest.ReturnCodes import PASS, FAIL	
from CimTest.Globals import do_main, platform_sup, logger
from XenKvmLib.vxml import get_class
from XenKvmLib.classes import get_typed_class
from XenKvmLib.common_util import cleanup_restore, test_dpath, \
create_diskpool_file

bug_no     = "88651"
test_dom   = "hd_domain"
test_mac   = "00:11:22:33:44:aa"
test_vcpus = 1 
id1        = "DiskPool/%s" %test_dpath
id2        = "MemoryPool/0"
id3        = "NetworkPool/xenbr0"
id4        = "ProcessorPool/0"
expr_values = {
                 "invalid_keyname" : {
                                        'rc'    : pywbem.CIM_ERR_FAILED, 
                                        'desc'  : 'Missing InstanceID'
                                     }, 
                 "invalid_keyvalue" : {
                                        'rc'    : pywbem.CIM_ERR_NOT_FOUND, 
                                        'desc'  : 'No such instance'
                                    } 
              }
libvirt_rev = 393

def err_invalid_ccname():
# This is used to verify the that the  
# Xen_ElementAllocatedFromPool asscoiation returns error when 
# mismatching values are passed as part of 
# CreationClassName and InstanceID.
#
# Example command for DiskPool w.r.t to Xen_ElementAllocatedFromPool \
# asscoiation :
# wbemcli ain -ac Xen_ElementAllocatedFromPool \
# 'http://localhost:5988/root/virt:Xen_DiskPool.InstanceID="MemoryPool/0"'
# 
# Output:
# wbemcli: Cim: (6) CIM_ERR_NOT_FOUND: The requested object could not be found:
# "No such ResourcePool instance (CreationClassName)"
# 
# Similarly we check for Memory,Network,Processor.

    global id2, id4
    lelist = {
              get_typed_class(virt, "DiskPool")        : id2, \
              get_typed_class(virt, "MemoryPool")      : id4, \
              get_typed_class(virt, "NetworkPool")     : id4, \
              get_typed_class(virt, "ProcessorPool")   : id2
             }

    for classname, instdid in sorted(lelist.items()):
        keys  = { "InstanceID" : instdid}
        field = "InvalidClassName"
        status = try_assoc(conn, classname, assoc_classname, keys, field_name=field, 
                           expr_values=expr_values['invalid_keyvalue'],bug_no=bug_no)
        if status != PASS:
            break
    return status

def err_invalid_keyname():
# This is used to verify the that the  
# Xen_ElementAllocatedFromPool asscoiation returns error when 
# invalid keyname is passed .
#
# Example command for Memory w.r.t to Xen_ElementAllocatedFromPool \
# asscoiation :
# wbemcli ain -ac Xen_ElementAllocatedFromPool \
# 'http://localhost:5988/root/virt:Xen_MemoryPool.InvalidID="MemoryPool/0"'
# 
# Output:
# wbemcli: Cim: (1) CIM_ERR_FAILED: A general error occurred that is not \
# covered by a more specific error code: "Missing InstanceID"
# 
# Similarly we check for LogicalDisk,Network,Processor.
#

    global id1, id2, id3, id4
    lelist = {
              get_typed_class(virt, "DiskPool")        : id1, \
              get_typed_class(virt, "MemoryPool")      : id2, \
              get_typed_class(virt, "NetworkPool")     : id3, \
              get_typed_class(virt, "ProcessorPool")   : id4
             }

    for classname, instdid in sorted(lelist.items()):
        keys = { "InvalidID" : instdid }
        field = "InstanceID_KeyName"    
        status = try_assoc(conn, classname, assoc_classname, keys, field_name=field, 
                           expr_values=expr_values['invalid_keyname'], bug_no="")
        if status != PASS:
            break
    return status


def err_invalid_keyvalue():
# This is used to verify the that the  
# Xen_ElementAllocatedFromPool asscoiation returns error when 
# invalid keyvalue is passed .
#
# Example command for Memory w.r.t to Xen_ElementAllocatedFromPool \
# asscoiation :
# wbemcli ai -ac Xen_ElementAllocatedFromPool \
# 'http://localhost:5988/root/virt:\
# Xen_MemoryPool.InstanceID="InvalidValue"' 
# 
# Output:
# wbemcli: Cim: (1) CIM_ERR_FAILED: A general error occurred that \
# is not covered by a more specific error code: \
# "Invalid InstanceID or unsupported pool type"
# 
# Similarly we check for LogicalDisk,Network,Processor.

    status = PASS 
    lelist = [
              get_typed_class(virt, "DiskPool")       , \
              get_typed_class(virt, "MemoryPool")     , \
              get_typed_class(virt, "NetworkPool")    , \
              get_typed_class(virt, "ProcessorPool")
             ]

    if CIM_REV < libvirt_rev:
        expr_values['invalid_keyvalue']['desc'] = 'Invalid InstanceID or unsupported pool type'
        expr_values['invalid_keyvalue']['rc'] = pywbem.CIM_ERR_FAILED

    for classname in sorted(lelist):
        keys = { "InstanceID" : "InvalidKeyValue" }
        field = "InstanceID_KeyValue"    
        status = try_assoc(conn, classname, assoc_classname, keys, field_name=field, 
                           expr_values=expr_values['invalid_keyvalue'], bug_no="")
        if status != PASS:
            break
    return status

def clean_and_exit(server, virt, msg):
    logger.error("------FAILED: Invalid %s.------", msg)
    cleanup_restore(server, virt)
    vsxml.undefine(server)

@do_main(platform_sup)
def main():
    global virt
    global conn
    global assoc_classname
    global vsxml
    status = PASS
    options = main.options
    destroy_and_undefine_all(options.ip)
    virt = options.virt
    if virt == "Xen":
        test_disk = "xvda"
    else:
        test_disk = "hda"
    virt_type = get_class(virt)
    vsxml = virt_type (test_dom, vcpus = test_vcpus, mac = test_mac, 
                       disk = test_disk)

    # Verify DiskPool on machine
    status = create_diskpool_file()
    if status != PASS:
        return status
    ret = vsxml.define(options.ip)
    if not ret:
        logger.error("Failed to define the dom: %s", test_dom)
        return FAIL
    conn = assoc.myWBEMConnection('http://%s' % options.ip,
                                 (Globals.CIM_USER, Globals.CIM_PASS),
                                 Globals.CIM_NS)
    assoc_classname = get_typed_class(virt, "ElementAllocatedFromPool")
    ret = err_invalid_keyname()
    if ret != PASS: 
        clean_and_exit(options.ip, virt, "KeyName")
        return ret

    ret = err_invalid_keyvalue()
    if ret != PASS: 
        clean_and_exit(options.ip, virt, "KeyValue")
        return ret

    ret = err_invalid_ccname()
    if ret != PASS: 
        clean_and_exit(options.ip, virt, "CCName")
        return ret

    cleanup_restore(options.ip, virt)
    vsxml.undefine(options.ip)
    return PASS
if __name__ == "__main__":
    sys.exit(main())
