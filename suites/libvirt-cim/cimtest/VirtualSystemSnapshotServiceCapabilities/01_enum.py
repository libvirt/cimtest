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
#                                                         Date: 24-03-2008
import sys
from XenKvmLib import enumclass
from CimTest.Globals import log_param, CIM_ERROR_ENUMERATE, logger
from CimTest.ReturnCodes import PASS, FAIL
from CimTest.Globals import do_main, platform_sup
from XenKvmLib.classes import get_typed_class

def print_error(fieldname, ret_value, exp_value):
    logger.error("%s Mismatch", fieldname)
    logger.error("Returned %s instead of %s", ret_value, exp_value)

@do_main(platform_sup)
def main():
    options = main.options
    log_param()
    # Expected results from enumeration
    cn       =  get_typed_class(options.virt, "VirtualSystemSnapshotServiceCapabilities")
    instid   = 'SnapshotCapabilities'

    try:
        vs_sservicecap = enumclass.enumerate_inst(options.ip,
                                                  "VirtualSystemSnapshotServiceCapabilities",
                                                  options.virt)
    except Exception, detail:
        logger.error(CIM_ERROR_ENUMERATE, cn)
        logger.error("Exception: %s", detail)
        return FAIL

    if len(vs_sservicecap) != 1:
        logger.error("%s return %i instances, excepted only 1 instance", cn, len(vs_sservicecap))
        return FAIL
    verify_vs_sservicecap = vs_sservicecap[0]
    if verify_vs_sservicecap.classname != cn:
        print_error('ClassName', verify_vs_sservicecap.classname, cn)
        return FAIL

    if verify_vs_sservicecap['InstanceID'] != instid:
        print_error('InstanceID', verify_vs_sservicecap['InstanceID'], instid)
        return FAIL

    return PASS
if __name__ == "__main__":
    sys.exit(main())
