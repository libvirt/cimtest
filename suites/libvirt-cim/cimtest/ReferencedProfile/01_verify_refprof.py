#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Deepti B. Kalakeri <deeptik@linux.vnet.ibm.com>
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
# The following test case is used to verify the ReferencedProfile provider. 
#
#Ex Command:
#-----------
# wbemcli ain -ac Xen_ReferencedProfile 'http://localhost:5988/root/interop:
# Xen_RegisteredProfile.InstanceID="CIM:DSP1057-VirtualSystem-1.0.0a"'
# 
# wbemcli ain -ac Xen_ReferencedProfile 'http://localhost:5988/root/interop:
# Xen_RegisteredProfile.InstanceID="CIM:DSP1059-GenericDeviceResourceVirtualization-1.0.0"'
# 
# wbemcli ain -ac Xen_ReferencedProfile 'http://localhost:5988/root/interop:
# Xen_RegisteredProfile.InstanceID="CIM:DSP1045-MemoryResourceVirtualization-1.0.0"'
# 
# wbemcli ain -ac Xen_ReferencedProfile 'http://localhost:5988/root/interop:
# Xen_RegisteredProfile.InstanceID="CIM:DSP1081-VirtualSystemMigration-1.0"'
#
# All the above give the following Output:
# ----------------------------------------
# All the above examples have the following as result.
# 
# localhost:5988/root/interop:Xen_RegisteredProfile.
# InstanceID="CIM:DSP1042-SystemVirtualization-1.0.0"
# ......
# InstanceID="CIM:DSP1042-SystemVirtualization-1.0.0"
# RegisteredOrganization=2
# RegisteredName="System Virtualization"
# RegisteredVersion="1.0.0"
# ....
# 
# wbemcli ai -ac Xen_ReferencedProfile 'http://localhost:5988/root/interop:
# Xen_RegisteredProfile.InstanceID="CIM:DSP1042-SystemVirtualization-1.0.0"'  
# 
# Output:
# -------
# localhost:5988/root/interop:Xen_RegisteredProfile.InstanceID="CIM:DSP1057-VirtualSystem-1.0.0a"
# -InstanceID="CIM:DSP1057-VirtualSystem-1.0.0a"
# -RegisteredOrganization=2
# -RegisteredName="Virtual System Profile"
# -RegisteredVersion="1.0.0a"
# 
# localhost:5988/root/interop:Xen_RegisteredProfile.
# InstanceID="CIM:DSP1059-GenericDeviceResourceVirtualization-1.0.0"
# .....
# localhost:5988/root/interop:Xen_RegisteredProfile.
# InstanceID="CIM:DSP1045-MemoryResourceVirtualization-1.0.0"
# ......
# localhost:5988/root/interop:Xen_RegisteredProfile.
# InstanceID="CIM:DSP1081-VirtualSystemMigration-1.0"
# ......
# 
#                                                           Date : 31-03-2008 
import sys
from XenKvmLib import enumclass
from XenKvmLib.assoc import Associators
from XenKvmLib.common_util import profile_init_list
from CimTest import Globals
from CimTest.Globals import logger, CIM_ERROR_ENUMERATE, CIM_ERROR_ASSOCIATORS
from CimTest.Globals import do_main
from XenKvmLib.classes import get_typed_class
from CimTest.ReturnCodes import FAIL, PASS, SKIP
from XenKvmLib.common_util import print_field_error

sup_types = ['Xen', 'KVM', 'XenFV', 'LXC']

def get_proflist():
    proflist = []
    status = PASS
    try: 
        key_list = ["InstanceID"]
        proflist = enumclass.enumerate(server, reg_classname, key_list, virt) 
        if len(proflist) < 5:
            logger.error("%s returned %i %s objects, expected atleast 5", 
                         reg_classname, len(proflist), 'Profile')
            status = FAIL

    except Exception, detail:
        logger.error(CIM_ERROR_ENUMERATE, reg_classname)
        logger.error("Exception: %s", detail)
        status = FAIL

    if status != PASS:
        return status, proflist

    profiles_instid_list = [ profile.InstanceID for profile in proflist ] 

    return status, profiles_instid_list 

def verify_fields(assoc_info, sys_prof_info):
    fieldnames = ["InstanceID", "RegisteredOrganization", "RegisteredName", "RegisteredVersion"]
    for f in fieldnames:
        if assoc_info[f] != sys_prof_info[f]:
            print_field_error(f, assoc_info[f], sys_prof_info[f])
            return FAIL
    return PASS

def verify_ref_assoc_info(assoc_info, profilename):
    status = PASS
    profiles = profile_init_list()
    logger.info("Verifying profile: %s", profilename)
    for inst in assoc_info:
        for profnum, profinfo in profiles.items():
            if profnum in inst['InstanceID']:
                status = verify_fields(inst, profinfo)
                if status != PASS:
                    break
        if status != PASS:
            break
    return status


def get_refprof_verify_info(proflist):
    assoc_info = []
    status = PASS
    assoc_name =  get_typed_class(virt, 'ReferencedProfile')
    for instid in proflist:
        try:
            assoc_info = Associators(server, assoc_name, reg_classname, 
                                     virt, InstanceID = instid, 
                                     CreationClassName = reg_classname)
            if len(assoc_info) < 1:
                logger.error("%s returned %i %s objects, expected atleast 1", 
                             assoc_name, len(assoc_info), 'Profiles')
                status = FAIL
            if status != PASS:
                break 

            status = verify_ref_assoc_info(assoc_info, instid)
            if status != PASS:
                break 

        except Exception, detail:
            logger.error(CIM_ERROR_ASSOCIATORS, assoc_name)
            logger.error("Exception: %s", detail)
            status = FAIL

    return status

@do_main(sup_types)
def main():
    options = main.options
    global virt, server, reg_classname
    virt = options.virt
    server = options.ip
    status = PASS

    prev_namespace = Globals.CIM_NS
    Globals.CIM_NS = 'root/interop'
    reg_classname = get_typed_class(virt, 'RegisteredProfile')

    status, proflist = get_proflist()
    if status != PASS :
        Globals.CIM_NS = prev_namespace
        return status 
    
    status = get_refprof_verify_info(proflist)
    Globals.CIM_NS = prev_namespace
    return status 

if __name__ == "__main__":
    sys.exit(main())
