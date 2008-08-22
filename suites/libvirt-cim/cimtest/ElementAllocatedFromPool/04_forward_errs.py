#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Deepti B. Kalakeri <dkalaker@in.ibm.com>
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

# This tc is used to verify the that the
# Xen_ElementAllocatedFromPool asscoiation returns error
# when invalid values are passed.
#
#                                                Date : 28-12-2007
#

import sys
import pywbem
from pywbem.cim_obj import CIMInstanceName
from XenKvmLib import assoc
from XenKvmLib.test_doms import destroy_and_undefine_all
from CimTest import Globals
from CimTest.Globals import logger
from CimTest.ReturnCodes import PASS, FAIL, XFAIL_RC
from CimTest.Globals import do_main, platform_sup
from XenKvmLib.vxml import get_class
from XenKvmLib.classes import get_typed_class
from XenKvmLib.common_util import cleanup_restore, test_dpath, \
create_diskpool_file
from XenKvmLib.const import default_network_name 

sup_types = ['Xen', 'KVM', 'XenFV']
bug_no             = "88651"
test_dom           = "hd_domain"
test_dom_invalid   = "Invalid"
test_mac   = "00:11:22:33:44:aa"
test_vcpus = 1
exp_list = [
             {'desc' : "No such instance (SystemName)", 'rc' : pywbem.CIM_ERR_NOT_FOUND}, 
             {'desc' : "No DeviceID specified", 'rc' : pywbem.CIM_ERR_FAILED}, 
             {'desc' : "No such instance", 'rc' : pywbem.CIM_ERR_NOT_FOUND}, 
             {'desc' : "CIM_ERR_INVALID_PARAMETER", 
                'rc' : pywbem.CIM_ERR_INVALID_PARAMETER}, 
             {'desc' : "No such instance (CreationClassName)",
                'rc' : pywbem.CIM_ERR_NOT_FOUND }, 
             {'desc' : "No such instance (SystemCreationClassName)", 
                'rc' :  pywbem.CIM_ERR_NOT_FOUND },  
            ]

def try_assoc(conn, exp_ret, dev_dom_name, invalid_keyname_list, test_vals, log_msg):

    status = PASS
    diskid = "%s/%s" % (dev_dom_name, test_disk)
    memid = "%s/mem" % dev_dom_name
    netid = "%s/%s" % (dev_dom_name, test_mac)
    procid = "%s/%s" % (dev_dom_name, 0)
    
    lelist = {
                  get_typed_class(virt, "LogicalDisk") : diskid, 
                  get_typed_class(virt, "NetworkPort") : netid, 
                  get_typed_class(virt, "Memory"     ) : memid, 
                  get_typed_class(virt, "Processor"  ) : procid
             }

    if invalid_keyname_list['DeviceID'] != "valid":
        devkeyname = "InvalidDeviceID"
    else:
        devkeyname = "DeviceID"
    if invalid_keyname_list['CreationClassName'] != "valid":
        ccnkeyname = "InvalidCreationClassName"
    else:
        ccnkeyname = "CreationClassName"
    if invalid_keyname_list['SystemCreationClassName'] != "valid":
        sccnkeyname = "InvalidSystemCreationClassName"
    else:
        sccnkeyname = "SystemCreationClassName"
    if invalid_keyname_list['SystemName'] != "valid" :
        snkeyname = "InvalidSystemName"
    else:
        snkeyname = "SystemName"
 
    test_keys = { devkeyname  : devkeyname, 
                  ccnkeyname  : ccnkeyname, 
                  sccnkeyname : sccnkeyname, 
                  snkeyname   : snkeyname 
                }
    for cn, devid in sorted(lelist.items()):
        assoc_info = []
        if test_vals['devid'] != "valid":
            dev_id = "InvalidDevID"
        else:
            dev_id = devid

        if test_vals['ccn'] != "valid":
            ccn = "InvalidCreationClassName"
        else:
            ccn = cn

        keys = { test_keys[devkeyname]  : dev_id, 
                 test_keys[ccnkeyname]  : ccn, 
                 test_keys[sccnkeyname] : test_vals['sccn'], 
                 test_keys[snkeyname]   : test_vals['sn'] 
               }
        if test_vals['cn'] != "valid":
            inst_cn = "InvalidClassName"
        else:
            inst_cn = cn
        instanceref = CIMInstanceName(inst_cn, keybindings=keys)
        try:
            assoc_info = conn.AssociatorNames(instanceref, 
                                              AssocClass=assoc_classname)
        except pywbem.CIMError, (err_no, desc):
            if err_no == exp_ret['rc'] and desc.find(exp_ret['desc']) >= 0:
                logger.info("Got expected exception where ")
                logger.info("Errno is '%s' ", exp_ret['rc'])
                logger.info("Error string is '%s'", exp_ret['desc'])
            else:
                logger.error("Unexpected rc code %s and description \
%s\n" %(err_no, desc))
                status = FAIL
        if len(assoc_info) != 0:
            logger.error("%s association \
should NOT have returned records. '%s'", assoc_classname, log_msg)
            status = XFAIL_RC(bug_no)
        if status != PASS:
            break
    return status

def err_invalid_sysname_keyname(conn, exp_ret):

# This is used to verify the that the  
# Xen_ElementAllocatedFromPool asscoiation returns error when 
# Non-existing SystemName is passed. 
#
# Example command for LogicalDisk w.r.t to Xen_ElementAllocatedFromPool \
# asscoiation :
# wbemcli ai -ac Xen_ElementAllocatedFromPool \
# 'http://localhost:5988/root/virt:\
# Xen_LogicalDisk.CreationClassName="Xen_LogicalDisk",\
# SystemName="Non-existing",DeviceID="Domain/xvda",SystemCreationClassName="Xen_ComputerSystem"'
# 
# Output:
#
# wbemcli: Cim: (6) CIM_ERR_NOT_FOUND: The requested object could not be found: \
# "No such instance (SystemName)"
#
# 
# Similarly we check for Memory,Network,Processor.
# 
#
# 
    test_keys = { 'DeviceID' : "valid", 
                   'CreationClassName' : "valid", 
                   'SystemCreationClassName' : "valid", 
                   'SystemName' : "invalid" 
                 } 
    test_vals = { 'devid' : "valid", 
                   'sccn' : get_typed_class(virt, "ComputerSystem"), 
                   'sn' : test_dom, 
                   'ccn' : "valid", 
                   'cn' : "valid"
                 }

    log_msg = "Invalid SystemName Key Name was supplied."

    return try_assoc(conn, exp_ret, test_dom, test_keys, test_vals, log_msg)

def err_invalid_sysname_keyvalue(conn, exp_ret):

# This is used to verify the that the  
# Xen_ElementAllocatedFromPool asscoiation returns error when 
# Non-existing SystemName is passed. 
#
# Example command for LogicalDisk w.r.t to Xen_ElementAllocatedFromPool \
# asscoiation :
# wbemcli ai -ac Xen_ElementAllocatedFromPool \
# 'http://localhost:5988/root/virt:\
# Xen_LogicalDisk.CreationClassName="Xen_LogicalDisk",\
# SystemName="Non-existing",DeviceID="Domain/xvda",SystemCreationClassName="Xen_ComputerSystem"'
# 
# Output:
# wbemcli: Cim: (6) CIM_ERR_NOT_FOUND: The requested object could not be found: \
# "No such instance (SystemName)"
#
# Similarly we check for Memory,Network,Processor.
# 
    test_keys = { 'DeviceID' : "valid", 
                   'CreationClassName' : "valid", 
                   'SystemCreationClassName' : "valid", 
                   'SystemName' : "valid" 
                 } 
    test_vals = { 'devid' : "valid", 
                   'sccn' : get_typed_class(virt, "ComputerSystem"), 
                   'sn' : "invalid", 
                   'ccn' : "valid", 
                   'cn' : "valid"
                 }

    log_msg = "Non-existing SystemName was supplied."

    return try_assoc(conn, exp_ret, test_dom, test_keys, test_vals, log_msg)

def err_invalid_devid_keyname(conn, exp_ret):
# This is used to verify the that the
# Xen_ElementAllocatedFromPool asscoiation returns error when
# Invalid DeviceId is passed.
#
# Example command for LogicalDisk w.r.t to Xen_ElementAllocatedFromPool \
# asscoiation :
# wbemcli ai -ac Xen_ElementAllocatedFromPool \
# 'http://localhost/root/virt:\
# Xen_LogicalDisk.CreationClassName="Xen_LogicalDisk",\
#SystemName="hd_domain",InvalidID="hd_domain/xvda",SystemCreationClassName="Xen_ComputerSystem"'
#
#
# Output:
#
# wbemcli: Cim: (1) CIM_ERR_FAILED: A general error occurred that is not covered \
# by a more specific error code: "No Such Instance"
#
# Similarly we check for Network,Memory,processor.
#
#

    test_keys = { 'DeviceID' : "invalid", 
                   'CreationClassName' : "valid", 
                   'SystemCreationClassName' : "valid", 
                   'SystemName' : "valid" 
                 } 
    test_vals = { 'devid' : "valid", 
                   'sccn' : get_typed_class(virt, "ComputerSystem"), 
                   'sn' : test_dom, 
                   'ccn' : "valid",
                   'cn' : "valid"
                 }

    log_msg = "Invalid deviceid keyname was supplied."

    return try_assoc(conn, exp_ret, test_dom, test_keys, test_vals, log_msg)

def err_invalid_devid_keyvalue(conn, exp_ret):

# This is used to verify the that the  
# Xen_ElementAllocatedFromPool asscoiation returns error when 
# Invalid DeviceId is passed. 
#
# Example command for LogicalDisk w.r.t to Xen_ElementAllocatedFromPool \
# asscoiation :
# wbemcli ai -ac Xen_ElementAllocatedFromPool \
# 'http://localhost/root/virt:\
# Xen_LogicalDisk.CreationClassName="Xen_LogicalDisk",\
# SystemName="hd_domain",DeviceID="Invalid/xvda",SystemCreationClassName="Xen_ComputerSystem"'
# 
# Output:
#
# wbemcli: Cim: (1) CIM_ERR_FAILED: A general error occurred that is not \
# covered by a more specific error code: "No DeviceID specified"
# 
# Similarly we check for Network.
# 
# 
    test_keys = { 'DeviceID' : "valid", 
                   'CreationClassName' : "valid", 
                   'SystemCreationClassName' : "valid", 
                   'SystemName' : "valid" 
                 } 
    test_vals = { 'devid' : "invalid", 
                   'sccn' : get_typed_class(virt, "ComputerSystem"), 
                   'sn' : test_dom, 
                   'ccn' : "valid",
                   'cn' : "valid"
                 }

    log_msg = "Invalid deviceid keyvalue was supplied."

    return try_assoc(conn, exp_ret, test_dom_invalid, test_keys, test_vals, 
                     log_msg)

def err_invalid_classname(conn, exp_ret):

# This is used to verify the that the  
# Xen_ElementAllocatedFromPool asscoiation returns error when 
# Invalid classname is passed. 
#
# Example command for LogicalDisk w.r.t to Xen_ElementAllocatedFromPool \
# asscoiation :
# wbemcli ai -ac Xen_ElementAllocatedFromPool \
# 'http://localhost/root/virt:InvalidClass.CreationClassName="Xen_LogicalDisk",\
# SystemName="hd_domain",DeviceID="hd_domain/xvda",SystemCreationClassName="Xen_ComputerSystem"' 
# 
# 
# Output:
#
# wbemcli: Cim: (4) CIM_ERR_INVALID_PARAMETER: One or more parameter values passed to \
# the method were invalid: "InValidClass.CreationClassName="Xen_LogicalDisk",\
# DeviceID="hd_domain/xvda",SystemCreationClassName="",SystemName="hd_domain""
# 
# Similarly we check for Memory,Network,Processor.
# 
# 
    test_keys = { 'DeviceID' : "valid", 
                   'CreationClassName' : "valid", 
                   'SystemCreationClassName' : "valid", 
                   'SystemName' : "valid" 
                 } 
    test_vals = { 'devid' : "valid", 
                   'sccn' : get_typed_class(virt, "ComputerSystem"), 
                   'sn' : test_dom, 
                   'ccn' : "valid", 
                   'cn' : "invalid"
                 }

    log_msg = "Invalid classname value was supplied."

    return try_assoc(conn, exp_ret, test_dom, test_keys, test_vals, log_msg)

def err_invalid_creationclassname_keyname(conn, exp_ret):

# This is used to verify the that the  
# Xen_ElementAllocatedFromPool asscoiation returns error when 
# Invalid classname is passed. 
#
# Example command for LogicalDisk w.r.t to Xen_ElementAllocatedFromPool \
# asscoiation :
# wbemcli ai -ac Xen_ElementAllocatedFromPool \
# 'http://localhost/root/virt:Xen_LogicalDisk.InvalidCCN="Xen_LogicalDisk",\
# SystemName="hd_domain",DeviceID="hd_domain/xvda",SystemCreationClassName="Xen_ComputerSystem"' 
# 
# 
# Output:
# 
# wbemcli: Cim: (6) CIM_ERR_NOT_FOUND: The requested object could not be found: \
# "No such instance (CreationClassName)"
#
#
# 
# Similarly we check for Memory,Network,Processor.
# 

    test_keys = { 'DeviceID' : "valid", 
                   'CreationClassName' : "invalid", 
                   'SystemCreationClassName' : "valid", 
                   'SystemName' : "valid" 
                 } 
    test_vals = { 'devid' : "valid", 
                   'sccn' : get_typed_class(virt, "ComputerSystem"), 
                   'sn' : test_dom, 
                   'ccn' : "valid", 
                   'cn' : "valid"
                 }

    log_msg = "Invalid creationclassname keyname was supplied."

    return try_assoc(conn, exp_ret, test_dom, test_keys, test_vals, log_msg)

def err_invalid_creationclassname_keyvalue(conn, exp_ret):

# This is used to verify the that the  
# Xen_ElementAllocatedFromPool asscoiation returns error when 
# Invalid classname is passed. 
#
# Example command for LogicalDisk w.r.t to Xen_ElementAllocatedFromPool \
# asscoiation :
# wbemcli ai -ac Xen_ElementAllocatedFromPool \
# 'http://localhost/root/virt:Xen_LogicalDisk.CreationClassName="InvalidCreationClassName",\
# SystemName="hd_domain",DeviceID="hd_domain/xvda",SystemCreationClassName="Xen_ComputerSystem"' 
# 
# 
# Output:
#
# wbemcli: Cim: (6) CIM_ERR_NOT_FOUND: The requested object could not be found: \
# "No such instance (CreationClassName)"
# 
# Similarly we check for Memory,Network,Processor.
# 

    test_keys = { 'DeviceID' : "valid", 
                   'CreationClassName' : "valid", 
                   'SystemCreationClassName' : "valid", 
                   'SystemName' : "valid" 
                 } 
    test_vals = { 'devid' : "valid", 
                   'sccn' : get_typed_class(virt, "ComputerSystem"), 
                   'sn' : test_dom, 
                   'ccn' : "invalid", 
                   'cn' : "valid"
                 }

    log_msg = "Invalid creatioclassname keyvalue was supplied."

    return try_assoc(conn, exp_ret, test_dom, test_keys, test_vals, log_msg)

def err_invalid_syscreationclassname_keyname(conn, exp_ret):

# This is used to verify the that the  
# Xen_ElementAllocatedFromPool asscoiation returns error when 
# Invalid system creation classname is passed. 
#
# Example command for LogicalDisk w.r.t to Xen_ElementAllocatedFromPool \
# asscoiation :
#
# wbemcli ain -ac Xen_ElementAllocatedFromPool 'http://root:vsm4you@localhost:5988/root/virt:\
# Xen_NetworkPort.CreationClassName="Xen_NetworkPort",SystemName="hd_domain",
# DeviceID="hd_domain/00:11:22:33:44:aa",InvalidSystemCreationClassName="Xen_ComputerSystem"'
# 
# Output:

# wbemcli: Cim: (6) CIM_ERR_NOT_FOUND: The requested object could not be found: 
# "No such instance (SystemCreationClassName)"
#
# Similarly we check for Memory,Network,Processor.
# 

    test_keys = { 'DeviceID' : "valid", 
                   'CreationClassName' : "valid", 
                   'SystemCreationClassName' : "invalid", 
                   'SystemName' : "valid" 
                 } 
    test_vals = { 'devid' : "valid", 
                   'sccn' : get_typed_class(virt, "ComputerSystem"), 
                   'sn' : test_dom, 
                   'ccn' : "valid", 
                   'cn' : "valid"
                 }

    log_msg = "Invalid system creatioclassname keyvalue was supplied."

    return try_assoc(conn, exp_ret, test_dom, test_keys, test_vals, log_msg)

def err_invalid_syscreationclassname_keyvalue(conn, exp_ret):

# This is used to verify the that the  
# Xen_ElementAllocatedFromPool asscoiation returns error when 
# Invalid system creation classname is passed. 
#
# Example command for LogicalDisk w.r.t to Xen_ElementAllocatedFromPool \
# asscoiation :
#
# wbemcli ain -ac Xen_ElementAllocatedFromPool 'http://root:vsm4you@localhost:5988/root/virt:\
# Xen_NetworkPort.CreationClassName="Xen_NetworkPort",SystemName="hd_domain",
# DeviceID="hd_domain/00:11:22:33:44:aa",SystemCreationClassName="Invalid"'
# 
# Output:

# wbemcli: Cim: (6) CIM_ERR_NOT_FOUND: The requested object could not be found: 
# "No such instance (SystemCreationClassName)"
#
# Similarly we check for Memory,Network,Processor.
# 

    test_keys = { 'DeviceID' : "valid", 
                   'CreationClassName' : "valid", 
                   'SystemCreationClassName' : "valid", 
                   'SystemName' : "valid" 
                 } 
    test_vals = { 'devid' : "valid", 
                   'sccn' : "invalid", 
                   'sn' : test_dom, 
                   'ccn' : "valid", 
                   'cn' : "valid"
                 }

    log_msg = "Invalid system creatioclassname keyvalue was supplied."

    return try_assoc(conn, exp_ret, test_dom, test_keys, test_vals, log_msg)

def clean_and_exit(server, virt,  msg):
    logger.error("------FAILED: Invalid %s.------", msg)
    cleanup_restore(server, virt)
    vsxml.undefine(server)

@do_main(platform_sup)
def main():
    global virt
    global conn
    global assoc_classname
    global test_disk
    global vsxml
    global server 
    status = PASS
    options = main.options
    destroy_and_undefine_all(options.ip)
    virt = options.virt
    server = options.ip
    if virt == "Xen":
        test_disk = "xvda"
    else:    
        test_disk = "hda"
    destroy_and_undefine_all(options.ip)
    vsxml = get_class(virt)(test_dom, vcpus = test_vcpus, mac = test_mac, \
                                                          disk = test_disk)
    # Verify DiskPool on machine
    status = create_diskpool_file()
    if status != PASS:
        return status

    bridge = vsxml.set_vbridge(options.ip, default_network_name)
    ret = vsxml.define(options.ip)
    if not ret:
        logger.error("Failed to define the dom: %s", test_dom)
        return FAIL
    conn = assoc.myWBEMConnection('http://%s' % options.ip,
                            (Globals.CIM_USER, Globals.CIM_PASS),
                                                  Globals.CIM_NS)
    assoc_classname = get_typed_class(virt, "ElementAllocatedFromPool")

    ret = err_invalid_sysname_keyname(conn, exp_list[0])
    if ret != PASS:
        clean_and_exit(options.ip, virt, "SystemName KeyName")
        return ret

    ret = err_invalid_sysname_keyvalue(conn, exp_list[0])
    if ret != PASS:
        clean_and_exit(options.ip, virt, "SystemName Key Value")
        return ret

    ret = err_invalid_devid_keyname(conn, exp_list[1])
    if ret != PASS:
        clean_and_exit(options.ip, virt, "DeviceID Keyname")
        return ret

    ret = err_invalid_devid_keyvalue(conn, exp_list[2])
    if ret != PASS:
        clean_and_exit(options.ip, virt, "DeviceID Keyvalue")
        return ret

    ret = err_invalid_classname(conn, exp_list[3])
    if ret != PASS:
        clean_and_exit(options.ip, virt, "classname Keyname")
        return ret

    ret = err_invalid_creationclassname_keyname(conn, exp_list[4])
    if ret != PASS:
        clean_and_exit(options.ip, virt, "creationclassname Keyname")
        return ret

    ret = err_invalid_creationclassname_keyvalue(conn, exp_list[4]) 
    if ret != PASS:
        clean_and_exit(options.ip, virt, "creationclassname Keyvalue")
        return ret

    ret = err_invalid_syscreationclassname_keyname(conn, exp_list[5]) 
    if ret != PASS:
        clean_and_exit(options.ip, virt, "System creationclassname Keyname")
        return ret

    ret = err_invalid_syscreationclassname_keyvalue(conn, exp_list[5]) 
    if ret != PASS:
        clean_and_exit(options.ip, virt, "System creationclassname Keyvalue")
        return ret

    cleanup_restore(options.ip, virt)
    vsxml.undefine(options.ip)
    return PASS
if __name__ == "__main__":
    sys.exit(main())
