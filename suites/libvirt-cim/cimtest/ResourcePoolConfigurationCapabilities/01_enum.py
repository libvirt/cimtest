#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Guolian Yun <yunguol@cn.ibm.com>
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
from XenKvmLib import enumclass
from CimTest import Globals
from CimTest.Globals import do_main
from CimTest.ReturnCodes import PASS, FAIL

sup_types = ['Xen', 'XenFV', 'KVM', 'LXC']

@do_main(sup_types)
def main():
    options = main.options

    key_list = ["InstanceID"]
    try:
        rpcc = enumclass.enumerate(options.ip,
                                   "ResourcePoolConfigurationCapabilities",
                                   key_list,
                                   options.virt)
    except Exception:
        Globals.logger.error(Globals.CIM_ERROR_ENUMERATE, '%s_ResourcePoolConfigurationCapabilities' % options.virt)
        return FAIL
     
    if len(rpcc) != 1:
        Globals.logger.error("%s_ResourcePoolConfigurationCapabilities return %i instances, \
                             excepted only 1 instance" % (options.virt, len(rpcc)))
        return FAIL
    if rpcc[0].InstanceID != "RPCC":
        Globals.logger.error("error result of enum ResourcePoolConfigurationCapabilities")
        return FAIL

    return PASS

if __name__ == "__main__":
    sys.exit(main())
