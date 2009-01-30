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
from pywbem.cim_types import Uint64
from XenKvmLib.classes import get_typed_class, inst_to_mof
from XenKvmLib import enumclass
from XenKvmLib.const import do_main
from CimTest.Globals import logger
from CimTest.ReturnCodes import FAIL, PASS
from XenKvmLib.vxml import get_class
from XenKvmLib.rasd import get_default_rasds

sup_types = ['Xen', 'XenFV', 'KVM']
default_dom = "memrasd_test"

mem_bytes = 2 << 30

values = [
    ("Bytes",      0),
    ("KiloBytes", 10),
    ("MegaBytes", 20),
    ("GigaBytes", 30),
    ]

def try_define(options, units, value, cxml):
    mrasd_cn = get_typed_class(options.virt, "MemResourceAllocationSettingData")

    rasds = get_default_rasds(options.ip, options.virt)

    rasd_list = {} 

    for rasd in rasds:
        if rasd.classname == mrasd_cn:
            rasd['VirtualQuantity'] = Uint64(value)
            rasd['AllocationUnits'] = units 
            rasd_list[mrasd_cn] = inst_to_mof(rasd)
        else:
            rasd_list[rasd.classname] = None 

    if rasd_list[mrasd_cn] is None:
        logger.error("Unable to get template MemRASD")
        return FAIL 

    cxml.set_res_settings(rasd_list)

    logger.info("Defining with %s = %i", units, value)

    ret = cxml.cim_define(options.ip)
    if not ret:
        logger.error("DefineSystem with (%s) units failed" % units)
        return FAIL 

    return PASS 

def check_value(options):
    mrasd_cn = get_typed_class(options.virt, "MemResourceAllocationSettingData")
    rasds = enumclass.EnumInstances(options.ip, mrasd_cn, ret_cim_inst=True)

    the_rasd = None
    mem_kb = mem_bytes >> 10

    for _rasd in rasds:
        if _rasd["InstanceID"] == "%s/mem" % default_dom:
            the_rasd = _rasd
    
    if not the_rasd:
        logger.error("Did not find test RASD on server")
        return FAIL 

    if the_rasd["AllocationUnits"] != "KiloBytes":
        logger.error("MRASD units are not kilobytes?")
        return FAIL 

    cim_kb = int(the_rasd["VirtualQuantity"])

    if cim_kb != mem_kb:
        logger.error("CIM reports %i KB instead of %i KB" % (cim_kb, mem_kb))
        return FAIL 

    logger.info("Verified %i KB" % mem_kb)

    return PASS 


@do_main(sup_types)
def main():
    options = main.options

    cxml = get_class(options.virt)(default_dom)

    status = FAIL 
    guest_is_undefined = None 

    for units, shift in values:
        guest_is_undefined = False

        value = mem_bytes >> shift

        status = try_define(options, units, value, cxml)
        if status != PASS:
            break

        status = check_value(options)
        if status != PASS:
            break

        cxml.undefine(options.ip)
        guest_is_undefined = True

    if guest_is_undefined != True:
        cxml.undefine(options.ip)

    return status

if __name__ == "__main__":
    sys.exit(main())
