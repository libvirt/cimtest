#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Guolian Yun <yunguol@cn.ibm.com>
#    Kaitlin Rupert <karupert@us.ibm.com>
#    Veerendra Chandrappa <vechandr@in.ibm.com>
#    Deepti B. Kalakeri<deeptik@linux.vnet.ibm.com>
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

# This tc is used to verify the EnabledState, HealthState, EnabledDefault and
# the Classname are set appropriately for the results returned by the 
# ElementConformsToProfile association for the RegisteredProfile class
# and ManagedElement Class
# 
#   "CIM:DSP1042-SystemVirtualization-1.0.0" ,
#   "CIM:DSP1057-VirtualSystem-1.0.0a"
#   "CIM:DSP1059-GenericDeviceResourceVirtualization-1.0.0_d"
#   "CIM:DSP1059-GenericDeviceResourceVirtualization-1.0.0_n"
#   "CIM:DSP1059-GenericDeviceResourceVirtualization-1.0.0_p"
#   "CIM:DSP1045-MemoryResourceVirtualization-1.0.0"
#   "CIM:DSP1081-VirtualSystemMigration-0.8.1"
#
#                                                          Date : 04-12-2007

import sys
from VirtLib import utils, live
from XenKvmLib import assoc
from XenKvmLib.test_doms import destroy_and_undefine_all
from XenKvmLib.classes import get_typed_class
from XenKvmLib import vxml
from CimTest import Globals 
from XenKvmLib.common_util import print_field_error, check_sblim
from CimTest.Globals import logger, CIM_ERROR_ASSOCIATORS, CIM_ERROR_ENUMERATE
from XenKvmLib.const import do_main 
from CimTest.ReturnCodes import PASS, FAIL, XFAIL_RC
from XenKvmLib.enumclass import EnumInstances
from XenKvmLib.const import default_network_name, default_pool_name 
from XenKvmLib.const import get_provider_version


sup_types = ['Xen', 'XenFV', 'KVM', 'LXC']
test_dom = "domU"
bug_sblim = '00007'
libvirt_cim_ectp_changes = 680

def pool_init(verify_list, pool_cn, pool_name, virt):
    ccn = get_typed_class(virt, pool_cn)
    instid = '%s/%s' %(pool_cn, pool_name)
    verify_list[ccn]= {'InstanceID' : instid }
    return verify_list
   
def  init_vs_pool_values(server, virt):
    verify_ectp_list = { }
    hs_ccn = get_typed_class(virt, 'HostSystem')
    host = live.hostname(server)
    cs_fields = {
                  'CreationClassName'    : hs_ccn,
                  'Name'                 : host
                }

    verify_ectp_list[hs_ccn] = cs_fields

    cs_ccn = get_typed_class(virt, 'ComputerSystem')
    verify_ectp_list[cs_ccn] = cs_fields.copy()
    verify_ectp_list[cs_ccn]['CreationClassName']   = cs_ccn
    verify_ectp_list[cs_ccn]['Name']   = test_dom

    vs_ccn = get_typed_class(virt, 'VirtualSystemMigrationService')
    verify_ectp_list[vs_ccn] = cs_fields.copy()
    verify_ectp_list[vs_ccn]['CreationClassName']   = vs_ccn
    verify_ectp_list[vs_ccn]['SystemCreationClassName']   =  hs_ccn
    verify_ectp_list[vs_ccn]['SystemName']   =  host
    verify_ectp_list[vs_ccn]['Name']   =  'MigrationService'

    verify_ectp_list = pool_init(verify_ectp_list, 'DiskPool', 
                                 default_pool_name, virt)
    verify_ectp_list = pool_init(verify_ectp_list, 'NetworkPool', 
                                 default_network_name, virt)
    verify_ectp_list = pool_init(verify_ectp_list, 'ProcessorPool', 0, virt)
    verify_ectp_list = pool_init(verify_ectp_list, 'MemoryPool', 0, virt)

                       
    return verify_ectp_list

def verify_fields(assoc_val, pllst_index, vs_pool_values):
    try:
        field_names  = vs_pool_values[pllst_index].keys()
        values = vs_pool_values[pllst_index]
        for field in field_names:
            if values[field] != assoc_val[field]:
                print_field_error(field,  assoc_val[field], values[field]) 
                return FAIL
    except Exception, details:
        logger.error("Exception: In fn verify_fields() %s", details)
        return FAIL
      
    return PASS

def verify_cs_hs_mig_fields(assoc_info, vs_pool_values):
    try:
        pllst_index = assoc_info[0]['CreationClassName']
        assoc_val   = None 
        if 'HostSystem' in pllst_index or \
           'VirtualSystemMigrationService' in pllst_index:
            if len(assoc_info) != 1:
                logger.error("'%s' returned '%d' records, expected 1", 
                              pllst_index, len(assoc_info)) 
                return FAIL
            assoc_val = assoc_info[0]
        else: 
            # For ComputerSystem info
            for inst in assoc_info:
                if inst['Name'] == test_dom:
                    assoc_val = inst
                    break
    except Exception, details:
        logger.error("Exception: In fn verify_cs_hs_mig_fields() %s", details)
        return FAIL

    if assoc_val == None:
       return FAIL

    return verify_fields(assoc_val, pllst_index, vs_pool_values)

def get_proflist(server, reg_classname, virt):
    profiles_instid_list = []
    status = PASS
    try: 
        proflist = EnumInstances(server, reg_classname) 
        curr_cim_rev, changeset = get_provider_version(virt, server)
        if curr_cim_rev < libvirt_cim_ectp_changes:
            len_prof_list = 5
        else:
            len_prof_list = 7 
        if len(proflist) < len_prof_list:
            logger.error("'%s' returned '%d' '%s' objects, expected atleast %d",
                          reg_classname, len(proflist), 'Profile', len_prof_list)
            status = FAIL

    except Exception, detail:
        logger.error(CIM_ERROR_ENUMERATE, reg_classname)
        logger.error("Exception: %s", detail)
        status = FAIL

    if status != PASS:
        return status, profiles_instid_list

    profiles_instid_list = [ profile.InstanceID for profile in proflist ] 

    return status, profiles_instid_list 


def verify_ectp_assoc(server, virt):
    reg_classname = get_typed_class(virt, "RegisteredProfile")
    an = get_typed_class(virt,"ElementConformsToProfile")

    status, inst_lst = get_proflist(server, reg_classname, virt)
    if status != PASS:
        return status

    verify_ectp_list = init_vs_pool_values(server, virt)
    for devid in inst_lst :
        logger.info("Verifying '%s' with '%s'", an, devid)
        try:
            assoc_info = assoc.Associators(server, 
                                           an, 
                                           reg_classname,
                                           InstanceID = devid)  
            if len(assoc_info) < 1:
                ret_val, linux_cs = check_sblim(server, virt)
                if ret_val != PASS:
                    logger.error(" '%s' returned (%d) '%s' objects", an, 
                                 len(assoc_info), reg_classname)
                    return FAIL
                else:
                    return XFAIL_RC(bug_sblim) 
                break

            if 'DSP1059' in devid or 'DSP1045' in devid:
                instid        = assoc_info[0]['InstanceID']
                index, other  = instid.split("/")
                cn = get_typed_class(virt, index)
                status = verify_fields(assoc_info[0], cn, verify_ectp_list)
            else:
                ccn = assoc_info[0]['CreationClassName']
                status = verify_cs_hs_mig_fields(assoc_info, verify_ectp_list)

            if status != PASS:
                break

        except Exception, detail:
            logger.error(CIM_ERROR_ASSOCIATORS, an)
            logger.error("Exception: %s" % detail)
            status = FAIL
    return status

@do_main(sup_types)
def main():
    options = main.options
    server  = options.ip
    virt    = options.virt
  
    status = PASS
    destroy_and_undefine_all(options.ip, options.virt)

    virt_xml = vxml.get_class(options.virt)
    cxml = virt_xml(test_dom)
    ret = cxml.cim_define(server)
    if not ret:
        logger.error('Unable to define domain %s' % test_dom)
        return FAIL

    ret = cxml.start(server)
    if not ret:
        cxml.undefine(server)
        logger.error('Unable to start domain %s' % test_dom)
        return FAIL


    prev_namespace = Globals.CIM_NS
    Globals.CIM_NS = 'root/interop'

    status = verify_ectp_assoc(server, virt)

    Globals.CIM_NS = prev_namespace
    cxml.destroy(server)
    cxml.undefine(server)
    return status

if __name__ == "__main__":
    sys.exit(main())

