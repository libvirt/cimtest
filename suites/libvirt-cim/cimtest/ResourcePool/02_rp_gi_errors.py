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
from VirtLib.live import net_list
from XenKvmLib import assoc
from XenKvmLib import vxml
from XenKvmLib.common_util import try_getinstance
from XenKvmLib.classes import get_typed_class
from distutils.file_util import move_file
from CimTest.ReturnCodes import PASS, SKIP
from CimTest.Globals import log_param, logger, CIM_USER, CIM_PASS, CIM_NS
from CimTest.Globals import do_main

sup_types = ['Xen', 'KVM']

expr_values = {
        "invalid_keyname"  : { 'rc'   : pywbem.CIM_ERR_FAILED,
                               'desc' : 'Missing InstanceID' },
        "invalid_keyvalue" : { 'rc'   : pywbem.CIM_ERR_NOT_FOUND,
                               'desc' : 'No such instance (Invalid_Keyvalue)'}
        }

test_dpath = "foo"
disk_file = '/tmp/diskpool.conf'
back_disk_file = disk_file + "." + "02_rp_gi_errors"

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


def err_invalid_instid_keyname(classname, instid):
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


def err_invalid_instid_keyvalue(classname):
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
    virt = main.options.virt
    status = PASS
    log_param()

    global conn
    conn = assoc.myWBEMConnection('http://%s' % ip, (CIM_USER, CIM_PASS),
                                  CIM_NS)


    # Taking care of already existing diskconf file
    # Creating diskpool.conf if it does not exist
    # Otherwise backing up the prev file and create new one.
    os.system("rm -f %s" % back_disk_file )
    if (os.path.exists(disk_file)):
        move_file(disk_file, back_disk_file)
    conf_file()

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
            clean_up_restore()
            return SKIP
    netid = "%s/%s" % ("NetworkPool", test_network)

    cn_instid_list = {
            get_typed_class(virt, "DiskPool")      : "DiskPool/foo",
            get_typed_class(virt, "MemoryPool")    : "MemoryPool/0",
            get_typed_class(virt, "NetworkPool")   : netid,
            get_typed_class(virt, "ProcessorPool") : "ProcessorPool/0"
            }

    for cn, instid in cn_instid_list.items():
        ret_value = err_invalid_instid_keyname(cn, instid)
        if ret_value != PASS:
            logger.error("------ FAILED: Invalid InstanceID Key Name.------")
            status = ret_value

        ret_value = err_invalid_instid_keyvalue(cn)
        if ret_value != PASS:
            logger.error("------ FAILED: Invalid InstanceID Key Value.------")
            status = ret_value

    clean_up_restore()
    return status

if __name__ == "__main__":
    sys.exit(main())
