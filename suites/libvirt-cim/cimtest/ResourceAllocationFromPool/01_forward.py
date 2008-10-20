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
from VirtLib import utils
from XenKvmLib import assoc
from XenKvmLib import enumclass
from XenKvmLib.classes import get_typed_class
from XenKvmLib.test_doms import destroy_and_undefine_all
from XenKvmLib.vxml import get_class 
from CimTest import Globals
from CimTest.Globals import logger
from XenKvmLib.const import do_main, default_pool_name, default_network_name
from CimTest.ReturnCodes import PASS, FAIL, XFAIL

sup_types = ['Xen', 'XenFV', 'KVM', 'LXC']

test_dom    = "RAFP_dom"
test_vcpus  = 1
test_mem    = 128
test_mac    = "00:11:22:33:44:aa"
test_npool  = default_network_name

def setup_env(server, virt):
    destroy_and_undefine_all(server)
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
        vsxml = virtxml(test_dom, mem=test_mem, vcpus = test_vcpus,
                        mac = test_mac, disk = test_disk, 
                        ntype='network', net_name = test_npool)
    
    try:
        ret = vsxml.cim_define(server)
        if not ret:
            logger.error("Failed to Define the domain: %s", test_dom)
            return FAIL, vsxml, test_disk

    except Exception, details:
        logger.error("Exception : %s", details)
        return FAIL, vsxml, test_disk

    return PASS, vsxml, test_disk

def get_instance(server, pool, list, virt='Xen'):
    pool_cn = get_typed_class(virt, pool)
    try:
        inst = enumclass.GetInstance(server, pool_cn, list)
    except Exception:
        logger.error(Globals.CIM_ERROR_GETINSTANCE  % pool_cn)
        return FAIL, inst
  
    return PASS, inst

def verify_rasd(server, assoc_cn, cn, virt, list, rasd):
    try:
        assoc_cn = get_typed_class(virt, assoc_cn)
        data = assoc.AssociatorNames(server,
                                     assoc_cn,
                                     get_typed_class(virt, cn),
                                     InstanceID=list)
    except Exception:
        logger.error(Globals.CIM_ERROR_ASSOCIATORNAMES % cn)
        return FAIL

    if len(data) < 1:
        logger.error("Return NULL, expect at least one instance")
        return FAIL
   
    for item in data:
        if item['InstanceID'] == rasd[cn]:
            logger.info("%s InstanceID match - expect %s, got %s" \
                        % (cn, rasd[cn], item['InstanceID']))
            return PASS 
    logger.error("RASD instance with InstanceID %s not found" % rasd[cn])
    return FAIL
               
@do_main(sup_types)
def main():
    options = main.options
    status = PASS

   
    status, vsxml, test_disk = setup_env(options.ip, options.virt)
    if status != PASS:
        vsxml.undefine(options.ip)
        return status
    
    diskp_id = "DiskPool/%s" % default_pool_name

    if options.virt == 'LXC':
        pool = { "MemoryPool" : {'InstanceID' : "MemoryPool/0"} }
        rasd = { "MemoryPool" :  "%s/mem" % test_dom }
    else:
        pool = { "MemoryPool"    : {'InstanceID' : "MemoryPool/0"},
                 "ProcessorPool" : {'InstanceID' : "ProcessorPool/0"},
                 "DiskPool"      : {'InstanceID' : diskp_id},
                 "NetworkPool"   : {'InstanceID' : "NetworkPool/%s" \
                                     % test_npool }}
        rasd = { "MemoryPool"    : "%s/mem" % test_dom, 
                 "ProcessorPool" : "%s/proc" % test_dom, 
                 "DiskPool"      : "%s/%s" %(test_dom, test_disk), 
                 "NetworkPool"   : "%s/%s" % (test_dom, test_mac) }

    for k, v in pool.iteritems():
        status, inst = get_instance(options.ip, k, v, options.virt) 
        if status != PASS:
            break 
        status = verify_rasd(options.ip, "ResourceAllocationFromPool", 
                             k, options.virt, inst.InstanceID,
                             rasd)
        if status != PASS:
            break

    vsxml.undefine(options.ip)
    return status 
        
        
if __name__ == "__main__":
    sys.exit(main())
