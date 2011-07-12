#!/usr/bin/env python
#
# Copyright 2011 IBM Corp.
#
# Authors:
#    Eduardo Lima (Etrunko) <eblima@br.ibm.com>
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
# CIMTest Filter Lists Enumerate
#

import sys
import helper

from CimTest.ReturnCodes import PASS, FAIL
from CimTest.Globals import logger
from XenKvmLib.const import do_main

sup_types = ["KVM",]

@do_main(sup_types)
def main():
    options = main.options

    _test = helper.FilterListTest(options.ip, options.virt)

    # Fetch current filters with libvirt
    libvirt_filters = _test.libvirt_filter_lists()
    if not libvirt_filters:
        return FAIL

    logger.info("libvirt filters:\n%s", libvirt_filters)

    # Fetch current filters with libvirt-cim
    cim_filters = _test.cim_filter_lists()
    if not cim_filters:
        # TODO: Add some filters of our own
        return FAIL

    logger.info("libvirt-cim filters:\n%s", cim_filters)

    # Compare results
    if len(libvirt_filters) != len(cim_filters):
        logger.error("CIM filters list length is different than libvirt filters list")
        return FAIL

    for f in libvirt_filters:
        if f not in cim_filters:
            logger.error("Filter %s, not found in CIM filters list", f)
            return FAIL

    return PASS
# main

if __name__ == "__main__":
    sys.exit(main())
