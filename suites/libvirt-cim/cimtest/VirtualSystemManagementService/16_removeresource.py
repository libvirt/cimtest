#!/usr/bin/python
#
# Copyright 2009 IBM Corp.
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
from XenKvmLib.vsms import get_vsms_class
from XenKvmLib.vxml import get_class
from XenKvmLib.classes import get_typed_class
from XenKvmLib.assoc import AssociatorNames
from CimTest.Globals import logger
from XenKvmLib.const import do_main, get_provider_version
from CimTest.ReturnCodes import FAIL, PASS, SKIP, XFAIL_RC

libvirt_bug = '00014'
sup_types = ['Xen', 'KVM', 'XenFV']
default_dom = 'domain'
rem_res_err_rev_start = 779
rem_res_err_rev_end = 828
nmac = '00:11:22:33:44:55'

@do_main(sup_types)
def main():
    options = main.options

    if options.virt == 'KVM':
        nddev = 'hdb'
    else:
        nddev = 'xvdb'

    cxml = get_class(options.virt)(default_dom, disk=nddev, mac=nmac)
    ret = cxml.cim_define(options.ip)
    if not ret:
        logger.error("Failed to define the dom: %s", default_dom)
        return FAIL
   
    try:
        # Get system devices through SystemDevice assocation
        sd_classname = get_typed_class(options.virt, 'SystemDevice')
        cs_classname = get_typed_class(options.virt, 'ComputerSystem')

        devs = AssociatorNames(options.ip, sd_classname, cs_classname,
                               Name=default_dom, CreationClassName=cs_classname)
        
        if len(devs) == 0:
            raise Exception("No devices returned")

        # Get RASD instances through SettingsDefineState
        sds_classname = get_typed_class(options.virt, 'SettingsDefineState')
        mem = get_typed_class(options.virt, 'Memory')
        proc = get_typed_class(options.virt, 'Processor')
        input = get_typed_class(options.virt, 'PointingDevice')
        dev_not_rem = [mem, proc, input] 
                
        service = get_vsms_class(options.virt)(options.ip)
        for dev in devs:
            if dev['CreationClassName'] in dev_not_rem:
                continue
            ccn = dev['CreationClassName']
            sccn = dev['SystemCreationClassName']
            rasd = AssociatorNames(options.ip, sds_classname, ccn,
                                   DeviceID = dev['DeviceID'],
                                   CreationClassName = ccn,
                                   SystemName = dev['SystemName'],
                                   SystemCreationClassName = sccn)
            if len(rasd) != 1:
                raise Exception("%i RASD insts for %s" 
                                % (len(rasd), dev['DeviceID']))
            # Invoke RemoveResourceSettings() to remove resource
            ret = service.RemoveResourceSettings(ResourceSettings=[rasd[0]])
            if ret[0] != 0:
                raise Exception("RemoveResourceSettings() returned %d " + 
                                "removing %s" % (ret[0], rasd[0]))
    except Exception, details:       
        logger.error(details)
        cxml.undefine(options.ip)
        input = get_typed_class(options.virt, 'PointingDevice')
        if ccn == input:
            return XFAIL_RC(libvirt_bug)
        return FAIL

    cxml.dumpxml(options.ip) 
    device = cxml.get_value_xpath('/domain/@devices')
    curr_cim_rev, changeset = get_provider_version(options.virt, options.ip)

    if device == None:
        status = PASS
    elif device != None and curr_cim_rev >= rem_res_err_rev_start and \
        curr_cim_rev < rem_res_err_rev_end:
        status = SKIP
    else:
        logger.error('The devices are not removed successfully')
        status = FAIL

    cxml.undefine(options.ip)
    return status

if __name__ == "__main__":
    sys.exit(main())
