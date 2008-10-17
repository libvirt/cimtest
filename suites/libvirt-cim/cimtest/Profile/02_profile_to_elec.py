#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Deepti B. Kalakeri <dkalaker@in.ibm.com>
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

# This is a cross-provider testcase.  It traverses the following path: 

# RegisteredProfile ---ElementConformsToProfile--- ComputerSystem 
#   ---ElementCapabilities--- EnabledLogicElementCapabilities.

# Steps:
#  1. Create a guest.
#  2. Enumerate the RegisteredProfiles on the system.
#  3. Get the CIM instance of the "Virtual System" RegisteredProfile.
#  4. Using the ElementConformsToProfile association, get all of the 
#      ComputerSystem instances on the system.
#  5. Verify a ComputerSystem instance is returned for the created guest.
#  6. Using the ElementCapabilities association, get the 
#      EnabledLogicElementCapabilities instance that corresponds to the 
#      ComputerSystem instance of the guest.

import sys
from XenKvmLib import enumclass 
from XenKvmLib.assoc import Associators 
from XenKvmLib.vxml import get_class
from XenKvmLib.test_doms import destroy_and_undefine_all
from CimTest import Globals 
from CimTest.Globals import logger, CIM_ERROR_ENUMERATE, CIM_ERROR_ASSOCIATORNAMES 
from XenKvmLib.const import do_main
from CimTest.ReturnCodes import PASS, FAIL
from XenKvmLib.classes import get_typed_class

sup_types = ['Xen', 'XenFV', 'KVM']

test_dom = "domguest"

def setup_env(server, virt):
    rc = -1
    status = PASS
    csxml_info = None
    try:
        destroy_and_undefine_all(server)
        virt_xml = get_class(virt)
        csxml_info = virt_xml(test_dom)
        rc = csxml_info.cim_define(server)

        if not rc:
            logger.error("Unable define domain %s using DefineSystem() "  % test_dom)
            status = FAIL

    except Exception, detail:
        logger.error("Exception defining domain %s" % test_dom)
        logger.error("Exception: %s", detail)
        status = FAIL

    return status, csxml_info

def print_err(err, detail, cn):
    logger.error(err % cn)
    logger.error("Exception: %s", detail)

def get_expected_inst(cn, list, property, exp):
    try:
        for x in list:
            if x[property] == exp:
                return PASS, x
    except Exception:
        pass
    logger.error("%s with %s was not returned" % (cn, exp))
    return FAIL, None


def get_profile(server, virt):
    registeredname = 'Virtual System Profile'
    cn = get_typed_class(virt, 'RegisteredProfile')
    status = PASS 
    profile = None

    try:
        proflist = enumclass.EnumInstances(server, cn, ret_cim_inst=True)
        status, profile = get_expected_inst(cn, proflist, 'RegisteredName',
                                            registeredname)
    except Exception, detail:
        print_err(CIM_ERROR_ENUMERATE, detail, cn)
        status = FAIL 

    return status, profile

def get_cs(server, virt, profile):
    cn = get_typed_class(virt, 'RegisteredProfile')
    an = get_typed_class(virt, 'ElementConformsToProfile')
    status = PASS
    cs = None

    try:
        assoc_info = Associators(server,
                                 an,
                                 cn,
                                 InstanceID = profile['InstanceID'],
                                 virt=virt)

        cn = get_typed_class(virt, 'ComputerSystem')
        status, cs = get_expected_inst(cn, assoc_info, 'Name', test_dom)

    except Exception, detail:
        print_err(CIM_ERROR_ASSOCIATORNAMES, detail, cn)
        status = FAIL

    return status, cs 

def get_elec(server, virt, cs):
    cn = get_typed_class(virt, 'ComputerSystem')
    an = get_typed_class(virt, 'ElementCapabilities')
    status = FAIL
    elec = None

    ccn = cs['CreationClassName']
    try:
        assoc_info = Associators(server,
                                 an,
                                 cn,
                                 Name = cs['Name'],
                                 CreationClassName = ccn,
                                 virt=virt)
        cn = get_typed_class(virt, 'EnabledLogicalElementCapabilities')
        status, elec = get_expected_inst(cn, assoc_info, 'InstanceID', test_dom)

    except Exception, detail:
        print_err(CIM_ERROR_ASSOCIATORNAMES, detail, cn)
        status = FAIL
    return status, elec

@do_main(sup_types)
def main():
    options = main.options
    virt    = options.virt
    server  = options.ip

    status, csxml = setup_env(server, virt)
    if status != PASS:
        return status

    prev_namespace = Globals.CIM_NS
    Globals.CIM_NS = 'root/interop'

    status, prof = get_profile(server, virt)
    if status != PASS or prof == None:
        csxml.undefine(server)
        return FAIL

    status, cs = get_cs(server, virt, prof)
    if status != PASS or cs == None:
        csxml.undefine(server)
        return FAIL

    Globals.CIM_NS = prev_namespace

    status, elec = get_elec(server, virt, cs)
    if status != PASS or elec == None:
        status = FAIL

    csxml.undefine(server)
    return status 
if __name__ == "__main__":
    sys.exit(main())
