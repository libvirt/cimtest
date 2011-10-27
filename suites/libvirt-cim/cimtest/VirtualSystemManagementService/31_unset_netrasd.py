#!/usr/bin/env python

#
# Copyright 2011 IBM Corp.
#
# Authors:
#   Eduardo Lima (Etrunko) <eblima@br.ibm.com>
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

#
# ModifyResourceSettings call to set/unset NetRASD ResourceType property
#

import sys
import pywbem

from CimTest.ReturnCodes import PASS, FAIL, XFAIL, SKIP
from CimTest.Globals import logger, CIM_USER, CIM_PASS, CIM_NS
from XenKvmLib.const import do_main
from XenKvmLib.classes import get_typed_class
from XenKvmLib.vxml import get_class

supported = ['Xen', 'KVM', 'XenFV', 'LXC']
domain = None

class CIMDomain(object):

    def __init__(self, name, virt, server):
        self.name = name
        self.server = server
        self._domain = get_class(virt)(name)
    #__init__

    def define(self):
        return self._domain.cim_define(self.server)
    # define

    def undefine(self):
        return self._domain.undefine(self.server)
    # undefine

    def destroy(self):
        return self._domain.cim_destroy(self.server)
    #destroy
# CIMDomain


def resource_settings(inst, virt, resource_subtype):
    return """
instance of %s {
    InstanceID="%s";
    ResourceType=%d;
    Address="%s";
    VirtualQuantityUnits="%s";
    NetworkType="%s";
    NetworkName="%s";
    ResourceSubType="%s";
};""" % (get_typed_class(virt, "NetResourceAllocationSettingData"),
        inst["InstanceID"],
        inst["ResourceType"],
        inst["Address"],
        inst["VirtualQuantityUnits"],
        inst["NetworkType"],
        inst["NetworkName"],
        resource_subtype)
# resource_settings()


@do_main(supported)
def main():
    # init
    options = main.options
    server = options.ip
    virt = options.virt

    server_url = "http://%s" % server
    cim = pywbem.WBEMConnection(server_url, (CIM_USER, CIM_PASS), CIM_NS)

    _class = get_typed_class(virt, "VirtualSystemManagementService")
    sys_mgmt_service = cim.EnumerateInstanceNames(_class)[0]

    # Create new domain
    global domain
    domain = CIMDomain("cimtest_unset_netrasd", virt, server)
    if not domain.define():
        logger.error("Error defining test domain")
        return FAIL

    # ein KVM_ComputerSystem
    _class = get_typed_class(virt, "ComputerSystem")
    computer_system_names = [i for i in cim.EnumerateInstanceNames(_class) if i["Name"] == domain.name]

    logger.info("ComputerSystem Names\n%s", computer_system_names)

    if not computer_system_names:
        logger.info("Host has no domains defined")
        return SKIP

    # ain -ac KVM_SystemDevice -arc KVM_NetworkPort <KVM_ComputerSytem Name>
    a_class = get_typed_class(virt, "SystemDevice")
    r_class = get_typed_class(virt, "NetworkPort")
    network_port_names = []

    for inst_name in computer_system_names:
        assoc_names = cim.AssociatorNames(inst_name, AssocClass=a_class, ResultClass=r_class)
        network_port_names.extend(assoc_names)

    logger.info("NetworkPort Names\n%s", network_port_names)

    if not network_port_names:
        logger.info("No NetworkPort instances returned")
        return XFAIL

    # ai -arc KVM_NetResourceAllocationSettingData <KVM_NetworkPort Name>
    r_class = get_typed_class(virt, "NetResourceAllocationSettingData")
    net_rasd_names = []

    for inst_name in network_port_names:
        assoc_names = cim.AssociatorNames(inst_name, ResultClass=r_class)
        net_rasd_names.extend(assoc_names)

    logger.info("NetRASD names\n%s", net_rasd_names)

    if not net_rasd_names:
        logger.info("No NetRASD instances returned")
        return XFAIL

    for subtype in ["virtio", "",]:
        logger.info("Setting ResourceSubType to '%s'", subtype)

        modified_net_rasd_names = []

        for inst_name in net_rasd_names:
            # Get current instance data
            inst = cim.GetInstance(inst_name)
            cur_id = inst["InstanceID"]
            cur_subtype = inst["ResourceSubType"]
            logger.info("Current ResourceSubType of %s: '%s'", cur_id, cur_subtype)

            # Invoke ModifyResourceSettings
            val = resource_settings(inst, virt, subtype)
            ret = cim.InvokeMethod("ModifyResourceSettings", sys_mgmt_service, **{"ResourceSettings": [val,],})

            if ret[0]:
                logger.error("ERROR Setting ResourceSubtype to '%s': %s", subtype, ret)
                return FAIL

            modified_net_rasd_names.extend(ret[1]["ResultingResourceSettings"])

            # Get modified instance data
            inst = cim.GetInstance(ret[1]["ResultingResourceSettings"][0])
            new_id = inst["InstanceID"]
            new_subtype = inst["ResourceSubType"]

            logger.info("Modified ResourceSubType of %s: '%s'", new_id, new_subtype)

            if cur_id != new_id:
                logger.error("Current '%s' and new '%s' InstanceID differ", cur_id, new_id)
                return FAIL

            if new_subtype != subtype:
                logger.error("Current '%s' and expected '%s' ResourceSubType differ", new_subtype, subtype)
                return FAIL
        # for inst_name...

        net_rasd_names = modified_net_rasd_names
    #for subtype...

    return PASS
#main()

if __name__ == "__main__":
    ret = main()

    if domain:
        domain.destroy()
        domain.undefine()

    sys.exit(ret)
