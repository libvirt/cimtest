#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Guolian Yun <yunguol@cn.ibm.com>
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
from XenKvmLib.enumclass import EnumInstances
from XenKvmLib.classes import get_typed_class
from XenKvmLib.common_util import parse_instance_id
from XenKvmLib.const import do_main
from XenKvmLib.vxml import get_class
from CimTest.ReturnCodes import PASS, FAIL
from CimTest.Globals import logger
from XenKvmLib.const import get_provider_version

SUPPORTED_TYPES = ['KVM']
default_dom = 'test_domain'
libvirt_em_type_changeset = 737

@do_main(SUPPORTED_TYPES)
def main():
    status = FAIL
    options = main.options
    curr_cim_rev, changeset = get_provider_version(options.virt, options.ip)
    if curr_cim_rev < libvirt_em_type_changeset:
        return SKIP

    emu_types = [0, 1]
    try:
        for exp_emu_type in emu_types:
            cxml = get_class(options.virt)(default_dom, emu_type=exp_emu_type)
            ret = cxml.cim_define(options.ip)
            if not ret:
                logger.error("Failed to call DefineSystem()")
                return FAIL
    
            drasd= get_typed_class(options.virt,'DiskResourceAllocationSettingData')
        
            drasd_list = EnumInstances(options.ip, drasd, ret_cim_inst=True)
            if len(drasd_list) < 1:
                raise Exception("%s returned %i instances, expected at least 1" \
                                 %(drasd, len(drasd_list)))

            found_rasd = None
            for rasd in drasd_list:
                guest, dev, status = parse_instance_id(rasd['InstanceID'])
                if status != PASS:
                    raise Exception("Unable to parse InstanceID: %s" \
                                    % rasd['InstanceID'])
                if guest == default_dom:
                    if rasd['EmulatedType'] == exp_emu_type:
                        found_rasd = rasd
                        status = PASS
                        break
                    else:
                        raise Exception("EmulatedType Mismatch: got %d,"
                                        "expected %d" %(rasd['EmulatedType'], 
                                         exp_emu_type))

            if found_rasd is None:
                raise Exception("DiskRASD for defined dom was not found")
    except Exception, detail:
        logger.error("Exception: %s", detail)           
        status = FAIL

    cxml.undefine(options.ip)
           
    return status

if __name__ == "__main__":
    sys.exit(main())
