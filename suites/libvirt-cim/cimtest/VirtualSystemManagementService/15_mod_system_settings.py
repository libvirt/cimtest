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
from XenKvmLib.const import do_main, CIM_DISABLE
from XenKvmLib.classes import get_typed_class, inst_to_mof
from XenKvmLib.enumclass import GetInstance 
from XenKvmLib.common_util import poll_for_state_change 
from XenKvmLib.const import get_provider_version
from XenKvmLib.xm_virt_util import domain_list, active_domain_list, \
                                   destroy_domain

sup_types = ['Xen', 'KVM', 'XenFV', 'LXC']
default_dom = 'rstest_domain'
cpu = 2
RECOVERY_VAL = 3
DEFINED_STATE = 3
bug = "00008"
f9_bug = "00010"
libvirt_f9_revision=613
libvirt_modify_setting_changes = 694
disable_change_rev = 945

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

def power_down_guest(ip, virt, dom, cxml):
    rev, changeset = get_provider_version(virt, ip)

    if rev < disable_change_rev and virt == "KVM":
        rc = destroy_domain(ip, dom, virt)
        if rc != 0:
            return FAIL
    else:
        status = cxml.cim_disable(ip)
        if status != PASS:
            logger.error("Failed to disable %s", dom)
            return FAIL

    status, cs = poll_for_state_change(ip, virt, dom, CIM_DISABLE)
    if status != PASS:
        logger.error("Failed to destroy %s", dom)
        return FAIL

    return PASS

@do_main(sup_types)
def main():
    options = main.options 

    test_cases = ["define", "start"]
    cxml = vxml.get_class(options.virt)(default_dom, vcpus=cpu)
    service = vsms.get_vsms_class(options.virt)(options.ip)

    try:

        for case in test_cases:
            #Each time through, define guest using a default XML
            cxml.undefine(options.ip)
            cxml = vxml.get_class(options.virt)(default_dom, vcpus=cpu)
            ret = cxml.cim_define(options.ip)
            if not ret:
                raise Exception("Failed to define the dom: %s" % default_dom)

            if case == "start":
                ret = cxml.cim_start(options.ip)
                if ret:
                    raise Exception("Failed to start %s" % default_dom)

            status, inst = get_vssd(options.ip, options.virt, True)
            if status != PASS:
                raise Expcetion("Failed to get the VSSD instance for %s" % \
                                default_dom)

            val = pywbem.cim_types.Uint16(RECOVERY_VAL)
            inst['AutomaticRecoveryAction'] = val
            vssd = inst_to_mof(inst)

            ret = service.ModifySystemSettings(SystemSettings=vssd) 
            curr_cim_rev, changeset = get_provider_version(options.virt, 
                                                           options.ip)
            if curr_cim_rev >= libvirt_modify_setting_changes:
                if ret[0] != 0:
                    raise Exception("Failed to modify dom: %s" % default_dom)

            if case == "start":
                status = power_down_guest(options.ip, options.virt, default_dom,
                                          cxml)
                if status != PASS:
                        raise Exception("Unable to disable %s" % default_dom)

            status, inst = get_vssd(options.ip, options.virt, False)
            if status != PASS:
                raise Exception("Failed to get the VSSD instance for %s" % \
                                default_dom)

            if inst.AutomaticRecoveryAction != RECOVERY_VAL:
                logger.error("Exp AutomaticRecoveryAction=%d, got %d", 
                             RECOVERY_VAL, inst.AutomaticRecoveryAction)
                raise Exception("%s not updated properly" % default_dom)

            status = PASS

    except Exception, details:
        logger.error(details)
        status = FAIL

    defined_domains = domain_list(options.ip, options.virt)
    if default_dom in defined_domains:
        cxml.cim_destroy(options.ip)

    curr_cim_rev, changeset = get_provider_version(options.virt, options.ip)
    if curr_cim_rev <= libvirt_f9_revision and options.virt == "KVM":
        return XFAIL_RC(f9_bug)

    if options.virt == "LXC":
        return XFAIL_RC(bug)

    return status 

if __name__ == "__main__":
    sys.exit(main())
 
