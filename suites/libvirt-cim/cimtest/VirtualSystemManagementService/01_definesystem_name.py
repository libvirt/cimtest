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
import pywbem
from VirtLib import utils
from XenKvmLib.test_doms import undefine_test_domain
from XenKvmLib.common_util import create_using_definesystem
from CimTest.Globals import do_main
from CimTest.Globals import logger

SUPPORTED_TYPES = ['Xen', 'KVM', 'XenFV', 'LXC']
default_dom = 'test_domain'

@do_main(SUPPORTED_TYPES)
def main():
    options = main.options

    status = create_using_definesystem(default_dom, options.ip, 
                                       virt=options.virt)
    undefine_test_domain(default_dom, options.ip, 
                         virt=options.virt)

    return status

if __name__ == "__main__":
    sys.exit(main())

