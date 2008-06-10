#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Guolian Yun <yunguol@cn.ibm.com>
#    Kaitlin Rupert <karupert@us.ibm.com>
#    Zhengang Li <lizg@cn.ibm.com>
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

import sys
from VirtLib import utils
from XenKvmLib import assoc
from XenKvmLib.test_doms import destroy_and_undefine_all
from XenKvmLib.vxml import get_class
from XenKvmLib.classes import get_typed_class
from CimTest import Globals
from CimTest.Globals import logger, do_main
from CimTest.ReturnCodes import PASS, FAIL
from XenKvmLib import enumclass
from XenKvmLib.common_util import cleanup_restore, create_diskpool_conf, \
create_netpool_conf


sup_types = ['Xen', 'XenFV', 'KVM', 'LXC']
test_dom    = "RAFP_dom"
test_vcpus  = 1
test_mem    = 128
test_mac    = "00:11:22:33:44:aa"

def setup_env(server, virt):
    destroy_and_undefine_all(server)
    vsxml = None
    if virt == "Xen":
        test_disk = "xvda"
    else:
        test_disk = "hda"

    virtxml = get_class(virt)
    if virt == 'LXC':
        vsxml = virtxml(test_dom)
    else:
        vsxml = virtxml(test_dom, mem=test_mem, vcpus = test_vcpus,
                        mac = test_mac, disk = test_disk)
    try:
        ret = vsxml.define(server)
        if not ret:
            logger.error("Failed to Define the domain: %s", test_dom)
            return FAIL, vsxml, test_disk

    except Exception, details:
        logger.error("Exception : %s", details)
        return FAIL, vsxml, test_disk

    return PASS, vsxml, test_disk

def init_list(test_disk, diskid, test_network, virt='Xen'):

    proc = { 'rasd_id' : '%s/%s' % (test_dom, 'proc'),
             'pool_id' : 'ProcessorPool/0'
           }

    mem = { 'rasd_id' : '%s/%s' % (test_dom,'mem'),
            'pool_id' : 'MemoryPool/0'
          }

    net  = { 
             'rasd_id' : '%s/%s' % (test_dom, test_mac),
             'pool_id' : 'NetworkPool/%s' %test_network
           }

    disk = { 'rasd_id' : '%s/%s' % (test_dom, test_disk),
             'pool_id' : diskid
           }

    if virt == 'LXC':
        cn_id_list = {
                       'MemResourceAllocationSettingData'  : mem,
                     }
    else:
        cn_id_list = {
                       'MemResourceAllocationSettingData'  : mem,
                       'ProcResourceAllocationSettingData' : proc,
                       'NetResourceAllocationSettingData'  : net,
                       'DiskResourceAllocationSettingData' : disk
                     }

    return cn_id_list

def get_rasd_instance(server, virt, key_list, cn):
    inst = None 
    try:
        inst = enumclass.getInstance(server, cn, key_list, virt)
    except Exception, details:
        logger.error(Globals.CIM_ERROR_GETINSTANCE, cn)
        logger.error("Exception details: %s", details)
        return inst, FAIL

    return inst, PASS

def verify_pool_from_RAFP(server, virt, inst, pool_id, cn):
    pool = []
    try:
        pool = assoc.AssociatorNames(server, "ResourceAllocationFromPool",
                                     cn, virt, InstanceID = inst.InstanceID)
    except Exception:
        logger.error(Globals.CIM_ERROR_ASSOCIATORNAMES, inst.InstanceID)
        return FAIL

    if len(pool) != 1:
        logger.error("No associated pool for %s", inst.InstanceID)
        return FAIL

    if pool[0]['InstanceID'] != pool_id:
        logger.error("InstanceID Mismatch")
        logger.error("Returned %s instead of %s", pool[0]['InstanceID'] ,
                      pool_id)
        return FAIL

    return PASS

def get_rasdinst_verify_pool_from_RAFP(server, virt, vsxml, cn, id_info):
    try:
        key_list = {  'InstanceID' : id_info['rasd_id'] }
        rasd_cn =  get_typed_class(virt, cn) 
        rasdinst, status = get_rasd_instance(server, virt, key_list, rasd_cn)
        if status != PASS or rasdinst.InstanceID == None:
            vsxml.undefine(server)    
            return status

        status = verify_pool_from_RAFP(server, virt, rasdinst, 
                                       id_info['pool_id'], cn)
    except Exception, details:
        logger.error("Exception in get_rasdinst_verify_pool_from_RAFP() fn")
        logger.error("Exception Details %s", details)
        status = FAIL

    if status != PASS:
        vsxml.undefine(server)    

    return status
    

@do_main(sup_types)
def main():
    options = main.options
    status = PASS
    server = options.ip
    virt = options.virt
    
    status, vsxml, test_disk = setup_env(server, virt)
    if status != PASS:
        return status

    status, diskid = create_diskpool_conf(server, virt)
    if status != PASS:
        return status

    status, test_network = create_netpool_conf(server, virt)
    if status != PASS:
        return status

    cn_id_list = init_list(test_disk, diskid, test_network, options.virt)

    for rasd_cn, id_info in cn_id_list.iteritems():
        status = get_rasdinst_verify_pool_from_RAFP(server, virt, vsxml, 
                                                    rasd_cn, id_info)
        if status != PASS:
            return status

    cleanup_restore(server, virt)
    vsxml.undefine(server)    
    return status

if __name__ == "__main__":
    sys.exit(main())
