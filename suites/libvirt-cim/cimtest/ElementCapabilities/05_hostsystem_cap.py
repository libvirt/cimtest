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
#
# This is a cross-class testcase to 
# Get the available service capabilities on the host.
#
# It traverses the following path: 
# {!Hostsystem} --> [HostedService](select one instance from the output) --> 
# [ElementCapabilities]
# (verify values of the instance returned) 
#
# Steps:
# ------
# 1) Initialise service_list which will be used for storing the service info 
#    obtained from HostedService info.
# 2) Create a capabilities list which will be used for comparison of the results
#    obtained from ElementCapabilities.
# 3) Get the host inforamtion. 
# 4) Use the host information obtained above and get the list of services on the 
#    system using the HostedService association.
# 5) From HostedService association select the ManagementService and MigrationService
#    services.
# 6) Build the service_list with the instances obtained above. 
# 7) Call ElementCapabilities assocaition with ManagementService and verify the 
#    ManagementCapabilities.
# 8) Call ElementCapabilities assocaition with  MigrationService and verify the
#    MigrationCapabilities.
#                                                                   Date : 28.02.2008

import sys
from VirtLib import utils
from XenKvmLib.assoc import AssociatorNames
from XenKvmLib.common_util import get_host_info
from CimTest.Globals import log_param, logger, CIM_ERROR_ASSOCIATORNAMES
from CimTest.Globals import do_main
from CimTest.ReturnCodes import PASS, FAIL

sup_types = ['Xen']

def print_err(err, detail, cn):
    logger.error(err % cn)
    logger.error("Exception: %s", detail)

def field_err(fieldname, exp_val, ret_value):
    logger.error("%s Mismatch", fieldname) 
    logger.error("Returned %s instead of %s", exp_val, ret_value)

def get_inst_from_list(cn, cs_list, filter_name, exp_val):
    status = PASS
    ret = -1
    inst = []
    for inst in cs_list:
        if inst[filter_name['key']] == exp_val:
            ret = PASS
            break

    if ret != PASS:
        logger.error("%s with %s was not returned" % (cn, exp_val))
        status = FAIL

    return status, inst

def get_assoc_info(server, cn, an, qcn, name):
    status = PASS
    assoc_info = []
    try:
        assoc_info = AssociatorNames(server,
                                         an,
                                         cn,
                     CreationClassName = cn,
                                Name = name)
        if len(assoc_info) < 1:
            logger.error("%s returned %i %s objects" % (an, len(assoc_info), qcn))
            status = FAIL
    except Exception, detail:
        print_err(CIM_ERROR_ASSOCIATORNAMES, detail, cn)
        status = FAIL
    return status, assoc_info

def get_association_info(server, service_fieldname, cn, an, qcn):
    status  = PASS
    cn      = service_list[service_fieldname]['CreationClassName']
    an      = 'Xen_ElementCapabilities'
    qcn     = 'Capabilities'
    name    = service_list[service_fieldname]['Name']
    sccname = service_list[service_fieldname]['SystemCreationClassName']
    sname   = service_list[service_fieldname]['SystemName']
    assoc_info = []
    try:
        assoc_info = AssociatorNames(server,
                                         an,
                                         cn,
                     CreationClassName = cn,
                                Name = name,
            SystemCreationClassName=sccname,
                           SystemName=sname)
        if len(assoc_info) < 1:
            logger.error("%s returned %i %s objects" % (an, len(assoc_info), qcn))
            status = FAIL

    except Exception, detail:
        print_err(CIM_ERROR_ASSOCIATORNAMES, detail, cn)
        status = FAIL
    return status, assoc_info


def get_values(cn, service_assoc_info, fieldname):
    status = PASS
    filter_name =  {"key" : "Name"}
    exp_val = service_list[fieldname]
    status, service_info = get_inst_from_list(cn,
                              service_assoc_info,
                                     filter_name,
                                         exp_val)
    if status != PASS or len(service_info) == 0:
        logger.error("Did not get the requested '%s' instance", exp_val)
        return status
    service_list[fieldname] = service_info 
    return status 

def verify_cap_fields(server, service_fieldname, cap_key):
    cn      = service_list[service_fieldname]['CreationClassName'] 
    an      = 'Xen_ElementCapabilities'
    qcn     = 'Capabilities'
    status, cap_assoc_info = get_association_info(server, service_fieldname, \
                                                                  cn, an, qcn)
    if status != PASS or len(cap_assoc_info) == 0:
        return status
    cn = cap_assoc_info[0].classname
    fieldname = 'ClassName'
    if cn != cap_list[cap_key][fieldname]:
        field_err(fieldname, cn, cap_list[cap_key][fieldname])
        status = FAIL
    fieldname = 'InstanceID'
    instid = cap_assoc_info[0][fieldname]
    if instid != cap_list[cap_key][fieldname]:
        field_err(fieldname, instid, cap_list[cap_key][fieldname])
        status = FAIL
    return status 

@do_main(sup_types)
def main():
    options = main.options
    log_param()
    server = options.ip
    global service_list
    global cap_list

    # initialising the list
    service_list = { 'ManagementService' : 'Management Service', \
                      'MigrationService' : 'MigrationService'
                   }

    # This will be used for the comparison at the end.
    mgtcap = { 'ClassName'     : 'Xen_VirtualSystemManagementCapabilities', \
               'InstanceID'    : 'ManagementCapabilities'
             }
    migcap = { 'ClassName'     : 'Xen_VirtualSystemMigrationCapabilities', \
               'InstanceID'    : 'MigrationCapabilities'
             }
    cap_list = { 
                 'ManagementCapabilities' : mgtcap, \
                 'MigrationCapabilities'  : migcap
               }

    # Get the host info
    status, host_name, classname = get_host_info(server)
    if status != PASS:
        return status

    an   = 'Xen_HostedService'
    cn   = classname
    qcn  = 'Service'
    name = host_name
    # Get the service available on the host
    status, service_assoc_info = get_assoc_info(server, cn, an, qcn, name)
    if status != PASS or len(service_assoc_info) == 0:
        return status

    # select the Management service and store in service_list
    fieldname = 'ManagementService'
    status = get_values(cn, service_assoc_info, fieldname)
    if status != PASS:
        return status

    # select the Migration service and store in service_list
    fieldname = 'MigrationService'
    status = get_values(cn, service_assoc_info, fieldname)
    if status != PASS:
        return status

    # Query ElementCapabilities and verify the ManagementCapabilities information.
    service_fieldname = 'ManagementService'
    cap_key = 'ManagementCapabilities'
    status = verify_cap_fields(server, service_fieldname, cap_key)
    if status != PASS:
        logger.error("ManagementCapabilities Verification failed")
        return status

    # Query ElementCapabilities and verify the MigrationCapabilities information.
    service_fieldname = 'MigrationService'
    cap_key = 'MigrationCapabilities'
    status = verify_cap_fields(server, service_fieldname, cap_key)
    if status != PASS:
        logger.error("MigrationCapabilities Verification failed")
        return status

    return status
if __name__ == "__main__":
    sys.exit(main())
