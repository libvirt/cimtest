#!/usr/bin/python
#
# Copyright 2009 IBM Corp.
#
# Authors:
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
# This testcase verifies VNC password can be specified via GRASD
# for the guest and the same is set in the Password field of GRASD.
#
#                                                   Date: 16-07-2009
#

import sys
from XenKvmLib import vxml
from CimTest.Globals import logger
from XenKvmLib.enumclass import EnumInstances
from CimTest.ReturnCodes import FAIL, PASS, SKIP
from XenKvmLib.const import do_main, get_provider_version
from XenKvmLib.classes import get_typed_class

libvirtcim_vnc_passwd_changes=925

sup_types = ['Xen', 'KVM', 'XenFV', 'LXC']
default_dom = 'vncpasswd_domain'
passwd = 'cimtest123'

def verify_grasd_passwd_value(virt, server):
    rasd_list   = []
    classname = get_typed_class(virt, "GraphicsResourceAllocationSettingData")
    try:
        rasd_list = EnumInstances(server, classname, ret_cim_inst=True)
        if len(rasd_list) < 1:
            logger.error("%s returned %i instances, excepted at least 1.",
                         classname, len(rasd_list))
            return FAIL

        inst_id = "%s/graphics" % default_dom
        for rasd in rasd_list:
            # Verify the Password for the domain is set
            if rasd['InstanceID'] == inst_id:
                if rasd['Password'] != "" and "*" in rasd['Password']:
                    logger.info("Password for '%s' is set.", default_dom)
                    return PASS

    except Exception, detail:
        logger.error("Exception: %s", detail)
        return FAIL

    logger.error("Password for '%s' is not set.", default_dom)
    return FAIL
            

@do_main(sup_types)
def main():
    options = main.options
    virt = options.virt
    server = options.ip
 
    curr_cim_rev, changeset = get_provider_version(virt, server)
    if curr_cim_rev < libvirtcim_vnc_passwd_changes:
        logger.info("VNC Password support not available, feature available in"\
                    " '%s' revision..", libvirtcim_vnc_passwd_changes)
        return SKIP
        
    if virt == 'LXC':
        logger.info("VNC is not supported by LXC, hence skipping the tc ....")
        return SKIP

    cxml = vxml.get_class(virt)(default_dom, vnc_passwd=passwd)

    try:
        ret = cxml.cim_define(server)
        if not ret:
            raise Exception("Failed to define the dom: %s" % default_dom)

        ret = cxml.cim_start(server)
        if ret != PASS:
            cxml.undefine(server)
            raise Exception("Failed to start the dom: %s" % default_dom)

        status = verify_grasd_passwd_value(virt, server)
        if status != PASS:
            logger.error("Failed to verify the Password field for domain '%s'",
                         default_dom)

    except Exception, details:
        logger.error(details)
        status = FAIL

    cxml.cim_destroy(server)
    cxml.undefine(server)
    return status

if __name__ == "__main__":
    sys.exit(main())
    
