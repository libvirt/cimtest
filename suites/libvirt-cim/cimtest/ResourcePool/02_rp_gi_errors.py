#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Author:
#   Anoop V Chakkalakkal
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
# returned by ResourcePool providers on giving invalid inputs.
#
#
#                                                        Date : 19-02-2008

import os
import sys
import pywbem
from XenKvmLib.xm_virt_util import net_list
from XenKvmLib import assoc
from XenKvmLib import vxml
from XenKvmLib.common_util import try_getinstance
from XenKvmLib.classes import get_typed_class
from distutils.file_util import move_file
from CimTest.ReturnCodes import PASS, SKIP
from CimTest.Globals import logger, CIM_USER, CIM_PASS, CIM_NS
from XenKvmLib.const import do_main, default_pool_name

sup_types = ['Xen', 'KVM', 'XenFV', 'LXC']

expr_values = {
        "invalid_keyname"  : { 'rc'   : pywbem.CIM_ERR_FAILED,
                               'desc' : 'Missing InstanceID' },
        "invalid_keyvalue" : { 'rc'   : pywbem.CIM_ERR_NOT_FOUND,
                               'desc' : 'No such instance (Invalid_Keyvalue)'}
        }

def err_invalid_instid_keyname(conn, classname, instid):
    # Input:
    # ------
    # wbemcli gi '<scheme>://[user:pwd@]<host>:<port>/<namespace:<ClassName>.
    # Invalid_Keyname="<InstanceID>"'
    #
    # Output:
    # -------
    # error code  : CIM_ERR_FAILED
    # error desc  : "Missing InstanceID"
    #
    key = {'Invalid_Keyname' : instid}
    return try_getinstance(conn, classname, key,
                           field_name='INVALID_InstID_KeyName',
                           expr_values=expr_values['invalid_keyname'],
                           bug_no="")


def err_invalid_instid_keyvalue(conn, classname):
    # Input:
    # ------
    # wbemcli gi '<scheme>://[user:pwd@]<host>:<port>/<namespace:<ClassName>.
    # InstanceID="Invalid_Keyvalue"
    #
    # Output:
    # -------
    # error code  : CIM_ERR_NOT_FOUND
    # error desc  : "No such instance (Invalid_Keyvalue)"
    #
    key = {'InstanceID' : 'Invalid_Keyvalue'}
    return try_getinstance(conn, classname, key,
                           field_name='INVALID_InstID_KeyValue',
                           expr_values=expr_values['invalid_keyvalue'],
                           bug_no="")


@do_main(sup_types)
def main():
    ip = main.options.ip
    if main.options.virt == "XenFV":
        virt = "Xen"
    else:
        virt = main.options.virt
    conn = assoc.myWBEMConnection('http://%s' % ip, (CIM_USER, CIM_PASS),
                                  CIM_NS)

    # Verify the Virtual Network on the machine.
    vir_network = net_list(ip, virt)
    if len(vir_network) > 0:
        test_network = vir_network[0]
    else:
        bridgename   = 'testbridge'
        test_network = 'default-net'
        netxml = vxml.NetXML(ip, bridgename, test_network, virt)
        ret = netxml.create_vnet()
        if not ret:
            logger.error("Failed to create the Virtual Network '%s'",
                         test_network)
            return SKIP
    netid = "%s/%s" % ("NetworkPool", test_network)

    if virt == 'LXC':
        cn_instid_list = {
                          get_typed_class(virt, "MemoryPool")    : "MemoryPool/0",
                          get_typed_class(virt, "NetworkPool")   : netid,
                          get_typed_class(virt, "ProcessorPool") : "ProcessorPool/0"
                         }
    else:
        cn_instid_list = {
                          get_typed_class(virt, "DiskPool")      : "DiskPool/foo",
                          get_typed_class(virt, "MemoryPool")    : "MemoryPool/0",
                          get_typed_class(virt, "NetworkPool")   : netid,
                          get_typed_class(virt, "ProcessorPool") : "ProcessorPool/0"
                          }

    for cn, instid in cn_instid_list.items():
        ret_value = err_invalid_instid_keyname(conn, cn, instid)
        if ret_value != PASS:
            logger.error("------ FAILED: Invalid InstanceID Key Name.------")
            return  ret_value

        ret_value = err_invalid_instid_keyvalue(conn, cn)
        if ret_value != PASS:
            logger.error("------ FAILED: Invalid InstanceID Key Value.------")
            return ret_value

    return PASS

if __name__ == "__main__":
    sys.exit(main())
