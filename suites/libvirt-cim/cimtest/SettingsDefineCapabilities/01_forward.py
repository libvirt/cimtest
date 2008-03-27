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

# This tc is used to verify the ResourceType,
# PropertyPolicy,ValueRole,ValueRange prop 
# are appropriately set when verified using the 
# Xen_SettingsDefineCapabilities asscoiation.
#
# Example association command :
# wbemcli ai -ac Xen_SettingsDefineCapabilities 
# 'http://localhost:5988/root/virt:
# Xen_AllocationCapabilities.InstanceID="DiskPool/foo"'
# 
# Output:
# ....
# localhost:5988/root/virt:
# Xen_DiskResourceAllocationSettingData.InstanceID="Maximum"
# -InstanceID="Maximum"
# -ResourceType=17
# -PropertyPolicy=0 (This is either 0 or 1)
# -ValueRole=3      ( greater than 0 and less than 4)
# -ValueRange=2     
# ( ValueRange is
#   0 - Default
#   1 - Minimum
#   2 - Maximum
#   3 - Increment 
# )
# .....
# 
# Similarly we check for Memory,Network,Processor.
#
#                                                Date : 21-12-2007

import sys
import os
from distutils.file_util import move_file
from VirtLib import utils
from XenKvmLib import assoc
from XenKvmLib import enumclass
from CimTest import Globals
from CimTest.Globals import do_main
from XenKvmLib.test_xml import netxml 
from XenKvmLib.test_doms import create_vnet 
from VirtLib.live import net_list
from CimTest.ReturnCodes import PASS, FAIL, SKIP

sup_types = ['Xen']

status = PASS
test_dpath = "foo"
disk_file = '/tmp/diskpool.conf'
back_disk_file = disk_file + "." + "SSDC_01_forward" 
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

def clean_up_restore():
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
        sys.exit(status)
         

def get_or_bail(ip, id, pool_class):
    """
        Getinstance for the CLass and return instance on success, otherwise
        exit after cleanup_restore .
    """
    key_list = { 'InstanceID' : id } 

    try:
        instance = enumclass.getInstance(ip, pool_class, key_list)
    except Exception, detail:
        Globals.logger.error(Globals.CIM_ERROR_GETINSTANCE, '%s' % pool_class)
        Globals.logger.error("Exception: %s", detail)
        clean_up_restore()
        status = FAIL 
        sys.exit(status)
    return instance


def init_list(disk, mem, net, proc):
    """
        Creating the lists that will be used for comparisons.
    """

    instlist = [ 
              disk.InstanceID, \
              mem.InstanceID, \
              net.InstanceID, \
              proc.InstanceID
             ]
    cllist = [ 
              "Xen_DiskResourceAllocationSettingData", \
              "Xen_MemResourceAllocationSettingData", \
              "Xen_NetResourceAllocationSettingData", \
              "Xen_ProcResourceAllocationSettingData"
             ]
    rtype = { 
              "Xen_DiskResourceAllocationSettingData" : 17, \
              "Xen_MemResourceAllocationSettingData"  :  4, \
              "Xen_NetResourceAllocationSettingData"  : 10, \
              "Xen_ProcResourceAllocationSettingData" :  3
             }
    rangelist = {
                  "Default"   : 0, \
                  "Minimum"   : 1, \
                  "Maximum"   : 2, \
                  "Increment" : 3 
                }
    return instlist, cllist, rtype, rangelist


def print_error(index, fieldname, assoc_info, exp_value):
    ret_value = assoc_info[index][fieldname]
    Globals.logger.error("%s Mismatch", fieldname)
    Globals.logger.error("Returned %s instead of %s", ret_value, exp_value)


@do_main(sup_types)
def main():
    options = main.options
    global status
    
    cn = 'Xen_AllocationCapabilities'  
    loop = 0 
    server = options.ip
    Globals.log_param()

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
        vir_network = net_list(server)
        if len(vir_network) > 0:
            test_network = vir_network[0]
        else:
            bridgename   = 'testbridge'
            test_network = 'default-net'
            net_xml, bridge = netxml(server, bridgename, test_network)
            ret = create_vnet(server, net_xml)
            if not ret:
                Globals.logger.error("Failed to create the Virtual Network '%s'", \
                                                                        test_network)
                return SKIP
        netid = "%s/%s" % ("NetworkPool", test_network)
        net = get_or_bail(server, id = netid, \
                                        pool_class=enumclass.Xen_NetworkPool) 
        proc = get_or_bail(server, id = procid, \
                                      pool_class=enumclass.Xen_ProcessorPool) 
    
    except Exception, detail:
        Globals.logger.error("Exception: %s", detail)
        clean_up_restore()
        status = FAIL 
        return status

    instlist, cllist, rtype, rangelist = init_list(disk, mem, net, proc )

    for instid in sorted(instlist):
        try:
            assoc_info = assoc.Associators(options.ip, \
                                              "Xen_SettingsDefineCapabilities",
                                              cn,
                                              InstanceID = instid)  
            if len(assoc_info) != 4:
                Globals.logger.error("Xen_SettingsDefineCapabilities returned \
%i ResourcePool objects instead 4", len(assoc_info))
                status = FAIL
                break
            for i in range(len(assoc_info)):
                if assoc_info[i].classname != cllist[loop]:
                    print_error(i, "Classname", assoc_info, cllist[loop])
                    status = FAIL 
                if assoc_info[i]['ResourceType'] != rtype[cllist[loop]]:
                    print_error(i, "ResourceType", assoc_info, rtype[cllist[loop]])
                    status = FAIL 
                ppolicy = assoc_info[i]['PropertyPolicy']
                if ppolicy != 0 and ppolicy != 1:
                    print_error(i, "PropertyPolicy", assoc_info, ppolicy)
                    status = FAIL 
                vrole  = assoc_info[i]['ValueRole']
                if vrole < 0 or vrole > 4:
                    print_error(i, "ValueRole", assoc_info, vrole)
                    status = FAIL 
                insid  = assoc_info[i]['InstanceID']
                vrange = rangelist[insid]
                if vrange != assoc_info[i]['ValueRange']:
                    print_error(i, "ValueRange", assoc_info, vrange)
                    status = FAIL 
                if status != 0:
                    break
            if status != 0:
                break
            else:
                loop = loop + 1 
        except Exception, detail:
            Globals.logger.error(Globals.CIM_ERROR_ASSOCIATORS, \
                                  'Xen_SettingsDefineCapabilities')
            Globals.logger.error("Exception: %s", detail)
            clean_up_restore()
            status = FAIL

    clean_up_restore()
    return status
    
if __name__ == "__main__":
    sys.exit(main())
