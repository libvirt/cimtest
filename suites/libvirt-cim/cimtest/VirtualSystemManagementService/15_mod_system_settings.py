#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Kaitlin Rupert <karupert@us.ibm.com>
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
import pywbem
from XenKvmLib import vsms
from XenKvmLib import vxml
from CimTest.Globals import logger
from CimTest.ReturnCodes import PASS, FAIL, XFAIL_RC
from XenKvmLib.const import do_main, default_network_name
from XenKvmLib.classes import get_typed_class, inst_to_mof
from XenKvmLib.enumclass import GetInstance 
from XenKvmLib.common_util import poll_for_state_change 
from XenKvmLib.const import get_provider_version

sup_types = ['Xen', 'KVM', 'XenFV', 'LXC']
default_dom = 'rstest_domain'
cpu = 2
RECOVERY_VAL = 3
DEFINED_STATE = 3
bug = "00008"
f9_bug = "00010"
libvirt_f9_revision=613
libvirt_modify_setting_changes = 694

def cleanup_env(ip, cxml):
    cxml.cim_destroy(ip)
    cxml.undefine(ip)

def get_vssd(ip, virt, get_cim_inst):
    cn = get_typed_class(virt, "VirtualSystemSettingData") 
    inst = None

    try:
        if virt == "XenFV": 
            virt = "Xen"

        key_list = {"InstanceID" : "%s:%s" % (virt, default_dom) }
        inst = GetInstance(ip, cn, key_list, get_cim_inst)

    except Exception, details:
        logger.error(details)
        return FAIL, inst

    if inst is None:
        return FAIL, inst

    return PASS, inst

@do_main(sup_types)
def main():
    options = main.options 

    test_cases = ["define", "start"]
    cxml = vxml.get_class(options.virt)(default_dom, vcpus=cpu)
    service = vsms.get_vsms_class(options.virt)(options.ip)

    for case in test_cases:
        #Each time through, define guest using a default XML
        cxml.undefine(options.ip)
        cxml = vxml.get_class(options.virt)(default_dom, vcpus=cpu)
        ret = cxml.cim_define(options.ip)
        if not ret:
            logger.error("Failed to define the dom: %s", default_dom)
            cleanup_env(options.ip, cxml)
            return FAIL

        if case == "start":
            ret = cxml.start(options.ip)
            if not ret:
                logger.error("Failed to start %s", default_dom)
                cleanup_env(options.ip, cxml)
                return FAIL

        status, inst = get_vssd(options.ip, options.virt, True)
        if status != PASS:
            logger.error("Failed to get the VSSD instance for %s", default_dom)
            cleanup_env(options.ip, cxml)
            return FAIL

        inst['AutomaticRecoveryAction'] = pywbem.cim_types.Uint16(RECOVERY_VAL)
        vssd = inst_to_mof(inst)

        ret = service.ModifySystemSettings(SystemSettings=vssd) 
        curr_cim_rev, changeset = get_provider_version(options.virt, options.ip)
        if curr_cim_rev >= libvirt_modify_setting_changes:
            if ret[0] != 0:
                logger.error("Failed to modify dom: %s", default_dom)
                cleanup_env(options.ip, cxml)
                return FAIL

        if case == "start":
            #This should be replaced with a RSC to shutdownt he guest
            cxml.destroy(options.ip)
            status, cs = poll_for_state_change(options.ip, options.virt, 
                                               default_dom, DEFINED_STATE)
            if status != PASS:
                logger.error("Failed to destroy %s", default_dom)
                cleanup_env(options.ip, cxml)
                return FAIL

        status, inst = get_vssd(options.ip, options.virt, False)
        if status != PASS:
            logger.error("Failed to get the VSSD instance for %s", default_dom)
            cleanup_env(options.ip, cxml)
            return FAIL

        if inst.AutomaticRecoveryAction != RECOVERY_VAL:
            logger.error("%s not updated properly.", default_dom)
            logger.error("Exp AutomaticRecoveryAction=%d, got %d", RECOVERY_VAL,
                         inst.AutomaticRecoveryAction)
            cleanup_env(options.ip, cxml)
            curr_cim_rev, changeset = get_provider_version(options.virt, options.ip)
            if curr_cim_rev <= libvirt_f9_revision and options.virt == "KVM":
                return XFAIL_RC(f9_bug)

            if options.virt == "LXC":
                return XFAIL_RC(bug)
            return FAIL 

    cleanup_env(options.ip, cxml)

    return PASS 

if __name__ == "__main__":
    sys.exit(main())
 
