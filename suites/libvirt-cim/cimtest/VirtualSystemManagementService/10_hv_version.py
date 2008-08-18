#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Dan Smith <danms@us.ibm.com>
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
from VirtLib import live
from XenKvmLib import vsms
from CimTest.Globals import do_main
from CimTest.Globals import logger
from CimTest.ReturnCodes import FAIL, PASS, XFAIL_RC

sup_types = ['Xen', 'XenFV', 'KVM', 'LXC']
bug_libvirt = "00006"

@do_main(sup_types)
def main():
    options = main.options

    try:
        service = vsms.enumerate_instances(options.ip, options.virt)[0]
    except Exception, details:
        service = None

    if not service:
        logger.error("Did not find VSMS instance")
        logger.error(details)
        return FAIL

    try:
        cim_ver = service["Caption"]
        local_ver = live.get_hv_ver(options.ip, options.virt)

        if cim_ver != local_ver:
            logger.error("CIM says version is `%s', but libvirt says `%s'" \
                         % (cim_ver, local_ver))
            if options.virt == 'LXC':
                return XFAIL_RC(bug_libvirt)
            else:
                return FAIL
        else:
            logger.info("Verified %s == %s" % (cim_ver, local_ver))
    except Exception, details:
        logger.error(details)
        return FAIL

    return PASS

if __name__ == "__main__":
    sys.exit(main())
