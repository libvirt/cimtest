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
#
# This is a cross-provider testcase to 
# Get the MigrationSettingData properties starting from the host 
#
# It traverses the following path: 
# {Hostsystem} --> [HostedService] {VirtualSystemMigrationService} --> 
# [ElementCapabilities] {VirtualSystemMigrationCapabilities} -->
# [SettingsDefineCapabilities] {VirtualSystemMigrationSettingData} 
# Verify the VirtualSystemMigrationSettingData.
#
# Steps:
# ------
# 1) Get the hostname by enumerating the hostsystem.
# 2) Get the various service on the host by using the HostedService association by supplying 
#    the inputs obtained from querying the hostsystem.
# 4) Select the VirtualSystemMigrationService from the association returned. We should get only
#    one record.
# 5) Use the VirtualSystemMigrationService information to query ElementCapabilities association
#    Verify that we should get only one MigrationCapabilities record from the VSMS association.
# 6) Obtain the VSMigrationSettingData values by using the MigrationCapabilities output from the 
#    previous query and supplying it to the SettingsDefineCapabilities association.
# 7) Check, that we obtain only one VSMigrationSettingData data.  
#    Verify the VSMigrationSettingData values.
#                                                                      Date : 28.03.2008

import sys
from XenKvmLib.const import do_main
from XenKvmLib.classes import get_typed_class
from XenKvmLib.assoc import Associators, AssociatorNames
from XenKvmLib.common_util import get_host_info
from CimTest.Globals import logger, CIM_ERROR_ASSOCIATORNAMES, \
CIM_ERROR_ASSOCIATORS
from CimTest.ReturnCodes import PASS, FAIL

sup_types = ['Xen', 'KVM', 'XenFV', 'LXC']

def print_err(err, detail, cn):
    logger.error(err, cn)
    logger.error("Exception: %s", detail)

def print_field_error(fieldname, ret_value, exp_value):
    logger.error("%s Mismatch", fieldname)
    logger.error("Returned %s instead of %s", ret_value, exp_value)


def get_inst_from_list(server, cn, assoc_info, filter_name, exp_val):
    status = PASS
    ret = -1
    inst = []
    for rec in assoc_info:
        record = rec[filter_name]
        if record == exp_val:
            inst.append(rec)
            ret = PASS

    # When no records are found.
    if ret != PASS:
        logger.error("%s with %s was not returned", cn, exp_val)
        status = FAIL

    return status, inst

def get_assocnames_info(server, cn, an, qcn, name):
    status = PASS
    assoc_info = []
    try:
        assoc_info = AssociatorNames(server, an, cn, Name = name, 
                                     CreationClassName = cn)
        if len(assoc_info) < 0 :
            logger.error("%s returned %i %s objects, expected atleast 3", 
                         an, len(assoc_info), qcn)
            status = FAIL
    except Exception, detail:
        print_err(CIM_ERROR_ASSOCIATORNAMES, detail, an)
        status = FAIL

    return status, assoc_info


def get_vsms_info():
    status, host_inst = get_host_info(server, virt)
    if status != PASS:
        return status, []

    classname = host_inst.CreationClassName
    host_name = host_inst.Name
    status, service_assoc_info = get_assocnames_info(server, classname, 
                                                     assoc_name, req_cn, host_name)
    if status != PASS or len(service_assoc_info) == 0:
        return status, service_assoc_info
    filter_name  =  "Name"
    filter_value =  'MigrationService'
    cn = 'VirtualSystemMigrationService'
    status, vsms_list = get_inst_from_list(server, cn, service_assoc_info, filter_name, 
                                                                          filter_value)
    return status, vsms_list

def get_vsmcap_from_ec(vsms_list):
    status = PASS
    vsms_info = vsms_list[0]
    cn   = vsms_info['CreationClassName']
    sn   = vsms_info['SystemName']
    name = vsms_info['Name']
    sccn = vsms_info['SystemCreationClassName']
    assoc_info = []
    try:
        assoc_info = AssociatorNames(server, assoc_name, cn, 
                                     CreationClassName = cn, 
                                     SystemName = sn, Name = name, 
                                     SystemCreationClassName = sccn)
        if len(assoc_info) != 1:
            logger.error("%s returned %i %s objects, expected only 1", assoc_name, len(assoc_info), req_cn)
            status = FAIL

    except Exception, detail:
        print_err(CIM_ERROR_ASSOCIATORNAMES, detail, assoc_name)
        status = FAIL

    return status, assoc_info

def get_vsmsd_from_sdc(vsmsd_list):
    status = PASS
    vsmsd_info = vsmsd_list[0]
    cn     = vsmsd_info.classname
    instid = vsmsd_info['InstanceID']
    assoc_info = []
    try:
        assoc_info = Associators(server, assoc_name, cn, 
                                 CreationClassName = cn, InstanceID = instid)
        if len(assoc_info) != 1:
            logger.error("%s returned %i %s objects, expected only 1", 
                         assoc_name, len(assoc_info), req_cn)
            status = FAIL

    except Exception, detail:
        print_err(CIM_ERROR_ASSOCIATORS, detail, assoc_name)
        status = FAIL

    return status, assoc_info

def verify_vsmsd_values(vsmsd_list):

    # Values to be used for comparison 
    cn       =  get_typed_class(virt, "VirtualSystemMigrationSettingData")
    instid   = 'MigrationSettingData'
    MType    = 2 #[CIM_MIGRATE_LIVE]
    priority = 0

    verify_vsmsd = vsmsd_list[0]
    if verify_vsmsd.classname != cn:
        print_field_error('ClassName', verify_vsmsd.classname, cn)
        return FAIL
    if verify_vsmsd['InstanceID'] != instid:
        print_field_error('InstanceID', verify_vsmsd['InstanceID'], instid)
        return FAIL
    if verify_vsmsd['MigrationType'] != MType:
        print_field_error('MigrationType', verify_vsmsd['MigrationType'], MType)
        return FAIL
    if verify_vsmsd['Priority'] != priority:
        print_field_error('Priority', verify_vsmsd['Priority'], priority)
        return FAIL
    return PASS


@do_main(sup_types)
def main():
    global virt, server
    global assoc_name, class_name, req_cn
    options = main.options
    server = options.ip
    status = PASS
    virt = options.virt

    assoc_name   = get_typed_class(virt, 'HostedService')
    req_cn  = 'Service' 
    status, vsms_list = get_vsms_info()
    if status != PASS or len(vsms_list) == 0:
        logger.error("Did not get the expected MigrationService record")
        return status
    if len(vsms_list) != 1:
        logger.error("%s returned %i %s objects, expected only 1", assoc_name, len(vsms_list), req_cn)
        return FAIL

    assoc_name  = get_typed_class(virt, 'ElementCapabilities') 
    req_cn  = 'MigrationCapabilities'
    status, vsmscap = get_vsmcap_from_ec(vsms_list)
    if status != PASS or len(vsmscap) == 0:
        logger.error("Did not get the expected MigrationCapabilities record")
        return status

    assoc_name  = get_typed_class(virt, 'SettingsDefineCapabilities') 
    req_cn  = 'MigrationSettingData'
    status, vsmsd = get_vsmsd_from_sdc(vsmscap)
    if status != PASS or len(vsmsd) == 0:
        logger.error("Did not get the expected MigrationSettingData record")
        return status

    status = verify_vsmsd_values(vsmsd)

    return status
if __name__ == "__main__":
    sys.exit(main())
