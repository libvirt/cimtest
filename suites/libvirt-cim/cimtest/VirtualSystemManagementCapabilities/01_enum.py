#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Guolian Yun <yunguol@cn.ibm.com>
#    Kaitlin Rupert <karupert@us.ibm.com>
#    Zhengang Li <lizg@cn.ibm.com>
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
from XenKvmLib.classes import get_typed_class

sup_types=['Xen', 'KVM', 'XenFV']

@do_main(sup_types)
def main():
    options = main.options
    Globals.log_param()

    try:
        key_list = ["InstanceID"]
        vsmc = enumclass.enumerate(options.ip,
                                   "VirtualSystemManagementCapabilities",
                                   key_list,
                                   options.virt)
    except Exception:
        Globals.logger.error(Globals.CIM_ERROR_ENUMERATE, 
                             get_typed_class(options.virt, 'VirtualSystemManagementCapabilities'))
        return 1
    
    if len(vsmc) != 1:
        Globals.logger.error("VirtualSystemManagementCapabilities return %i instance, excepted only 1" % len(vsmc))
        return 1
    if vsmc[0].InstanceID != "ManagementCapabilities":
        Globals.logger.error( "error result of enum VirtualSystemManagementCapabilities")
        return 1


if __name__ == "__main__":
    sys.exit(main())
