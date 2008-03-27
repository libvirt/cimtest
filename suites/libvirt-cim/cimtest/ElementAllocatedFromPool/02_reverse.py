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

# This tc is used to verify the classname, InstanceID and certian prop are 
# are appropriately set for the domains when verified using the 
# Xen_ElementAllocatedFromPool asscoiation.
#
# Example command for LogicalDisk w.r.t to Xen_ElementAllocatedFromPool \
# asscoiation :
# wbemcli ai -ac Xen_ElementAllocatedFromPool \
# 'http://localhost:5988/root/virt:Xen_DiskPool.InstanceID="DiskPool/foo"'
# 
# Output:
# localhost:5988/root/virt:Xen_LogicalDisk.CreationClassName="Xen_LogicalDisk",\
# DeviceID="xen1/xvdb",SystemCreationClassName="",SystemName="xen1"
# ....
#-SystemName="xen1"
#-CreationClassName="Xen_LogicalDisk"
#-DeviceID="xen1/xvda  "
#-Primordial=FALSE
#-Name="xvda"
# .....
# 
# Similarly we check for Memory,Network,Processor.
#
#                                                Date : 29-11-2007

import sys
import os
from distutils.file_util import move_file
import pywbem
from VirtLib import utils
from VirtLib import live 
from XenKvmLib import assoc
from XenKvmLib import enumclass
from CimTest import Globals
from CimTest.Globals import do_main
from CimTest.ReturnCodes import PASS, FAIL, SKIP
from XenKvmLib.test_xml import testxml_bridge
from XenKvmLib.test_doms import test_domain_function, destroy_and_undefine_all
from VirtLib.live import network_by_bridge

sup_types = ['Xen']

status = PASS
test_dom   = "hd_domain"
test_mac   = "00:11:22:33:44:aa"
test_mem   = 128 
test_vcpus = 4 
test_disk  = "xvdb"
test_dpath = "foo"
disk_file = '/tmp/diskpool.conf'
back_disk_file = disk_file + "." + "02_reverse" 
diskid = "%s/%s" % ("DiskPool", test_dpath)
memid = "%s/%s" % ("MemoryPool", 0)
procid = "%s/%s" % ("ProcessorPool", 0)

def conf_file():
   """
       Creating diskpool.conf file.
   """
   try:
         f = open(disk_file, 'w')
         f.write('%s %s' % (test_dpath, '/'))
         f.close()
   except Exception,detail:
      Globals.logger.error("Exception: %s", detail)
      status = SKIP
      sys.exit(status)

def clean_up_restore(ip):
    """
        Restoring back the original diskpool.conf 
        file.
    """
    try: 
        if os.path.exists(back_disk_file):
            os.remove(disk_file)
            move_file(back_disk_file, disk_file)
    except Exception, detail:
        Globals.logger.error("Exception: %s", detail)
        status = SKIP
        ret = test_domain_function(test_dom, ip, \
                                                   cmd = "destroy")
        sys.exit(status)
         

def get_or_bail(ip, id, pool_class):
    """
        Getinstance for the CLass and return instance on success, otherwise
        exit after cleanup_restore and destroying the guest.
    """
    key_list = { 'InstanceID' : id }
    try:
        instance = enumclass.getInstance(ip, pool_class, key_list)
    except Exception, detail:
        Globals.logger.error(Globals.CIM_ERROR_GETINSTANCE, '%s', pool_class)
        Globals.logger.error("Exception: %s", detail)
        clean_up_restore(ip)
        status = FAIL
        ret = test_domain_function(test_dom, ip, \
                                                   cmd = "destroy")
        sys.exit(status)
    return instance

def print_error(field, ret_val, req_val):
    Globals.logger.error("%s Mismatch", field)
    Globals.logger.error("Returned %s instead of %s", ret_val, req_val)

def init_list(ip, disk, mem, net, proc):
    """
        Creating the lists that will be used for comparisons.
    """

    pllist = {
              "Xen_DiskPool"     : disk.InstanceID, \
              "Xen_MemoryPool"   : mem.InstanceID, \
              "Xen_NetworkPool"  : net.InstanceID, \
              "Xen_ProcessorPool": proc.InstanceID
             }
    cllist = [
              "Xen_LogicalDisk", \
              "Xen_Memory", \
              "Xen_NetworkPort", \
              "Xen_Processor"
             ]
    prop_list = ["%s/%s"  % (test_dom, test_disk), test_disk, \
                 "%s/%s" % (test_dom, "mem"), test_mem, \
                 "%s/%s" % (test_dom, test_mac), test_mac
                ]
    proc_prop = []
    for i in range(test_vcpus):
        proc_prop.append("%s/%s" % (test_dom, i))
    return pllist, cllist, prop_list, proc_prop

def get_inst_for_dom(assoc_val):
     list = []

     for i in range(len(assoc_val)):
         if assoc_val[i]['SystemName'] == test_dom:
             list.append(assoc_val[i])

     return list

def get_spec_fields_list(inst_list, field_name):
    global status
    specific_fields = { }
    if (len(inst_list)) != 1:
        Globals.logger.error("Got %s record for Memory/Network/LogicalDisk instead of \
1", len(inst_list))
        status = FAIL
        return 
# verifying the Name field for LogicalDisk 
    try:
        if inst_list[0]['CreationClassName'] != 'Xen_Memory':
            field_value = inst_list[0][field_name]
            if field_name == 'NetworkAddresses':
# For network we NetworkAddresses is a list of addresses, since we 
# are assigning only one address we are taking field_value[0]
                field_value = field_value[0] 
        else:
            field_value = ((int(inst_list[0]['NumberOfBlocks'])*4096)/1024)
        specific_fields = {
                            "field_name"  : field_name,\
                            "field_value" : field_value
                          }
    except Exception, detail:
        Globals.logger.error("Exception in get_spec_fields_list(): %s", detail)
        status = FAIL

    return specific_fields

def  assoc_values(assoc_list, field , list, index, specific_fields_list=""):
    """
        Verifying the records retruned by the associations.
    """
    global status
    if field  == "CreationClassName":
        for i in range(len(assoc_list)):
            if assoc_list[i][field] != list[index]:
                print_error(field,  assoc_list[i][field], list[index])
                status = FAIL
            if status != PASS:
                break
    elif field == "DeviceID":
        if assoc_list[0]['CreationClassName'] == 'Xen_Processor':
# Verifying  the list of DeviceId returned by the association 
# against the list created intially .
            for i in range(len(list)):
                if assoc_list[i]['DeviceID'] != list[i]: 
                    print_error(field, assoc_list[i]['DeviceID'], list[i])
                    status = FAIL
        else:
# Except for Xen_Processor, we get only once record for a domain for 
# other classes.
            if  assoc_list[0]['DeviceID'] != list[index]: 
                print_error(field, assoc_list[0]['DeviceID'] , list[index])
                status = FAIL
    else: 
 # other specific fields verification
        if assoc_list[0]['CreationClassName'] != 'Xen_Processor':
               spec_field_name  = specific_fields_list['field_name']
               spec_field_value =  specific_fields_list['field_value']
               if spec_field_value != list[index]:
                   print_error(field, spec_field_value, list[index])
                   status = FAIL


@do_main(sup_types)
def main():
    options = main.options

    global status 
    loop = 0 
    server = options.ip
    destroy_and_undefine_all(options.ip)
    Globals.log_param()
    test_xml, bridge = testxml_bridge(test_dom, mem = test_mem, vcpus = test_vcpus, \
                               mac = test_mac, disk = test_disk, server = options.ip)
    if bridge == None:
        Globals.logger.error("Unable to find virtual bridge")
        return SKIP

    if test_xml == None:
        Globals.logger.error("Guest xml was not created properly")
        return FAIL

    virt_network = network_by_bridge(bridge, server)
    if virt_network == None:
        Globals.logger.error("No virtual network found for bridge %s", bridge)
        return SKIP

    ret = test_domain_function(test_xml, server, cmd = "create")
    if not ret:
        Globals.logger.error("Failed to Create the dom: %s", test_dom)
        return FAIL

    # Taking care of already existing diskconf file
    # Creating diskpool.conf if it does not exist
    # Otherwise backing up the prev file and create new one.
    os.system("rm -f %s" % back_disk_file )
    if not (os.path.exists(disk_file)):
        conf_file()
    else:
        move_file(disk_file, back_disk_file)
        conf_file()
    try :
        disk = get_or_bail(server, id=diskid, \
                                          pool_class=enumclass.Xen_DiskPool)
        mem = get_or_bail(server, id = memid, \
                                        pool_class=enumclass.Xen_MemoryPool)
        netid = "%s/%s" % ("NetworkPool", virt_network)
        net = get_or_bail(server, id = netid, \
                                        pool_class=enumclass.Xen_NetworkPool) 
        proc = get_or_bail(server, id = procid, \
                                      pool_class=enumclass.Xen_ProcessorPool) 
    
    except Exception, detail:
        Globals.logger.error("Exception: %s", detail)
        clean_up_restore(server)
        status = FAIL
        ret = test_domain_function(test_dom, server, \
                                                   cmd = "destroy")
        return status

    pllist, cllist, prop_list, proc_prop = init_list(server, disk, mem, net, proc)

# Looping through the pllist to get association for various pools.
    for cn,  instid in sorted(pllist.items()):
        try:
            assoc_info = assoc.Associators(server, \
                                               "Xen_ElementAllocatedFromPool", \
                                                                           cn, \
                                                            InstanceID = instid)  
# Verifying the Creation Class name for all the records returned for each 
# pool class queried
            inst_list = get_inst_for_dom(assoc_info)
            if (len(inst_list)) == 0:
                Globals.logger.error("Association did not return any records for \
the specified domain: %s", test_dom)
                status = FAIL
                break

            assoc_values(assoc_list=inst_list, field="CreationClassName", \
                                                             list=cllist, \
                                                                index=loop)
# verifying the DeviceID
            if inst_list[0]['CreationClassName'] == 'Xen_Processor':
# The DeviceID for the processor varies from 0 to (vcpu - 1 )
                list_index = 0
                assoc_values(assoc_list=inst_list, field="DeviceID", \
                                                     list=proc_prop, \
                                                     index=list_index)
            else:
# For LogicalDisk, Memory and NetworkPort
                if  inst_list[0]['CreationClassName'] == 'Xen_LogicalDisk':
                    list_index = 0                
                elif inst_list[0]['CreationClassName'] == 'Xen_Memory':
                    list_index = 2                
                else:
                    list_index = 4 # NetworkPort
                assoc_values(assoc_list=inst_list, field="DeviceID", \
                                                     list=prop_list, \
                                                     index=list_index)
                if  inst_list[0]['CreationClassName'] == 'Xen_LogicalDisk':
# verifying the Name field for LogicalDisk 
                    specific_fields = get_spec_fields_list(inst_list,field_name="Name")
                    list_index = 1        
                elif inst_list[0]['CreationClassName'] == 'Xen_Memory':
# verifying the NumberOfBlocks allocated for Memory
                    specific_fields = get_spec_fields_list(inst_list,field_name="NumberOfBlocks")
                    list_index = 3                
                else:
# verifying the NetworkAddresses for the NetworkPort
                    specific_fields = get_spec_fields_list(inst_list,field_name="NetworkAddresses")
                    list_index = 5 # NetworkPort
                    assoc_values(assoc_list=inst_list, field="Other", \
                                                      list=prop_list, \
                                                    index=list_index, \
                                  specific_fields_list=specific_fields)
            if status != PASS:
                break
            else:
# The loop variable is used to index the cllist to verify the creationclassname 
               loop = loop + 1
        except Exception, detail:
            Globals.logger.error(Globals.CIM_ERROR_ASSOCIATORS, \
                                  'Xen_ElementAllocatedFromPool')
            Globals.logger.error("Exception: %s", detail)
            clean_up_restore(server)
            status = FAIL

    ret = test_domain_function(test_dom, server, \
                                                   cmd = "destroy")
    clean_up_restore(server)
    return status
if __name__ == "__main__":
    sys.exit(main())
