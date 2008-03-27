#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
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
# This tc is used to verify the Classname and InstanceID of 
# Xen_SettingsDefineCapabilities association with Xen_VirtualSystemMigrationCapabilities 
# Command
# -------
# wbemcli ai -ac Xen_SettingsDefineCapabilities \
# 'http://localhost:5988/root/virt:\
# Xen_VirtualSystemMigrationCapabilities.InstanceID="MigrationCapabilities"'  -nl
#
# 
# Output
# ------
# localhost:5988/root/virt:Xen_VirtualSystemMigrationSettingData.\
# InstanceID="MigrationSettingData" 
# 
#                                                Date : 05-03-2008 

import sys
from VirtLib import utils
from XenKvmLib import assoc
from CimTest.Globals import log_param, CIM_ERROR_ASSOCIATORS, logger, do_main
from CimTest.ReturnCodes import PASS, FAIL

sup_types = ['Xen']

def print_error(fieldname, ret_value, exp_value):
    logger.error("%s Mismatch", fieldname)
    logger.error("Returned %s instead of %s", ret_value, exp_value)

@do_main(sup_types)
def main():
    options = main.options
    log_param()
    status = PASS
    server = options.ip
    an     = 'Xen_SettingsDefineCapabilities'
    cn     = 'Xen_VirtualSystemMigrationCapabilities'
    qcn    = 'Xen_VirtualSystemMigrationSettingData'
    instid = 'MigrationCapabilities'

    try:
        assoc_info = assoc.Associators(server, \
                                           an, \
                                           cn, \
                           InstanceID = instid)  
        if len(assoc_info) != 1: 
            logger.error("%s returned %i %s objects", an, len(assoc_info), qcn)
            return FAIL
        verify_assoc = assoc_info[0]
        if verify_assoc.classname != qcn:
            print_error('Classname', verify_assoc.classname, qcn)
            status = FAIL 
        if verify_assoc['InstanceID'] != 'MigrationSettingData':
            print_error('InstanceID', verify_assoc['InstanceID'], 'MigrationCapabilities')
            status = FAIL 
    except Exception, detail:
        logger.error(CIM_ERROR_ASSOCIATORS, an)
        logger.error("Exception: %s", detail)
        status = FAIL
    return status
    
if __name__ == "__main__":
    sys.exit(main())
