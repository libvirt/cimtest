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

# The following test case is used to verify the profiles supported
# by the VSM providers. 
#  
#                                          Date : 24-10-2007 
import sys
import pywbem
from XenKvmLib import enumclass
from CimTest import Globals
from CimTest.Globals import do_main

sup_types = ['Xen']

@do_main(sup_types)
def main():
    options = main.options

    registeredOrganization = 2
    registeredname = ['System Virtualization', \
                      'Virtual System Profile' ]
    inst_id = ['CIM:DSP1042-SystemVirtualization-1.0.0', \
                      'CIM:DSP1057-VirtualSystem-1.0.0a']
    registeredversion = [ '1.0.0', '1.0.0a'] 
    cn = 'Xen_RegisteredProfile'
    index = 0 

    status = 0
    prev_namespace = Globals.CIM_NS
    Globals.CIM_NS = 'root/interop'

    Globals.log_param()
    try: 
        key_list = ["InstanceID"]
        proflist = enumclass.enumerate(options.ip, \
                                    enumclass.Xen_RegisteredProfile, \
                                    key_list) 

    # For each of the instances verify : 
    # -RegisteredOrganization = 2
    # -InstanceID="CIM:DSP1042-SystemVirtualization-1.0.0"
    # -RegisteredName="System Virtualization"
    # -RegisteredVersion="1.0.0"

        for profile in proflist:
            Globals.logger.log(int(Globals.logging.PRINT),"Verifying the \
fields for :%s", profile.RegisteredName)
            if profile.InstanceID == "" :
                Globals.logger.error("InstanceID is %s instead of %s", \
                   'NULL', inst_id[index])
                status = 1  
            if inst_id[index] != profile.InstanceID :
                Globals.logger.error("InstanceID is %s instead of %s", \
                   profile.InstanceID, inst_id[index])
                status = 1  
            if registeredOrganization != profile.RegisteredOrganization:
                Globals.logger.error("RegisteredOrganization is %s instead of %s"\
                   , profile.RegisteredOrganization, registeredOrganization)
                status = 1
            if registeredname[index] != profile.RegisteredName:
                 Globals.logger.error("RegisteredName is %s instead of %s", \
                   profile.RegisteredName, registeredname[index])
                 status = 1  
            if registeredversion[index] != profile.RegisteredVersion:
                 Globals.logger.error("RegisteredVersion is %s instead of \
%s", profile.RegisteredVersion, registeredversion[index])
                 status = 1
            if status != 0:
                Globals.CIM_NS = prev_namespace
                return status 
            index = index + 1 
    except Exception, detail:
        Globals.logger.error(Globals.CIM_ERROR_ENUMERATE, 'Xen_RegisteredProfile')
        Globals.logger.error("Exception: %s", detail)
        status = 1
        return status 

# The execution will reach here only if all the checks are successful       
    Globals.logger.log(int(Globals.logging.PRINT), "Verification of the properties \
for the class '%s' was successful", cn)
    return status

if __name__ == "__main__":
    sys.exit(main())
