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
# Xen_SettingsDefineCapabilities association with 
# Xen_VirtualSystemMigrationCapabilities 
# Command
# -------
# wbemcli ai -ac Xen_SettingsDefineCapabilities \
# 'http://localhost:5988/root/virt:\
# Xen_VirtualSystemMigrationCapabilities.InstanceID=\
# "MigrationCapabilities"'  -nl
#
# 
# Output
# ------
# localhost:5988/root/virt:Xen_VirtualSystemMigrationSettingData.\
# InstanceID="MigrationSettingData" 
# 
#                                                Date : 05-03-2008 

import sys
from XenKvmLib import assoc
from CimTest.Globals import CIM_ERROR_ASSOCIATORS, logger
from CimTest.ReturnCodes import PASS, FAIL
from XenKvmLib.const import do_main, platform_sup
from XenKvmLib.classes import get_typed_class
from XenKvmLib.common_util import print_field_error

@do_main(platform_sup)
def main():
    options = main.options
    status = PASS
    server = options.ip
    an     = get_typed_class(options.virt, 'SettingsDefineCapabilities')
    cn     = get_typed_class(options.virt, 'VirtualSystemMigrationCapabilities')
    qcn    = get_typed_class(options.virt, 'VirtualSystemMigrationSettingData')
    instid = 'MigrationCapabilities'
    try:
        assoc_info = assoc.Associators(server, an, cn, InstanceID = instid, 
                                                       virt = options.virt)  
        if len(assoc_info) != 1: 
            logger.error("%s returned %i %s objects", an, len(assoc_info), qcn)
            return FAIL
        verify_assoc = assoc_info[0]
        if verify_assoc.classname != qcn:
            print_field_error('Classname', verify_assoc.classname, qcn)
            status = FAIL 
        if verify_assoc['InstanceID'] != 'MigrationSettingData':
            print_field_error('InstanceID', verify_assoc['InstanceID'], 
                                               'MigrationCapabilities')
            status = FAIL 
    except Exception, detail:
        logger.error(CIM_ERROR_ASSOCIATORS, an)
        logger.error("Exception: %s", detail)
        status = FAIL
    return status
    
if __name__ == "__main__":
    sys.exit(main())
