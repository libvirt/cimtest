#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Deepti B. Kalakeri<dkalaker@in.ibm.com> 
#    
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
# This tc is used to verify if appropriate exceptions are 
# returned by Xen_AllocationCapabilities on giving invalid inputs.
#
# 1) Test by passing Invalid InstanceID Key Value
# Input:
# ------
# wbemcli gi http://localhost:5988/root/virt:\
# Xen_AllocationCapabilities.InstanceID="Wrong" -nl
# 
# Output:
# -------
# error code  : CIM_ERR_NOT_FOUND 
# error desc  : "Instance not found"
#
# 2) Test by giving invalid Invalid InstanceID Key Name
# Input:
# ------
# wbemcli gi http://localhost:5988/root/virt:\
# Xen_AllocationCapabilities.Wrong="ProcessorPool/0" -nl
#
# Output:
# -------
# error code  : CIM_ERR_FAILED 
# error desc  : "No InstanceID specified"
#                                                   -Date 21.02.2008

import sys
import os
import pywbem
from distutils.file_util import move_file
from XenKvmLib import assoc
from VirtLib import utils
from CimTest.Globals import logger, CIM_USER, CIM_PASS, CIM_NS
from CimTest.ReturnCodes import PASS, SKIP
from XenKvmLib.common_util import try_getinstance
from VirtLib.live import net_list
from XenKvmLib.test_xml import netxml
from XenKvmLib.test_doms import create_vnet
from CimTest.Globals import do_main, platform_sup
from XenKvmLib.classes import get_typed_class
from XenKvmLib.const import CIM_REV

test_dpath = "foo"
disk_file = '/tmp/diskpool.conf'
back_disk_file = disk_file + "." + "alloccap_err" 
diskid = "%s/%s" % ("DiskPool", test_dpath)
memid = "%s/%s" % ("MemoryPool", 0)
procid = "%s/%s" % ("ProcessorPool", 0)
rev = 463

def conf_file():
    """
       Creating diskpool.conf file.
    """
    try:
        f = open(disk_file, 'w')
        f.write('%s %s' % (test_dpath, '/'))
        f.close()
    except Exception,detail:
        logger.error("Exception: %s", detail)
        status = SKIP 
        sys.exit(status)

def clean_up_restore():
    """
        Restoring back the original diskpool.conf 
        file.
    """
    try: 
        if os.path.exists(back_disk_file):
            os.remove(disk_file)
            move_file(back_disk_file, disk_file)
    except Exception, detail:
        logger.error("Exception: %s", detail)
        status = SKIP 
        sys.exit(status)
    
@do_main(platform_sup)     
def main():

    options = main.options
    status = PASS
    server = options.ip
    os.system("rm -f %s" % back_disk_file )
    if not (os.path.exists(disk_file)):
        conf_file()
    else:
        move_file(disk_file, back_disk_file)
        conf_file()

    vir_network = net_list(server)
    if len(vir_network) > 0:
        test_network = vir_network[0]
    else:
        bridgename   = 'testbridge'
        test_network = 'default-net'
        net_xml, bridge = netxml(server, bridgename, test_network)
        ret = create_vnet(server, net_xml)
        if not ret:
            logger.error("Failed to create the Virtual Network '%s'",
                         test_network)
            return SKIP
    net_instid = 'NetworkPool/%s' %test_network
    instid_list = ['ProcessorPool/0', 'MemoryPool/0',
                   'DiskPool/foo', net_instid]
    conn = assoc.myWBEMConnection('http://%s' % options.ip,
                                  (CIM_USER, CIM_PASS), CIM_NS)
    classname =  get_typed_class(options.virt, "AllocationCapabilities") 


    field = 'INVALID_Instid_KeyValue'
    keys = { 'InstanceID' : field }
    exp = {
            "invalid_keyname" : { 'rc' : pywbem.CIM_ERR_FAILED,
                                  'desc' : 'No InstanceID specified' },
            "invalid_keyvalue" : { 'rc' : pywbem.CIM_ERR_NOT_FOUND,
                                   'desc' : 'Instance not found' }}
    if CIM_REV < rev:
        exp['invalid_keyvalue']['desc'] = 'Object could not be found'

    ret_value = try_getinstance(conn, classname, keys, field_name=field,
                                expr_values=exp['invalid_keyvalue'], bug_no="")
    if ret_value != PASS:
        logger.error("------ FAILED: Invalid InstanceID Key Value.------")
        status = ret_value

    field = 'INVALID_Instid_KeyName'
    for i in range(len(instid_list)):
        keys = { field : instid_list[i] }
        ret_value = try_getinstance(conn, classname, keys, field_name=field,
                                    expr_values=exp['invalid_keyname'],
                                    bug_no="")
        if ret_value != PASS:
            logger.error("------ FAILED: Invalid InstanceID Key Name.------")
            status = ret_value
        if status != PASS: 
            break
    clean_up_restore()
    return status
if __name__ == "__main__":
    sys.exit(main())
