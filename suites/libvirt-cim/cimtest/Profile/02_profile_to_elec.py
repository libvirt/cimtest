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
import pywbem
from XenKvmLib import enumclass 
from XenKvmLib.assoc import Associators 
from XenKvmLib.common_util import create_using_definesystem
from XenKvmLib.test_doms import undefine_test_domain, destroy_and_undefine_all
from CimTest import Globals 
from CimTest.Globals import log_param, logger, CIM_ERROR_ENUMERATE, CIM_ERROR_ASSOCIATORNAMES 
from CimTest.Globals import do_main
from CimTest.ReturnCodes import PASS, FAIL

sup_types = ['Xen']

test_dom = "domguest"

def setup_env(server):
    rc = -1
    status = PASS

    try:
        destroy_and_undefine_all(server)
        rc = create_using_definesystem(test_dom, server)

        if rc != 0:
            logger.error("Unable define domain %s using DefineSystem() %s" \
                         % test_dom)
            status = FAIL

    except Exception, detail:
        logger.error("Exception defining domain %s" % test_dom)
        logger.error("Exception: %s", detail)
        status = FAIL

    return status

def print_err(err, detail, cn):
     logger.error(err % cn)
     logger.error("Exception: %s", detail)

def get_inst_from_list(server, cn, qcn, list, filter, exp_val):
     status = PASS
     ret = -1
     inst = None
 
     if len(list) < 1:
         logger.error("%s returned %i %s objects" % (qcn, len(list), cn))
         return FAIL, None
 
     for inst in list:
         if inst[filter['key']] == exp_val:
             ret = PASS
             break;

     if ret != PASS:
         status = FAIL
         logger.error("%s with %s was not returned" % (cn, exp_val))
 
     return PASS, inst 

def get_profile(server):
    registeredname = 'Virtual System Profile'
    cn = 'Xen_RegisteredProfile'
    status = PASS 
    profile = None

    try:
        proflist = enumclass.enumerate_inst(server,
                                            enumclass.Xen_RegisteredProfile)

        filter =  {"key" : "RegisteredName"}
        status, profile = get_inst_from_list(server, 
                                             cn, 
                                             cn, 
                                             proflist, 
                                             filter,
                                             registeredname)

    except Exception, detail:
        print_err(CIM_ERROR_ENUMERATE, detail, cn)
        status = FAIL 

    return status, profile

def get_cs(server, profile):
    cn = 'Xen_RegisteredProfile'
    an = 'Xen_ElementConformsToProfile'
    status = PASS
    cs = None

    try:
        assoc_info = Associators(server,
                                 an,
                                 cn,
                                 InstanceID = profile['InstanceID'])

        cn = 'Xen_ComputerSystem'
        filter =  {"key" : "Name"}
        status, cs = get_inst_from_list(server, 
                                        cn, 
                                        an, 
                                        assoc_info, 
                                        filter,
                                        test_dom)

    except Exception, detail:
        print_err(CIM_ERROR_ASSOCIATORNAMES, detail, cn)
        status = FAIL

    return status, cs 

def get_elec(server, cs):
    cn = 'Xen_ComputerSystem'
    an = 'Xen_ElementCapabilities'
    status = FAIL
    elec = None

    ccn = cs['CreationClassName']
    try:
        assoc_info = Associators(server,
                                 an,
                                 cn,
                                 Name = cs['Name'],
                                 CreationClassName = ccn)

        cn = 'Xen_EnabledLogicalElementCapabilities'
        filter =  {"key" : "InstanceID"}
        status, elec = get_inst_from_list(server, 
                                          cn, 
                                          an, 
                                          assoc_info, 
                                          filter,
                                          test_dom)

    except Exception, detail:
        print_err(CIM_ERROR_ASSOCIATORNAMES, detail, cn)
        status = FAIL

    return status, elec

@do_main(sup_types)
def main():
    options = main.options
    log_param()

    status = PASS 

    status = setup_env(options.ip)
    if status != PASS:
        return status

    prev_namespace = Globals.CIM_NS
    Globals.CIM_NS = 'root/interop'

    status, prof = get_profile(options.ip)
    if status != PASS or prof == None:
        return status 

    status, cs = get_cs(options.ip, prof)
    if status != PASS or cs == None:
        return status 

    Globals.CIM_NS = prev_namespace

    status, elec = get_elec(options.ip, cs)
    if status != PASS or elec == None:
        return status 

    return status 


if __name__ == "__main__":
    sys.exit(main())
