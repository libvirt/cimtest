#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Kaitlin Rupert <karupert@us.ibm.com>
#    Veerendra Chandrappa <vechandr@in.ibm.com>
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

# This tc is used to verify the classname, InstanceID are  appropriately set for
# the Logical Devices of a domU when verified using the Xen_SettingsDefineState
# association.
# Date : 29-11-2007

import sys
from VirtLib import utils
from XenKvmLib import vxml
from XenKvmLib import assoc
from XenKvmLib import devices
from XenKvmLib.classes import get_typed_class
from XenKvmLib.const import CIM_REV
from CimTest import Globals
from CimTest.Globals import do_main
from CimTest.ReturnCodes import PASS, FAIL 

sup_types = ['Xen', 'KVM', 'XenFV', 'LXC']

test_dom = "domu1"
test_mac = "00:11:22:33:44:aa"
test_vcpus = 1
proc_instid_rev = 590


def print_error(cn, detail):
    Globals.logger.error(Globals.CIM_ERROR_GETINSTANCE, cn)
    Globals.logger.error("Exception: %s", detail)

def get_keys(baseccn, device_id, basesccn, virt):
    id = "%s/%s" % (test_dom, device_id)

    key_list = { 'DeviceID' : id,
                 'CreationClassName' : get_typed_class(virt, baseccn),
                 'SystemName' : test_dom,
                 'SystemCreationClassName' : get_typed_class(virt, basesccn)
               }

    return key_list

@do_main(sup_types)
def main():
    options = main.options
    status = PASS
    idx = 0

    if options.virt == 'Xen':
        test_disk = 'xvda'
    else:
        test_disk = 'hda'
    virt_xml = vxml.get_class(options.virt)
    if options.virt == 'LXC':
        cxml = virt_xml(test_dom)
        cn_id = {'Memory' : 'mem'}
    else:
        cxml = virt_xml(test_dom, vcpus = test_vcpus, mac = test_mac, 
                        disk = test_disk)
        cn_id = {
                'LogicalDisk' : test_disk,
                'Memory'      : 'mem',
                'NetworkPort' : test_mac,
                'Processor'   : test_vcpus -1 }


    ret = cxml.create(options.ip)
    if not ret:
        Globals.logger.error("Failed to Create the dom: %s", test_dom)
        return FAIL 


    devlist = {}
    logelelst = {}
    exp_inst_id_val = {}
    for cn in cn_id.keys():
        key_list = get_keys(cn, cn_id[cn], 'ComputerSystem', options.virt)

        if CIM_REV >= proc_instid_rev and cn == 'Processor':
            exp_inst_id_val[cn] = "%s/%s" % (test_dom, "proc") 
        else:
            exp_inst_id_val[cn] = key_list['DeviceID']

        try:
            dev_class = devices.get_class(get_typed_class(options.virt, cn))
            devlist[cn] = dev_class(options.ip, key_list)
            logelelst[cn] = devlist[cn].DeviceID
        except Exception, detail:
            print_error(cn, detail)
            cxml.destroy(options.ip)
            cxml.undefine(options.ip)
            return FAIL
    sccn = get_typed_class(options.virt, 'ComputerSystem')
    for cn in logelelst.keys():
        try:
            ccn = get_typed_class(options.virt, cn)
            assoc_info = assoc.AssociatorNames(options.ip, 
                                               'SettingsDefineState',
                                               cn, virt=options.virt,
                                               DeviceID = logelelst[cn],
                                               CreationClassName = ccn,
                                               SystemName = test_dom,
                                               SystemCreationClassName = sccn)

            if len(assoc_info) != 1:
                Globals.logger.error("Returned %i device instances for '%s'",
                                     len(assoc_info), test_dom)
                status = FAIL
                break

            if assoc_info[0]['InstanceID'] !=  exp_inst_id_val[cn]:
                Globals.logger.error("InstanceID Mismatch")
                Globals.logger.error("Returned %s instead of %s" \
                        % (assoc_info[0]['InstanceID'], exp_inst_id_val[cn]))
                status = FAIL

            if status != PASS:
                break

        except Exception, detail:
            Globals.logger.error(Globals.CIM_ERROR_ASSOCIATORS, sds_classname)
            Globals.logger.error("Exception: %s", detail)
            status = FAIL

    cxml.destroy(options.ip)
    cxml.undefine(options.ip)
    return status
    
if __name__ == "__main__":
    sys.exit(main())

