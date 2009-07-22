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
# -DevicePaths=
# -Host="host_sys.domain.com"
# -SourceDirectory="/var/lib/images"
# 
#                                               Date : 21-05-2009

import sys
from sets import Set
from copy import copy
from CimTest.Globals import logger
from XenKvmLib.const import do_main
from CimTest.ReturnCodes import PASS, FAIL
from XenKvmLib.pool import get_pool_rasds, DIR_POOL, FS_POOL, NETFS_POOL, \
                           DISK_POOL, ISCSI_POOL, LOGICAL_POOL, SCSI_POOL
                

sup_types = ['KVM', 'Xen', 'XenFV']
DISKPOOL_REC_LEN = 7

def init_list():
    pval = "/dev/null"
    dir_pool = { 'ResourceType' : 17,
                 'PoolID'       : "DiskPool/0",
                 'Type' : DIR_POOL,
                 'DevicePaths': None, 
                 'Host' : None, 'SourceDirectory': None, 
                 'Path' : pval 
               }

    fs_pool = dir_pool.copy()
    fs_pool['Type'] = FS_POOL
    fs_pool['DevicePaths'] = [u'/dev/sda100']

    netfs_pool = dir_pool.copy()
    netfs_pool['Type'] = NETFS_POOL
    netfs_pool['Host']  = u'host_sys.domain.com'
    netfs_pool['SourceDirectory'] = u'/var/lib/images'
    
    disk_pool = dir_pool.copy()
    disk_pool['Type'] = DISK_POOL
    disk_pool['DevicePaths'] = [u'/dev/VolGroup00/LogVol100']
    
    iscsi_pool = dir_pool.copy()
    iscsi_pool['Type'] = ISCSI_POOL
    iscsi_pool['DevicePaths'] = [u'iscsi-target']
    iscsi_pool['Host']  = u'host_sys.domain.com'

    logical_pool = dir_pool.copy()
    logical_pool['Type'] = LOGICAL_POOL

    scsi_pool = dir_pool.copy()
    scsi_pool['Type'] = SCSI_POOL
    scsi_pool['Path'] = '/dev/disk/by-id'

    exp_t_dp_h_sdir_path = [ dir_pool, fs_pool, netfs_pool, disk_pool, 
                             iscsi_pool, logical_pool, scsi_pool ]
    return exp_t_dp_h_sdir_path

def get_rec(diskpool_rasd, inst_id='Default'):
    recs = []
    for dp_rasd in diskpool_rasd:
        if dp_rasd['InstanceID'] == inst_id :
           recs.append(dp_rasd)
    return recs

def cmp_recs(item, rec):
    try:
        for key, val in item.iteritems():
             exp_val = val
             res_val = rec[key]
             if type(val).__name__ == 'list':
                 cmp_exp = (len(Set(res_val) - Set(exp_val)) != 0)
             elif type(val).__name__ != 'NoneType':
                 cmp_exp = (exp_val != res_val)
             elif type(val).__name__ == 'NoneType':
                 continue

             if cmp_exp:
                 raise Exception("Mismatching values, Got %s, "\
                                 "Expected %s" % (res_val, exp_val))
    except Exception, details:
        logger.error("Exception details: %s", details)
        return FAIL

    return PASS

def verify_records(exp_t_dp_h_sdir_path, rec):
    try:
        found = False
        for item in exp_t_dp_h_sdir_path:
            if rec['Type'] == item['Type']:
                status =  cmp_recs(item, rec)
                if status != PASS:
                    raise Exception("Verification failed for '%s'" \
                                     % rec['Type'])
                found = True
    except Exception, details:
        logger.error("Exception details: %s", details)
        return FAIL, found

    return PASS, found


@do_main(sup_types)
def main():
    options = main.options
    virt = options.virt
    server = options.ip
    status, diskpool_rasd = get_pool_rasds(server, virt, pool_type="DiskPool", 
                                           filter_default=False)
    if status != PASS:
        return status
    inst_list = [ 'Default', 'Minimum', 'Maximum', 'Increment' ]

    exp_t_dp_h_sdir_path = init_list()

    for inst_type in inst_list:
        logger.info("Verifying '%s' records", inst_type)

        try:
            n_rec = get_rec(diskpool_rasd, inst_id=inst_type)
            if len(n_rec) != DISKPOOL_REC_LEN:
                raise Exception("Got %s recs instead of %s" %(len(n_rec), 
                                 DISKPOOL_REC_LEN))

            for rec in n_rec:
                status, found = verify_records(exp_t_dp_h_sdir_path, rec)
                if status != PASS or found == False:
                    return FAIL

        except Exception, details:
            logger.error("Exception details: %s", details)
            return FAIL

    return PASS
if __name__ == "__main__":
    sys.exit(main())
