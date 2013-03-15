#!/usr/bin/python
#
# Copyright 2010 IBM Corp.
#
# Authors:
#    Sharad Mishra <snmishra us ibm com>
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
# Purpose:
#   Verify provider's support for macvtap.
#
# Steps:
#  1) Build RASD parameters, making sure to specify macvtap mode for network
#     interface 
#  2) Create guest
#  3) Verify guest is defined properly
#

import sys
from CimTest.Globals import logger
from CimTest.ReturnCodes import FAIL, PASS, SKIP
from VirtLib import utils
from XenKvmLib.classes import get_typed_class, inst_to_mof
from XenKvmLib.rasd import get_default_rasds
from XenKvmLib.const import do_main, get_provider_version
from XenKvmLib.vxml import get_class
from XenKvmLib.common_util import parse_instance_id
from XenKvmLib.enumclass import EnumInstances

sup_types = ['Xen', 'XenFV', 'KVM']
test_dom = 'rstest_nic'

target_dev_rev = 1029 

def get_rasd_list(ip, virt, target_dev, source_dev):
    nrasd_cn = get_typed_class(virt, "NetResourceAllocationSettingData")

    rasds = get_default_rasds(ip, virt)

    rasd_list = {} 

    for rasd in rasds:
        if rasd.classname == nrasd_cn and "Default" in rasd['InstanceID']:

            rasd['NetworkMode'] = target_dev
            rasd['NetworkType'] = "direct"
            rasd['SourceDevice'] = source_dev

        rasd_list[rasd.classname] = inst_to_mof(rasd)

    return rasd_list 

def verify_net_rasd(ip, virt, target_dev, source_dev, guest_name):
    inst = None

    try:
        nrasd_cn = get_typed_class(virt, 'NetResourceAllocationSettingData')
        enum_list = EnumInstances(ip, nrasd_cn)

        if enum_list < 1:
            raise Exception("No %s instances returned" % nrasd_cn)

        for rasd in enum_list:
            guest, dev, status = parse_instance_id(rasd.InstanceID)
            if status != PASS:
                raise Exception("Unable to parse InstanceID: %s" % \
                                rasd.InstanceID)

            if guest == guest_name:
                inst = rasd 
                break

        if inst is None:
            raise Exception("%s instance for %s not found" % (nrasd_cn, 
                            guest_name))

        if inst.NetworkMode != target_dev:
            raise Exception("Expected NetworkMode to be %s" % target_dev)

        if inst.SourceDevice != source_dev:
            raise Exception("Expected SourceDevice to be %s" % source_dev)

    except Exception, details:
        logger.error(details)
        return FAIL

    return PASS 

@do_main(sup_types)
def main():
    options = main.options
    server = options.ip

    status = FAIL

    curr_cim_rev, changeset = get_provider_version(options.virt, options.ip)
    if curr_cim_rev < target_dev_rev:
        logger.error("Network interface target device support is available" \
                     " in rev >= %s", target_dev_rev)
        return SKIP

    cxml = get_class(options.virt)(test_dom)

    target_dev = "vepa"

    # Fedora changed the default device naming scheme, see
    #  http://fedoraproject.org/wiki/Features/ConsistentNetworkDeviceNaming
    #
    # So if we're running on Fedora, let's "default" to "em1" although that
    # doesn't guarantee that we will find what we're looking for.  This code
    # probably needs some mechanism to detect with interfaces are available,
    # then query those interfaces to find one that supports the feature we
    # want.  If not are found and XFAIL could be generated indicating so.
    #
    cmd = 'cat /etc/issue | grep -v ^$ | egrep "Fedora"'
    rc, out = utils.run_remote(server, cmd)
    if rc == 0:
        source_dev = "em1"
    else:
        source_dev = "eth1"

    guest_defined = False

    try:
        rasd_list = get_rasd_list(options.ip, options.virt, target_dev, source_dev)
        if len(rasd_list) < 1:
            raise Exception("Unable to get template RASDs for %s" % test_dom)

        cxml.set_res_settings(rasd_list)
        ret = cxml.cim_define(options.ip)
        if not ret:
            raise Exception("Unable to define %s" % test_dom)
       
        guest_defined = True 

        status = cxml.cim_start(options.ip)
        if status != PASS:
            raise Exception("Unable to start %s" % test_dom)

        status = verify_net_rasd(options.ip, options.virt, target_dev, 
                                 source_dev, test_dom)
        if status != PASS:
            raise Exception("Failed to net interface for %s" % test_dom)

    except Exception, details:
        logger.error(details)
        status = FAIL

    if guest_defined == True: 
        cxml.undefine(options.ip)

    return status 

if __name__ == "__main__":
    sys.exit(main())
    
