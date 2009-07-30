#!/usr/bin/python
#
# Copyright 2009 IBM Corp.
#
# Authors:
#    Deepti B. Kalakeri<dkalaker@in.ibm.com> 
#    
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
# This test case should test the  CreateChildResourcePool service 
# supplied by the RPCS provider. 
# This tc verifies the FileSystem Type storage pool.
#
# The test case is not run in the batch run and we need to run it using 
# the following command:
# For Fs pool type:
# ----------------
# python create_verify_storagepool.py -t fs -d /dev/sda4 -m /tmp/mnt -n fs_pool
#         -v Xen -u <username> -p <passwd>
#
# For disk pool type:
# -------------------
# python create_verify_storagepool.py -t fs -d /dev/sda -m /tmp/ -n disk_pool 
#         -v Xen -u <username> -p <passwd>
# 
# For logical pool type:
# ----------------------
# python create_verify_storagepool.py -t logical -d /dev/VolGroup01
# -n VolGroup01 -v Xen -u <username> -p  <passwd>  
#
# For scsi pool type with HBA's:
# ------------------------------
# python create_verify_storagepool.py -t scsi -v KVM -u <username> -p <passwd>
# -n scsi_pool -a host2  
#
# Where t can be :
#       2 - fs [ FileSystem ]
#       4 - disk [ Disk ]
#       6 - logical [ Logical ]
#       7 - scsi 
# 
# 
#                                                         Date : 27.06.2009

import os
import sys
from optparse import OptionParser
from commands  import getstatusoutput
from distutils.text_file import TextFile
from pywbem import WBEMConnection, cim_types, CIMInstanceName
sys.path.append('../../../lib')
from CimTest import Globals
from CimTest.Globals import logger, log_param
from CimTest.ReturnCodes import PASS, FAIL, SKIP
sys.path.append('../lib')
from XenKvmLib.classes import inst_to_mof, get_typed_class
from XenKvmLib.pool import get_pool_rasds
from XenKvmLib.common_util import pre_check
from XenKvmLib.enumclass import EnumInstances
from XenKvmLib.const import get_provider_version

TEST_LOG="cimtest.log"
libvirt_cim_fs_changes = 857
libvirt_cim_disk_changes = 872
libvirt_cim_logical_changes = 906
libvirt_cim_scsi_changes = 921


supp_types = [ 'Xen', 'KVM' , 'LXC' ]
pool_types = { 'DISK_POOL_FS' : 2 , 'DISK_POOL_DISK' : 4, 
               'DISK_POOL_LOGICAL' : 6 , 'DISK_POOL_SCSI' : 7 }

def verify_cmd_options(options, parser):
    try: 
        if options.pool_name == None:
            raise Exception("Must specify the Pool Name to be created")

        if options.virt == None or options.virt not in supp_types:
            raise Exception("Must specify virtualization type")

        if options.pool_type == None:
            raise Exception("Must specify pool type to be tested")

        if options.part_dev == None and options.pool_type != 'scsi':
            raise Exception("Free Partition/disk to be mounted not specified")

        if options.mnt_pt == None and (options.pool_type == 'fs' or \
           options.pool_type == 'disk'):
            raise Exception("Mount points to be used not specified")

        if options.adap_name == None and options.pool_type == 'scsi':
            raise Exception("Adapter name used not specified")

    except Exception, details:
        print "\nFATAL: ", details , "\n"
        print parser.print_help()
        return FAIL

    return PASS

def env_setup(sysname, virt, clean, debug):
    env_ready = pre_check(sysname, virt)
    if env_ready != None: 
        print "\n%s.  Please check your environment.\n" % env_ready
        return FAIL

    if clean:
        cmd = "rm -f %s" % (os.path.join(os.getcwd(), TEST_LOG))
        status, output = getstatusoutput(cmd)

    if debug:
        dbg = "-d"
    else:
        dbg = ""

    return PASS

def get_pooltype(pooltype, virt):

    if pooltype == "fs":
       pool_type = pool_types['DISK_POOL_FS']
    elif pooltype == "disk":
       pool_type = pool_types['DISK_POOL_DISK']
    elif pooltype == "logical":
       pool_type = pool_types['DISK_POOL_LOGICAL']
    elif pooltype == "scsi":
       pool_type = pool_types['DISK_POOL_SCSI']
    else:
       logger.error("Invalid pool type ....")
       return None, None

    return PASS, pool_type

def verify_inputs(part_dev, mount_pt, pool_type, pool_name, adap_name):

    del_dir = False   

    if pool_type == pool_types['DISK_POOL_FS'] or \
       pool_type == pool_types['DISK_POOL_DISK']:

        if pool_type == pool_types['DISK_POOL_DISK']:
           # Make sure part_dev is a disk and not a partition
           cmd = "fdisk -l | grep -w '%s'" % part_dev
           status, disk_info = getstatusoutput(cmd)
           if status != PASS:
              logger.error("'%s' does not seem like a disk", part_dev)
              return FAIL, del_dir

        cmd = "mount"
        status, mount_info = getstatusoutput(cmd)
        if status != PASS:
            logger.error("Failed to get mount info.. ")
            return FAIL, del_dir
     
        for line in mount_info.split('\n'):
            try:
                # Check if the specified partition is mounted before using it 
                part_name = line.split()[0]
                if part_dev == part_name:
                    logger.error("[%s] already mounted", part_dev)
                    raise Exception("Please specify free partition/disk other "
                                    "than [%s]" % part_dev)

                # Check if mount point is already used for mounting
                mount_name = line.split()[2]
                if mount_pt == mount_name:
                    logger.error("[%s] already mounted", mount_pt)
                    raise Exception("Please specify dir other than [%s]" \
                                     % mount_pt)

            except Exception, details:
                logger.error("%s", details)
                return FAIL, del_dir

        # Check if the mount point specified already exist, if not create it..
        if not os.path.exists(mount_pt):
            os.mkdir(mount_pt)

            # set del_dir=True so that we remove it before exiting from the tc.
            del_dir = True 
        else:
            # Check if the mount point specified is a dir
            if not os.path.isdir(mount_pt):
                logger.error("The mount point [%s] should be a dir", mount_pt)
                return FAIL, del_dir

            files = os.listdir(mount_pt)
            if len(files) != 0:
                logger.info("The mount point [%s] given is not empty",
                              mount_pt)

    elif pool_type == pool_types['DISK_POOL_LOGICAL']:
        if not os.path.exists("/sbin/lvm"):
            logger.error("LVM support does not exist on the machine")
            return FAIL, del_dir

        cmd = "lvm vgs | sed '1 d' 2>>/dev/null"
        status, output = getstatusoutput(cmd) 
        if status != PASS:
            logger.error("Failed to get lvm output")
            return FAIL, del_dir

        vgname_list =  []
        for line in output.split('\n'):
            vgname_list.append(line.split()[0])

        if not pool_name in vgname_list:
            logger.error("Please specify existing VolGroup for Poolname")
            return FAIL, del_dir

        return PASS, del_dir

    elif pool_type == pool_types['DISK_POOL_SCSI']:
        hba_path = "/sys/class/scsi_host/"
        adap_path = "%s%s" % (hba_path, adap_name)
        if not os.path.exists(adap_path):
            logger.error("HBA '%s' does not exist on the machine, specify "\
                         "one present in '%s' path", adap_path, hba_path)
            return FAIL, del_dir 

    return PASS, del_dir

def get_uri(virt):
    if virt == 'Xen':
        vuri = 'xen:///'
    elif virt == 'KVM':
        vuri = 'qemu:///system'
    elif virt == 'LXC':
        vuri = 'lxc:///system'
    return vuri

def get_pool_settings(dp_rasds, pooltype, part_dev, mount_pt, 
                      pool_name, adap_name):
    pool_settings = None

    for dpool_rasd in dp_rasds:

        if dpool_rasd['Type'] == pooltype and \
            dpool_rasd['InstanceID'] == 'Default':

            dp_pid = "%s/%s" % ("DiskPool", pool_name)
            dpool_rasd['PoolID'] = dpool_rasd['InstanceID'] = dp_pid

            if pooltype == pool_types['DISK_POOL_FS'] or \
               pooltype == pool_types['DISK_POOL_DISK']:
                dpool_rasd['DevicePaths'] = [part_dev]
                dpool_rasd['Path'] = mount_pt

            elif pooltype == pool_types['DISK_POOL_LOGICAL']:
                dpool_rasd['Path'] = part_dev

            elif pooltype == pool_types['DISK_POOL_SCSI']:
                dpool_rasd['AdapterName'] = adap_name
                dpool_rasd['Path'] = "/dev/disk/by-id"
            break

    if not pool_name in dpool_rasd['InstanceID']:
        return pool_settings

    pool_settings = inst_to_mof(dpool_rasd)
    return pool_settings


def verify_pool(sysname, virt, pool_name, dp_cn):
    try:
        pool = EnumInstances(sysname, dp_cn)
        for dpool in pool:
            ret_pool = dpool.InstanceID
            if pool_name == ret_pool: 
               logger.info("Found the pool '%s'", pool_name)
               return PASS
    except Exception, details:
        logger.error("Exception details: %s", details)

    return FAIL

def cleanup(virt, rpcs_conn, rpcs_cn, dp_cn, dp_id, 
            pool_name, sysname, mount_pt, del_dir, res):

    if res == PASS:
        pool_settings = CIMInstanceName(dp_cn, namespace=Globals.CIM_NS, 
                                        keybindings = {'InstanceID': dp_id})
        rpcs_conn.InvokeMethod("DeleteResourcePool",
                               rpcs_cn,
                               Pool = pool_settings)
        pool = EnumInstances(sysname, dp_cn)
        for dpool in pool:
            ret_pool = dpool.InstanceID
            if ret_pool == dp_id:
                logger.error("Failed to delete diskpool '%s'", pool_name)
                return FAIL

    if del_dir == True:
        cmd ="rm -rf %s"  % mount_pt
        ret, out = getstatusoutput(cmd)
        if ret != PASS:
            logger.error("WARNING: '%s' was not removed", mount_pt)
            logger.error("WARNING: Please remove %s manually", mount_pt)

    return PASS


def main():
    usage = "usage: %prog [options] \nex: %prog -i localhost"
    parser = OptionParser(usage)

    parser.add_option("-i", "--host-url", dest="h_url", default="localhost:5988",
                      help="URL of CIMOM to connect to (host:port)")
    parser.add_option("-N", "--ns", dest="ns", default="root/virt",
                      help="Namespace (default is root/virt)")
    parser.add_option("-u", "--user", dest="username", default=None,
                      help="Auth username for CIMOM on source system")
    parser.add_option("-p", "--pass", dest="password", default=None,
                      help="Auth password for CIMOM on source system")
    parser.add_option("-v", "--virt-type", dest="virt", default=None,
                      help="Virtualization type [ Xen | KVM ]")
    parser.add_option("-t", "--pool-type", dest="pool_type", default=None,
                      help="Pool type:[ fs | logical | scsi | disk ]")
    parser.add_option("-d", "--part-dev", dest="part_dev", default=None,
                      help="specify the free partition to be used for " \
                           "fs pool type or the predefined Vol Group" \
                           " for logical pool type or empty disk like" \
                           " /dev/sda for disk type pools")
    parser.add_option("-m", "--mnt_pt", dest="mnt_pt", default=None, 
                      help="Mount point to be used")
    parser.add_option("-n", "--pool-name", dest="pool_name", default=None, 
                      help="Pool to be created")
    parser.add_option("-a", "--adap_name", dest="adap_name", default=None, 
                      help="Adap name to be used Ex: specify one of the host" \
                           "in /sys/class/scsi_host/ like host0")
    parser.add_option("-c", "--clean-log",  action="store_true", dest="clean",
                      help="Will remove existing log files before test run")
    parser.add_option("-l", "--debug-output", action="store_true", dest="debug",
                      help="Duplicate the output to stderr")

    (options, args) = parser.parse_args()

    # Verify command line options
    status = verify_cmd_options(options, parser)
    if status != PASS:
       return status
    
    part_dev = options.part_dev
    mount_pt = options.mnt_pt
    pool_name = options.pool_name
    adap_name = options.adap_name
    virt = options.virt

    if ":" in options.h_url:
        (sysname, port) = options.h_url.split(":")
    else:
        sysname = options.h_url

    # Verify if the CIMOM is running, if requested clean cimtest.log.
    # Set Debug option if requested
    status = env_setup(sysname, virt, options.clean, options.debug)
    if status != PASS:
       return status

    log_param(file_name=TEST_LOG)

    print "Please check cimtest.log in the curr dir for debug log msgs..."

    status, pooltype = get_pooltype(options.pool_type, virt)
    if status != PASS:
       return FAIL

    os.environ['CIM_NS'] = Globals.CIM_NS = options.ns
    os.environ['CIM_USER'] = Globals.CIM_USER = options.username
    os.environ['CIM_PASS'] = Globals.CIM_PASS = options.password

    curr_cim_rev, changeset = get_provider_version(virt, sysname)
    if curr_cim_rev < libvirt_cim_fs_changes and \
       pooltype == pool_types['DISK_POOL_FS']:
       logger.info("Test Skipped for '%s' pool type, Support for File System "
                    "Pool is available in revision '%s'",  options.pool_type, 
                    libvirt_cim_fs_changes)
       return SKIP

    elif curr_cim_rev < libvirt_cim_disk_changes and \
        pooltype == pool_types['DISK_POOL_DISK']:
       logger.info("Test Skipped for '%s' pool type, Support for disk Pool" 
                   " is available in revision '%s'",  options.pool_type, 
                   libvirt_cim_disk_changes)
       return SKIP

    elif curr_cim_rev < libvirt_cim_logical_changes and \
        pooltype == pool_types['DISK_POOL_LOGICAL']:
       logger.info("Test Skipped for '%s' pool type, Support for Logical Pool" 
                   " is available in revision '%s'",  options.pool_type, 
                   libvirt_cim_logical_changes)
       return SKIP

    elif curr_cim_rev < libvirt_cim_scsi_changes and \
        pooltype == pool_types['DISK_POOL_SCSI']:
       logger.info("Test Skipped for '%s' pool type, Support for scsi Pool" 
                   " is available in revision '%s'",  options.pool_type, 
                   libvirt_cim_scsi_changes)
       return SKIP
   
    pooltype = cim_types.Uint16(pooltype)

    status, del_dir = verify_inputs(part_dev, mount_pt, pooltype, pool_name, 
                                    adap_name)
    if status != PASS:
        if del_dir == True:
            cmd ="rm -rf %s" % mount_pt
            status, out = getstatusoutput(cmd)
        logger.error("Input verification failed")
        return status

    cn = "DiskPool"
    dp_cn = get_typed_class(virt, cn)
    dp_id = "%s/%s" % (cn, pool_name) 
    rpcs_cn = get_typed_class(virt, "ResourcePoolConfigurationService")

    status = verify_pool(sysname, virt, dp_id, dp_cn)
    if status == PASS:
        logger.error("Pool --> '%s' already exist", pool_name)
        logger.error("Specify some other pool name")
        if del_dir == True:
            cmd ="rm -rf %s" % mount_pt
            status, out = getstatusoutput(cmd)
        return status

    res = [FAIL]
    try:
        src_conn = WBEMConnection('http://%s' % sysname, (options.username, 
                                   options.password), options.ns)
   
        # Get DiskPoolRASD's from SDC association with AC of DiskPool/0
        status, dp_rasds = get_pool_rasds(sysname, virt, cn)
        if status != PASS:
           raise Exception("Failed to get DiskPool Rasd's")

        # Get the DiskPoolRASD mof with appropriate values of diskpool 
        # to be created....
        pool_settings = get_pool_settings(dp_rasds, pooltype, part_dev, 
                                          mount_pt, pool_name, adap_name)
        if pool_settings == None:
            raise Exception("Did not get the required pool settings ...")

        # Create DiskPool..
        res = src_conn.InvokeMethod("CreateChildResourcePool",
                                    rpcs_cn,
                                    Settings=[pool_settings],
                                    ElementName=pool_name)

    except Exception, details:
        logger.error("In main(), exception '%s'", details)

    # Verify if the desired pool was successfully created ..
    if res[0] == PASS:
        status = verify_pool(sysname, virt, dp_id, dp_cn)
        if status != PASS:
            logger.error("Failed to verify pool: %s " % pool_name)

    # Clean up the pool and the mount dir that was created ...
    status = cleanup(virt, src_conn, rpcs_cn, dp_cn, dp_id,
                      pool_name, sysname, mount_pt, del_dir, res[0])

    if res[0] == PASS and status == PASS:
        logger.info("Pool %s was successfully verified for pool type %s", 
                    pool_name , options.pool_type)

        # Place holder to give a hint to the user the tc passed 
        # otherwise the user will have to look into the cimtest.log in the 
        # current dir.
        print "Pool '", pool_name,"' was successfully verified for pool type "\
              "'", options.pool_type , "'"
        return PASS
    else:
        logger.error("Test Failed to verify '%s' pool creation ....", 
                     options.pool_type)
        return FAIL
if __name__=="__main__":
    sys.exit(main())

