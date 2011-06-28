#!/usr/bin/python
#
# Copyright 2010 IBM Corp.
#
# Authors:
#    Deepti B. Kalakeri <deeptik linux vnet ibm com>
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
#   Verify provider's VSI support.
#
# Steps:
#  1) Build RASD parameters, making sure to specify macvtap mode for network
#     interface and vsi values.
#  2) Create guest
#  3) Verify guest is defined properly and the vsi values assgined to the guest
#     are reflected in the NetRASD.
#
#                                               Date: 16-07-2010
#

import sys
from CimTest.Globals import logger
from CimTest.ReturnCodes import FAIL, PASS, SKIP, XFAIL_RC, XFAIL
from XenKvmLib.classes import get_typed_class, inst_to_mof
from XenKvmLib.rasd import get_default_rasds
from XenKvmLib.const import do_main, get_provider_version
from XenKvmLib.vxml import get_class
from XenKvmLib.common_util import parse_instance_id
from XenKvmLib.enumclass import EnumInstances

sup_types = ['Xen', 'XenFV', 'KVM']
test_dom = 'vsi_guest'
bug_no = "00016" 

libvirt_cim_vsi_support = 1042 

def get_rasd_list(ip, virt, vsi_defaults, nrasd_cn):
    rasds = get_default_rasds(ip, virt)
    rasd_list = {} 

    for rasd in rasds:
        if rasd.classname == nrasd_cn and "Default" in rasd['InstanceID']:

            rasd['NetworkMode'] = vsi_defaults['NetworkMode']
            rasd['NetworkType'] = vsi_defaults['NetworkType']
            rasd['SourceDevice'] = vsi_defaults['SourceDevice']
            rasd['VSIType'] = vsi_defaults['VSIType']
            rasd['VSIManagerID'] = vsi_defaults['VSIManagerID']
            rasd['VSITypeID'] = vsi_defaults['VSITypeID']
            rasd['VSITypeIDVersion'] = vsi_defaults['VSITypeIDVersion']
        # Currently Libvirt throws error when passing Profile id, 
        # add it when supported
        #    rasd['ProfileID'] = vsi_defaults['ProfileID']
            rasd_list[rasd.classname] = inst_to_mof(rasd)
            break

    return rasd_list 

def get_net_inst(ip, nrasd_cn, guest_name):
    inst = None
    enum_list = EnumInstances(ip, nrasd_cn)

    if enum_list < 1:
        logger.error("No %s instances returned", nrasd_cn)
        return FAIL, inst

    for rasd in enum_list:
        guest, dev, status = parse_instance_id(rasd.InstanceID)
        if status != PASS:
            logger.error("Unable to parse InstanceID: %s", rasd.InstanceID)
            return FAIL, inst

        if guest == guest_name:
            inst = rasd 
            break

    if inst is None:
        logger.error("%s instance for %s not found", nrasd_cn, guest_name)
        return FAIL, inst
    else:
        return PASS, inst
   

def verify_net_rasd(ip, virt, vsi_defaults, inst):
    try:
        if inst.NetworkMode != vsi_defaults['NetworkMode']:
            raise Exception("%s" % "NetworkMode", \
                            "%s" % inst.NetworkMode, \
                            "%s" % vsi_defaults['NetworkMode'],\
                            "%s" % FAIL)

        if inst.SourceDevice != vsi_defaults['SourceDevice']:
            raise Exception("%s" % "SourceDevice", \
                            "%s" % inst.SourceDevice, "%s" \
                            % vsi_defaults['SourceDevice'],\
                            "%s" % FAIL)

        if inst.VSIType != vsi_defaults['VSIType']:
            raise Exception("%s" % "VSIType", \
                             "%s" % inst.VSIType, "%s" \
                             % vsi_defaults['VSIType'], \
                             "%s" % FAIL)

        # Once the bug is fixed change the status value from XFAIL to FAIL
        if inst.VSIInstanceID == None:
            raise Exception("%s" % "VSIInstanceID", \
                            "%s" % inst.VSIInstanceID, \
                            "%s" % "a value",\
                            "%s" % XFAIL)
       
        if inst.VSITypeIDVersion != vsi_defaults['VSITypeIDVersion']:
            raise Exception("%s" % "VSITypeIDVersion", 
                            "%s" % inst.VSITypeIDVersion, \
                            "%s" % vsi_defaults['VSITypeIDVersion'],\
                            "%s" % XFAIL)

        if inst.VSITypeID != vsi_defaults['VSITypeID']:
            raise Exception("%s" % "VSITypeID", \
                            "%s" % inst.VSITypeID, \
                            "%s" % vsi_defaults['VSITypeID'], \
                            "%s" % XFAIL)

    except Exception, (field, ret_val, exp_val, status):
        logger.error("Mismatch in '%s' values", field)
        logger.error("Got %s, Expected %s", ret_val, exp_val)
        if status == "3":
             return XFAIL_RC(bug_no)
        return status

    return PASS 

@do_main(sup_types)
def main():
    options = main.options
    server = options.ip
    virt = options.virt

    status = FAIL

    curr_cim_rev, changeset = get_provider_version(virt, server)
    if curr_cim_rev < libvirt_cim_vsi_support:
        logger.error("VSI support is available in rev >= %s", 
                      libvirt_cim_vsi_support)
        return SKIP


    # Currently Libvirt throws error when passing Profile id, 
    # add it when supported
    #    'ProfileID' : "vsi_profile"
    # Also, Libvirt returns error when 'VSIType' is 802.1Qbh 
    # The tc can be modified to loop for the different VSIType, 
    # when supported.
    vsi_defaults = { 'NetworkMode'  : "vepa",
                     'NetworkType'  : "direct",
                     'SourceDevice' : "eth1",
                     'VSIType'      : "802.1Qbg",
                     'VSIManagerID' : "12",
                     'VSITypeID'    : "0x12345",
                     'VSITypeIDVersion' : "1"
                   } 

    nrasd_cn = get_typed_class(virt, 'NetResourceAllocationSettingData')
    status  = FAIL
    cxml = None

    try:
        rasd_list = get_rasd_list(server, virt, vsi_defaults, nrasd_cn)
        if len(rasd_list) < 1:
            status = FAIL
            raise Exception("Unable to get template RASDs for %s" % test_dom)

        cxml = get_class(virt)(test_dom)
        cxml.set_res_settings(rasd_list)
        ret = cxml.cim_define(server)
        if not ret:
            status = FAIL
            raise Exception("Unable to define guest %s" % test_dom)
       
        status = cxml.cim_start(server)
        if status != PASS:
            status = XFAIL
            raise Exception("Unable to start VM "
                            "*** Is VSI support available on this host? ***")

        status, inst = get_net_inst(server, nrasd_cn, test_dom)
        if status != PASS:
            status = FAIL
            raise Exception("Failed to get net interface for %s" % test_dom)

        status = verify_net_rasd(server, virt, vsi_defaults, inst)
        if status != PASS:
            status = FAIL
            logger.error("Failed to verify net interface for %s", test_dom)

    except Exception, details:
        logger.error(details)

    if cxml is not None:
        cxml.cim_destroy(server)
        cxml.undefine(server)

    return status 

if __name__ == "__main__":
    sys.exit(main())
    
