#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Deepti B.Kalakeri <dkalaker@in.ibm.com>
#    Guolian Yun <yunguol@cn.ibm.com>
#    Kaitlin Rupert <karupert@us.ibm.com>
#    Veerendra Chandrappa <vechandr@in.ibm.com>
#    Zhengang Li <lizg@cn.ibm.com>
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
import os
from VirtLib import utils
from distutils.file_util import move_file
from XenKvmLib import enumclass
from CimTest import Globals
from CimTest.Globals import log_param, logger, do_main
from CimTest.ReturnCodes import PASS, FAIL, SKIP
from VirtLib.live import net_list
from XenKvmLib.test_xml import netxml
from XenKvmLib.test_doms import create_vnet
from XenKvmLib.vsms import RASD_TYPE_PROC, RASD_TYPE_MEM, RASD_TYPE_NET_ETHER, \
RASD_TYPE_DISK 


sup_types = ['Xen']

test_dpath = "foo"
disk_file = '/tmp/diskpool.conf'
back_disk_file = disk_file + "." + "resourcepool_enum"
diskid = "%s/%s" % ("DiskPool", test_dpath)

def conf_file():
    """
       Creating diskpool.conf file.
    """
    status = PASS
    try:
        f = open(disk_file, 'w')
        f.write('%s %s' % (test_dpath, '/'))
        f.close()
    except Exception,detail:
        logger.error("Exception: %s", detail)
        status = SKIP
    if status != PASS:
        logger.error("Creation of Disk Conf file Failed")
    return status
        

def clean_up_restore():
    """
        Restoring back the original diskpool.conf 
        file.
    """
    status = PASS
    try:
        if os.path.exists(back_disk_file):
            os.remove(disk_file)
            move_file(back_disk_file, disk_file)
    except Exception, detail:
        logger.error("Exception: %s", detail)
        return SKIP
    if status != PASS:
        logger.error("Failed to Disk Conf file")
    return status

def init_list(server):
    global pool_list
    status = PASS
    os.system("rm -f %s" % back_disk_file )
    if not (os.path.exists(disk_file)):
        status = conf_file()
    else:
        move_file(disk_file, back_disk_file)
        status = conf_file()
    if status != PASS:
        return status
    vir_network = net_list(server)
    if len(vir_network) > 0:
        test_network = vir_network[0]
    else:
        bridgename   = 'testbridge'
        test_network = 'default-net'
        net_xml, bridge = netxml(server, bridgename, test_network)
        ret = create_vnet(server, net_xml)
        if not ret:
            logger.error("Failed to create the Virtual Network '%s'", \
                                                           test_network)
            return SKIP
    disk_instid = 'DiskPool/%s' %test_dpath
    net_instid = 'NetworkPool/%s' %test_network
    pool_list = { 
                 'Xen_MemoryPool'    : ['MemoryPool/0', RASD_TYPE_MEM], \
                 'Xen_ProcessorPool' : ['ProcessorPool/0', RASD_TYPE_PROC], \
                 'Xen_DiskPool'      : [disk_instid, RASD_TYPE_DISK], \
                 'Xen_NetworkPool'   : [net_instid, RASD_TYPE_NET_ETHER]
               } 
    return status 

def print_error(fieldname="", ret_value="", exp_value=""):
    logger.error("%s Mismatch", fieldname)
    logger.error("Returned %s instead of %s", ret_value, exp_value)

def verify_fields(poolname, cn):
    global pool_list
    status = PASS
    if len(poolname) < 1:
        logger.error("%s return %i instances, expected atleast 1 instance" \
                     % (cn, len(poolname)))
        return FAIL
    ret_value = poolname[0].InstanceID
    exp_value = pool_list[cn][0]
    if ret_value != exp_value:
        print_error('InstanceID', ret_value, exp_value)
        status = FAIL
    ret_value = poolname[0].ResourceType
    exp_value = pool_list[cn][1]
    if ret_value != exp_value:
        print_error('ResourceType', ret_value, exp_value)
        status = FAIL
    return status


@do_main(sup_types)
def main():
    options = main.options

    log_param()
    global pool_list
    server = options.ip
    status = init_list(server)
    if status != PASS: 
        logger.error("Failed to initialise the list")
        return status

    key_list = ["InstanceID"]
    try:
        mempool = enumclass.enumerate(options.ip,
                                      enumclass.Xen_MemoryPool,
                                                      key_list)
    except Exception:
        logger.error(Globals.CIM_ERROR_ENUMERATE % enumclass.Xen_MemoryPool)
        return FAIL
    status = verify_fields(poolname=mempool, cn='Xen_MemoryPool')
    try:
        propool = enumclass.enumerate(options.ip,
                                      enumclass.Xen_ProcessorPool,
                                      key_list)
    except Exception:
        logger.error(Globals.CIM_ERROR_ENUMERATE % enumclass.Xen_ProcessorPool)
        return FAIL

    status = verify_fields(poolname=propool, cn='Xen_ProcessorPool')
    try:
        diskpool = enumclass.enumerate(options.ip,
                                      enumclass.Xen_DiskPool,
                                      key_list)
    except Exception:
        logger.error(Globals.CIM_ERROR_ENUMERATE % enumclass.Xen_DiskPool)
        return FAIL
    status = verify_fields(poolname=diskpool, cn='Xen_DiskPool') 
    try:
        netpool = enumclass.enumerate(options.ip,
                                      enumclass.Xen_NetworkPool,
                                      key_list)
    except Exception:
        logger.error(Globals.CIM_ERROR_ENUMERATE % enumclass.Xen_NetworkPool)
        return FAIL
    status = verify_fields(poolname=netpool, cn='Xen_NetworkPool')
    status = clean_up_restore()
    return status

if __name__ == "__main__":
    sys.exit(main())
