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

# This test case is used to verify the Parent DiskPoolRASD properties 
# in detail using the SettingsDefineCapabilities association.
#
# Ex: 
# Command:
# wbemcli ai -ac SettingsDefineCapabilities \
# 'http://localhost:5988/root/virt:KVM_AllocationCapabilties.InstanceID=\
# "DiskPool/0"'
#
# Output:
# localhost/root/virt:KVM_DiskPoolResourceAllocationSettingData.\
# InstanceID="Increment"
# -InstanceID="Default" [ verified for Minimum, Maximum, Increment as well ]
# -ResourceType=17
# -PoolID="DiskPool/0"
# -Type=3               [ For Type 1 and 2 as well ]
# -Path="/dev/null"
# -DevicePath=
# -Host="host_sys.domain.com"
# -SourceDirectory="/var/lib/images"
# 
#                                               Date : 21-05-2009

import sys
from sets import Set
from CimTest.Globals import logger
from XenKvmLib.const import do_main
from CimTest.ReturnCodes import PASS, FAIL
from XenKvmLib.pool import get_pool_rasds

sup_types = ['KVM', 'Xen', 'XenFV']
DISKPOOL_REC_LEN = 3

def get_rec(diskpool_rasd, inst_id='Default'):
    recs = []
    for dp_rasd in diskpool_rasd:
        if dp_rasd['InstanceID'] == inst_id :
           recs.append(dp_rasd)
    return recs

@do_main(sup_types)
def main():
    options = main.options
    virt = options.virt
    server = options.ip
    diskpool_rasd = get_pool_rasds(server, virt, pool_type="DiskPool", 
                                   filter_default=False)
    inst_list = [ 'Default', 'Minimum', 'Maximum', 'Increment' ]
    n_rec_val = { 'ResourceType' : 17,
                  'PoolID'       : "DiskPool/0",
                  'Path'         : "/dev/null",
                }
    exp_type_path_host_dir = [('1', 'None', 'None', 'None'),
                              ('2', '/dev/sda100', 'None', 'None'), 
                              ('3', 'None', 'host_sys.domain.com', 
                               '/var/lib/images')]
                    
                  
    for inst_type in inst_list:
        logger.info("Verifying '%s' records", inst_type)

        try:
            n_rec = get_rec(diskpool_rasd, inst_id=inst_type)
            if len(n_rec) != DISKPOOL_REC_LEN:
                raise Exception("Got %s recs instead of %s" %(len(n_rec), 
                                 DISKPOOL_REC_LEN))

            res_type_path_host_dir = []
            for rec in n_rec:
                l = (str(rec['Type']), str(rec['DevicePath']), 
                         str(rec['Host']), str(rec['SourceDirectory']))
                res_type_path_host_dir.append(l)

            if len(Set(exp_type_path_host_dir) & Set(res_type_path_host_dir)) \
               != DISKPOOL_REC_LEN :
                raise Exception("Mismatching values, \nGot %s,\nExpected %s"\
                                 %(exp_type_path_host_dir, 
                                   res_type_path_host_dir))

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
