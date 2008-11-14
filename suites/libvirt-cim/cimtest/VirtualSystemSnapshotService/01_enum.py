#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Deepti B.Kalakeri <dkalaker@in.ibm.com>
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
#                                                         Date: 25-03-2008
import sys
from XenKvmLib import enumclass
from CimTest.Globals import CIM_ERROR_ENUMERATE, logger
from CimTest.ReturnCodes import PASS, FAIL
from XenKvmLib.const import do_main
from XenKvmLib.classes import get_typed_class
from XenKvmLib.common_util import get_host_info

def print_error(fieldname, ret_value, exp_value):
    logger.error("%s Mismatch", fieldname)
    logger.error("Returned %s instead of %s", ret_value, exp_value)

sup_types = ['Xen', 'KVM', 'XenFV', 'LXC']
@do_main(sup_types)
def main():
    options = main.options
    # Expected results from enumeration
    cn     =  get_typed_class(options.virt, "VirtualSystemSnapshotService")
    Name   = 'SnapshotService'
    status, host_inst = get_host_info(options.ip, options.virt)
    if status != PASS:
        return status

    classname = host_inst.CreationClassName
    host_name = host_inst.Name

    try:
        vs_sservice = enumclass.EnumNames(options.ip, cn)
    except Exception, detail:
        logger.error(CIM_ERROR_ENUMERATE, cn)
        logger.error("Exception: %s", detail)
        return FAIL

    if len(vs_sservice) != 1:
        logger.error("%s return %i instances, excepted only 1 instance", cn, len(vs_sservice))
        return FAIL
    verify_vs_sservice = vs_sservice[0]

    if verify_vs_sservice['CreationClassName'] != cn:
        print_error('CreationClassName', verify_vs_sservice['CreationClassName'], cn)
        return FAIL

    if verify_vs_sservice['Name'] != Name:
        print_error('Name', verify_vs_sservice['Name'], Name)
        return FAIL

    if verify_vs_sservice['SystemName'] != host_name:
        print_error('SystemName', verify_vs_sservice['SystemName'], host_name)
        return FAIL

    if verify_vs_sservice['SystemCreationClassName'] != classname:
        print_error('SystemCreationClassName', verify_vs_sservice['SystemCreationClassName'], classname)
        return FAIL

    return PASS
if __name__ == "__main__":
    sys.exit(main())
