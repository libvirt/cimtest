#!/usr/bin/python
#
# Copyright 2009 IBM Corp.
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

# This test case is used to verify the Parent NetPoolRASD and 
# DiskPoolRASD properties in detail using the SettingsDefineCapabilities
# association.
#
# Ex: 
# Command:
# wbemcli ai -ac SettingsDefineCapabilities \
# 'http://localhost:5988/root/virt:KVM_AllocationCapabilties.InstanceID=\
# "NetworkPool/0"'
#
# Output:
# localhost/root/virt:KVM_NetPoolResourceAllocationSettingData.InstanceID="Default"
# -InstanceID="Default" [ verified for Maximum, Increment, Default as well ]
# -ResourceType=10
# -PoolID="NetworkPool/0"
# -Address="192.168.122.1"
# -Netmask="255.255.255.0"
# -IPRangeStart="192.168.122.2"
# -IPRangeEnd="192.168.122.254"
# -ForwardDevice=  [ verified for 'None' and "eth0" ]
# -ForwardMode=0   [ verified for 1,2 as well ]
# 
# 
# 
#                                               Date : 18-05-2009

import sys
from sets import Set
from CimTest.Globals import logger
from XenKvmLib.const import do_main
from CimTest.ReturnCodes import PASS, FAIL
from XenKvmLib.pool import get_pool_rasds

sup_types = ['KVM', 'Xen', 'XenFV']

def get_rec(netpool_rasd, inst_id='Default'):
    recs = []
    for np_rasd in netpool_rasd:
        if np_rasd['InstanceID'] == inst_id :
           recs.append(np_rasd)
    return recs

@do_main(sup_types)
def main():
    options = main.options
    virt = options.virt
    server = options.ip
    netpool_rasd = get_pool_rasds(server, virt, filter_default=False)
    inst_list = [ 'Default', 'Minimum', 'Maximum', 'Increment' ]
    n_rec_val = { 'ResourceType' : 10,
                  'PoolID'  :  "NetworkPool/0",
                  'Address' : "192.168.122.1",
                  'Netmask' : "255.255.255.0",
                  'IPRangeStart' : "192.168.122.2",
                  'IPRangeEnd'   : "192.168.122.254"
                }
    exp_mode_device = [('None', 0L), ('None', 1L), ('eth0', 1L), 
                       ('None', 2L), ('eth0', 2L)]
    for inst_type in inst_list:
        logger.info("Verifying '%s' records", inst_type)

        try:
            n_rec = get_rec(netpool_rasd, inst_id=inst_type)
            if len(n_rec) != 5:
                raise Exception("Got %s recs instead of 5" %(len(n_rec)))


            res_mode_device = []
            for rec in n_rec:
                l = (str(rec['ForwardDevice']), rec['ForwardMode'])
                res_mode_device.append(l)

            if len(Set(exp_mode_device) & Set(res_mode_device)) != 5 :
                raise Exception("Mismatching Mode and device values, " \
                                "Got %s, Expected %s"  %(exp_mode_device, \
                                 res_mode_device))

            for key in n_rec_val.keys():
                for rec in n_rec:
                    if n_rec_val[key] != rec[key]:
                        raise Exception("'%s' Mismatch, Got %s, Expected %s" \
                                        % (key, rec[key],  n_rec_val[key]))

        except Exception, details:
            logger.error("Exception details: %s", details)
            return FAIL

    return PASS

if __name__ == "__main__":
    sys.exit(main())
