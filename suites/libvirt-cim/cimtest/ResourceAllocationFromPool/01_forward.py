#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Guolian Yun <yunguol@cn.ibm.com>
#    Kaitlin Rupert <karupert@us.ibm.com>
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
from CimTest.Globals import logger
from CimTest.ReturnCodes import PASS, FAIL
from XenKvmLib.assoc import AssociatorNames 
from XenKvmLib.classes import get_typed_class
from XenKvmLib.vxml import get_class
from XenKvmLib.const import do_main, default_pool_name, default_network_name, \
                            LXC_netns_support
from XenKvmLib.pool import pool_cn_to_rasd_cn, enum_pools
from XenKvmLib.rasd import enum_rasds 
from XenKvmLib.common_util import parse_instance_id

sup_types = ['Xen', 'XenFV', 'KVM', 'LXC']

test_dom    = "RAFP_dom"

def setup_env(server, virt):
    vsxml = None
    if virt == "Xen":
        test_disk = "xvda"
    elif virt == "XenFV" or virt=="KVM":
        test_disk = "hda"
    else:
        test_disk = None

    virtxml = get_class(virt)
    if virt == 'LXC':
        vsxml = virtxml(test_dom)
    else:
        vsxml = virtxml(test_dom, disk=test_disk) 
    
    try:
        ret = vsxml.cim_define(server)
        if not ret:
            logger.error("Failed to Define the domain: %s", test_dom)
            return FAIL, vsxml, test_disk

    except Exception, details:
        logger.error("Exception : %s", details)
        return FAIL, vsxml, test_disk

    return PASS, vsxml, test_disk

def init_rasd_list(virt, ip, guest_name):
    disk_rasd_cn = get_typed_class(virt, "DiskResourceAllocationSettingData")

    rasd_insts = {}

    rasds, status = enum_rasds(virt, ip)
    if status != PASS:
        logger.error("Enum RASDs failed")
        return rasd_insts, status

    for rasd_cn, rasd_list in rasds.iteritems():
        if virt == "LXC" and rasd_cn == disk_rasd_cn:
            continue

        for rasd in rasd_list:
            guest, dev, status = parse_instance_id(rasd.InstanceID)
            if status != PASS:
                logger.error("Unable to parse InstanceID: %s", rasd.InstanceID)
                return rasd_insts, FAIL

            if guest == guest_name:
                rasd_insts[rasd.Classname] = rasd

    return rasd_insts, PASS

def filter_pool_list(virt, list, cn):
    diskp_cn = get_typed_class(virt, "DiskPool")
    netp_cn = get_typed_class(virt, "NetworkPool")

    if cn == diskp_cn:
        exp_id = default_pool_name
    elif cn == netp_cn:
        exp_id = default_network_name
    else:
         return None, PASS 

    if len(list) < 1:
        logger.error("%s did not return any instances", cn)
        return None, FAIL

    for inst in list:
        guest, id, status = parse_instance_id(inst.InstanceID)
        if status != PASS:
            logger.error("Unable to parse InstanceID: %s", inst.InstanceID)
            return None, FAIL

        if id == exp_id:
            return inst, PASS

    return None, FAIL


def init_pool_list(virt, ip):
    pool_insts = {}

    pools, status = enum_pools(virt, ip)
    if status != PASS:
        return pool_insts, status
   
    for pool_cn, pool_list in pools.iteritems():
        inst, status = filter_pool_list(virt, pool_list, pool_cn)
        if status != PASS:
            logger.error("Unable to find exp %s inst", pool_cn)
            return pool_insts, FAIL 

        if inst is None:
            if len(pool_list) != 1:
                logger.error("Got %d %s, exp 1", len(pool_list), pool_cn)
                return pool_insts, FAIL 
            inst = pool_list[0]

        pool_insts[pool_cn] = inst

    if len(pool_insts) != len(pools):
        logger.error("Got %d pool insts, exp %d", len(pool_insts), len(pools))
        return pool_insts, FAIL 

    if virt == "LXC":
        diskp_cn = get_typed_class(virt, "DiskPool")
        del pool_insts[diskp_cn]

        if LXC_netns_support is False:
            netp_cn = get_typed_class(virt, "NetworkPool")
            del pool_insts[netp_cn]

    return pool_insts, PASS

def verify_rasd(enum_list, rasds, rasd_cn, guest_name):
    status = FAIL

    for rasd in enum_list:
        guest, dev, status = parse_instance_id(rasd['InstanceID'])
        if status != PASS:
            logger.error("Unable to parse InstanceID: %s", rasd['InstanceID'])
            return status 

        if guest != guest_name:
            continue

        exp_rasd = rasds[rasd_cn]

        if rasd['InstanceID'] == exp_rasd.InstanceID:
            status = PASS
        else:
            logger.info("Got %s instead of %s", rasd['InstanceID'],
                        exp_rasd.InstanceID)
            status = FAIL

    if status != PASS:
        logger.error("RASD with id %s not returned", exp_rasd.InstanceID)
        return FAIL

    return PASS

@do_main(sup_types)
def main():
    options = main.options
    status = PASS

    status, vsxml, test_disk = setup_env(options.ip, options.virt)
    if status != PASS:
        vsxml.undefine(options.ip)
        return status

    try:
        rasds, status = init_rasd_list(options.virt, options.ip, test_dom)
        if status != PASS:
            raise Exception("Unable to build rasd instance list")

        pools, status = init_pool_list(options.virt, options.ip)
        if status != PASS:
            raise Exception("Unable to build pool instance list")

        if len(rasds) != len(pools):
            raise Exception("%d RASD insts != %d pool insts" % (len(rasds),
                            len(pools)))

        assoc_cn = get_typed_class(options.virt, "ResourceAllocationFromPool")
        for pool_cn, pool in pools.iteritems():
            data = AssociatorNames(options.ip,
                                   assoc_cn,
                                   pool_cn,
                                   InstanceID=pool.InstanceID)

            if len(data) < 1:
                raise Exception("No RASD associated with %s" % pool.InstanceID)

            rasd_cn = pool_cn_to_rasd_cn(pool_cn, options.virt)
            status = verify_rasd(data, rasds, rasd_cn, test_dom)
            if status != PASS:
                raise Exception("Failed to verify RASDs")

    except Exception, details:
        logger.error(details)
        status = FAIL

    vsxml.undefine(options.ip)
    return status 
        
        
if __name__ == "__main__":
    sys.exit(main())
