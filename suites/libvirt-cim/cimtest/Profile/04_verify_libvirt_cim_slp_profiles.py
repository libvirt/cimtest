#! /usr/bin/python
#
# Copyright 2009 IBM Corp.
#
# Authors:
#    Deepti B. Kalakeri <dkalaker@in.ibm.com>
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
# The following test case is used to verify the profiles registered by 
# Libvirt-CIM  are advertised via slp tool.
#  
#                                          Date : 20-10-2009 

import sys
import os
import string
from sets import Set
from socket import gethostbyaddr, gethostname, gethostbyname
from VirtLib.utils import run_remote
from XenKvmLib import enumclass
from XenKvmLib.classes import get_typed_class
from CimTest import Globals
from CimTest.Globals import logger
from XenKvmLib.const import do_main
from CimTest.ReturnCodes import PASS, FAIL, SKIP

sup_types = ['Xen', 'KVM', 'XenFV', 'LXC']
def  get_slp_info(server):

    cmd = "slptool help"
    rc, out = run_remote(server, cmd)
    if rc != 0:
        # Check if slptool exist in non-standard path
        cmd = "whereis slptool"
        rc, out =  run_remote(server, cmd)
        slp_path = out.split(":")
        if slp_path[1] == '':
            logger.error("SLP tool does not exist on the machine ")
            return SKIP

    logger.info("Slp tool found on the machine ....")

    # The test is written to work with Pegasus for now.
    # In future we can include sfcb support as well
    # When sfcb support will be planned then replace the following check 
    # with check_cimom() fn of common_util.py lib
    cmd = "ps -ef | grep -v grep | grep cimserver"
    rc, out = run_remote(server, cmd)
    if rc != 0:
        logger.info("cimserver not found on '%s'", server)
        logger.info("Test not supported for sfcb yet ... hence skipping")
        return SKIP

    cmd = "cimconfig -l -p | grep slp"
    rc, out = run_remote(server, cmd)
    if rc != 0:
        logger.error("SLP is not enabled for the cimserver on '%s'", server)
        return SKIP

    return PASS

def get_slp_attrs(server):
    slp_attrs = None

    cmd = "slptool findattrs service:wbem:http://%s:5988" % server
    rc, slp_attrs = run_remote(server, cmd)
    if len(slp_attrs) != 0:
        return PASS, slp_attrs

    return FAIL, slp_attrs

def filter_reg_name_from_slp(slp_attrs):
    slp_profile_list = []

    for line in slp_attrs.split('\n'):
        lines = line.split("RegisteredProfilesSupported")
        dmtf_profiles = lines[1].split("DMTF")
        for profile in dmtf_profiles:
            tmp_prof =  profile.rsplit(":", 1)
            if len(tmp_prof) < 2:
                return []

            temp_reg_ele =  tmp_prof[1].rstrip(",")
            reg_prof_name = temp_reg_ele.rstrip(")")
            slp_profile_list.append(reg_prof_name)

    slp_profile_list = Set(slp_profile_list)

    return slp_profile_list

def get_libvirt_cim_profile_info(server, virt):
    libvirt_cim_reg_list = None
    status = FAIL
    prev_namespace = Globals.CIM_NS
    Globals.CIM_NS = 'root/interop'
    cn = get_typed_class(virt, 'RegisteredProfile')

    try: 
        proflist = enumclass.EnumInstances(server, cn)
    except Exception, detail:
        logger.error(CIM_ERROR_ENUMERATE, get_typed_class(virt, cn))
        logger.error("Exception: %s", detail)
        Globals.CIM_NS = prev_namespace
        return status, libvirt_cim_reg_list
    
    Globals.CIM_NS = prev_namespace

    libvirt_cim_reg_list = Set([str(x.RegisteredName) for x in proflist])
    if len(libvirt_cim_reg_list) != 0:
        status = PASS
        
    return status, libvirt_cim_reg_list
   

@do_main(sup_types)
def main():
    options = main.options
    server = options.ip
    virt = options.virt
    status = FAIL

    status = get_slp_info(server)
    if status != PASS:
        return status 

    # Making sure that the server information passed is 
    # hostname or ip address
    if server == "localhost":
        host = gethostname()
        ip_addr = gethostbyname(host)
    else:
        ip_addr = gethostbyaddr(server)[2][0]

    status, slp_attrs = get_slp_attrs(ip_addr)
    if status != PASS:
        logger.error("Failed to get slp attributes on %s", server)
        return status

    slp_profile_list = filter_reg_name_from_slp(slp_attrs)

    if len(slp_profile_list) < 1:
        logger.error("Failed to get profile list on %s", server)
        return status

    status, libvirt_cim_reg_list = get_libvirt_cim_profile_info(server, virt)
    if status != PASS:
        logger.error("Failed to enumerate profile information on %s", server)
        return status

    # Make sure all the Libvirt-CIM profiles are advertised via slp
    if (libvirt_cim_reg_list) <= (slp_profile_list):
        logger.info("Successfully verified the Libvirt-CIM profiles")
        return PASS

    logger.error("Mismatch in the profiles registered")
    logger.error("Slp returned profile --> %s,\n Libvirt-CIM expected "
                 "profiles %s", slp_profile_list, libvirt_cim_reg_list)
    return FAIL

if __name__=="__main__":
    sys.exit(main())

