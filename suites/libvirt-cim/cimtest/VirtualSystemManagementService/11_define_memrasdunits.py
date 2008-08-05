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
from XenKvmLib.test_doms import undefine_test_domain
from XenKvmLib.common_util import create_using_definesystem
from XenKvmLib import rasd
from XenKvmLib.classes import get_typed_class
from XenKvmLib import enumclass
from CimTest.Globals import do_main
from CimTest.Globals import logger
from CimTest.ReturnCodes import FAIL, PASS

sup_types = ['Xen', 'XenFV', 'KVM']
default_dom = "memrasd_test"

mem_bytes = 2 << 30

values = [
    ("Bytes",      0),
    ("KiloBytes", 10),
    ("MegaBytes", 20),
    ("GigaBytes", 30),
    ]

def try_define(options, vssd, units, value):
    mrasd_class = vsms.get_masd_class(options.virt)
    mrasd = mrasd_class(megabytes=value, mallocunits=units, 
                        name=default_dom)

    params = { 
        "vssd" : vssd.mof(),
        "rasd" : [mrasd.mof()],
        }

    logger.info("Defining with %s = %i" % (units, value))
    rc = create_using_definesystem(default_dom,
                                   options.ip,
                                   params=params,
                                   virt=options.virt)
                                   
    if rc != PASS:
        logger.error("DefineSystem (%s) failed" % units)
        return False

    return True

def check_value(options):
    mrasd_cn = get_typed_class(options.virt, rasd.masd_cn)
    rasds = enumclass.enumerate_inst(options.ip, mrasd_cn, options.virt)

    the_rasd = None
    mem_kb = mem_bytes >> 10

    for _rasd in rasds:
        if _rasd["InstanceID"] == "%s/mem" % default_dom:
            the_rasd = _rasd
    
    if not the_rasd:
        logger.error("Did not find test RASD on server")
        return False

    if the_rasd["AllocationUnits"] != "KiloBytes":
        logger.error("MRASD units are not kilobytes?")
        return False

    cim_kb = int(the_rasd["VirtualQuantity"])

    if cim_kb != mem_kb:
        logger.error("CIM reports %i KB instead of %i KB" % (cim_kb, mem_kb))
        return False

    logger.info("Verified %i KB" % mem_kb)

    return True


@do_main(sup_types)
def main():
    options = main.options

    vssd_class = vsms.get_vssd_class(options.virt)
    vssd = vssd_class(name=default_dom, virt=options.virt)

    status = PASS

    for units, shift in values:
        value = mem_bytes >> shift

        if not try_define(options, vssd, units, value):
            status = FAIL
            break

        if not check_value(options):
            status = FAIL
            break

        undefine_test_domain(default_dom, options.ip, virt=options.virt)

    undefine_test_domain(default_dom, options.ip, virt=options.virt)


    return status

if __name__ == "__main__":
    sys.exit(main())
