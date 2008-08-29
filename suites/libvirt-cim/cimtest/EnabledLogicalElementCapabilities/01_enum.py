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
from XenKvmLib.classes import get_typed_class
from CimTest import Globals
from XenKvmLib.const import do_main
from VirtLib import live
from VirtLib import utils

sup_types = ['Xen', 'KVM', 'XenFV', 'LXC']

@do_main(sup_types)
def main():
    options = main.options
    
    try:
        key_list = ["InstanceID"]
        elec = enumclass.enumerate(options.ip,
                                   "EnabledLogicalElementCapabilities",
                                   key_list,
                                   options.virt)
    except Exception:
        Globals.logger.error(Globals.CIM_ERROR_ENUMERATE, \
                             get_typed_class(options.virt, 'EnabledLogicalElementCapabilities'))
        return 1

     
    names = live.domain_list(options.ip, options.virt)
    
    if len(elec) != len(names):
        Globals.logger.error("Get domain list error, the number of domains is not equal")
        return 1
    else:
        for i in range(0, len(elec)):
            if elec[i].InstanceID not in names:
                Globals.logger.error("enumrate EnabledLogicalElementCapabilities result error")
                return 1


if __name__ == "__main__":
    sys.exit(main())
