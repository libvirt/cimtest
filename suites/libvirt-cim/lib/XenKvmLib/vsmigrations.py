
# Copyright 2008 IBM Corp.
#
# Authors:
#    Guolian Yun <yunguol@cn.ibm.com>
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

import random
from time import sleep
from  socket import gethostbyaddr
from VirtLib import utils
from pywbem import WBEMConnection, CIMInstanceName
from CimTest.CimExt import CIMMethodClass, CIMClassMOF
from CimTest.ReturnCodes import PASS, FAIL
from XenKvmLib.enumclass import EnumInstances
from XenKvmLib.classes import get_typed_class, virt_types
from XenKvmLib.xm_virt_util import domain_list 
from XenKvmLib.const import get_provider_version
from CimTest.Globals import logger, CIM_USER, CIM_PASS, CIM_NS, \
                            CIM_ERROR_ENUMERATE

# Migration constants
CIM_MIGRATE_OFFLINE=1
CIM_MIGRATE_LIVE=2
CIM_MIGRATE_RESUME=3
CIM_MIGRATE_RESTART=4

CIM_JOBSTATE_STARTING=3
CIM_JOBSTATE_COMPLETE=7
CIM_JOBSTATE_RUNNING=4

libvirt_mig_changes = 668

def eval_cls(basename):
    def func(f):
        def body(virt):
            if virt in virt_types:
                return eval(get_typed_class(virt, basename))
        return body
    return func


class CIM_VirtualSystemMigrationService(CIMMethodClass):
    conn = None
    inst = None

    def __init__(self, server, virt='Xen'):
        self.conn = WBEMConnection('http://%s' % server,
                                  (CIM_USER, CIM_PASS), CIM_NS)

        self.inst = get_typed_class(virt, 'VirtualSystemMigrationService')


@eval_cls('VirtualSystemMigrationService')
def get_vs_mig_setting_class(virt):
    pass

class Xen_VirtualSystemMigrationService(CIM_VirtualSystemMigrationService):
    pass

class KVM_VirtualSystemMigrationService(CIM_VirtualSystemMigrationService):
    pass

# classes to define VirtualSystemMigrationSettingData parameters
class CIM_VirtualSystemMigrationSettingData(CIMClassMOF):
    def __init__(self, type, priority):
        self.InstanceID = 'MigrationSettingData'
        self.CreationClassName = self.__class__.__name__
        self.MigrationType = type 
        self.Priority = priority 

class Xen_VirtualSystemMigrationSettingData(CIM_VirtualSystemMigrationSettingData):
    pass

class KVM_VirtualSystemMigrationSettingData(CIM_VirtualSystemMigrationSettingData):
    pass

def check_mig_support(virt, options):
    s_sysname = gethostbyaddr(options.ip)[0]
    t_sysname = gethostbyaddr(options.t_url)[0]
    if virt == 'KVM' and (t_sysname == s_sysname or t_sysname in s_sysname):
        logger.info("Libvirt does not support local migration for KVM")
        return SKIP, s_sysname, t_sysname

    return PASS, s_sysname, t_sysname


def get_msd(virt, mtype='live', mpriority=0):
    if mtype == "live":
        mtype = CIM_MIGRATE_LIVE
    elif mtype == "resume":
        mtype = CIM_MIGRATE_RESUME
    elif mtype == "restart":
        mtype = CIM_MIGRATE_RESTART
    elif mtype == "offline":
        mtype = CIM_MIGRATE_OFFLINE
    else:
        logger.error("Invalid migration type '%s' specified", mtype)
        return None
    try:
        vsmsd_cn = get_typed_class(virt, "VirtualSystemMigrationSettingData")
        msd = eval(vsmsd_cn)(type=mtype, priority=mpriority)
    except Exception, details:
        logger.error("In get_msd() Exception details: %s", details)
        return None

    return msd.mof()

def get_guest_ref(guest, virt):
    guest_cn = get_typed_class(virt, "ComputerSystem")
    keys = { 'Name' : guest, 'CreationClassName' : guest_cn } 
    cs_ref = None

    try:
        cs_ref = CIMInstanceName(guest_cn, keybindings=keys) 

    except Exception, details:
        logger.error("In fn get_guest_ref() Exception details: %s", details)
        return None

    return cs_ref

#Remove this once vsms.02_host_migrate_type.py uses get_msd()
def default_msd_str(mtype=3, mpriority=0):
    msd = Xen_VirtualSystemMigrationSettingData(type=mtype, 
                                                priority=mpriority)
   
    return msd.mof()

def remote_copy_guest_image(virt, s_sysname, t_sysname, test_dom):
    cn_name = get_typed_class(virt, 'DiskResourceAllocationSettingData')    
    req_image = backup_image = None

    try:
       d_rasds = EnumInstances(s_sysname, cn_name, ret_cim_inst=True)
       for d_rasd in d_rasds:
           if test_dom in d_rasd["InstanceID"]:
               req_image = d_rasd["Address"]
               break

       if req_image == None:
           logger.error("Failed to get Disk RASD info for '%s'", test_dom)
           return FAIL, req_image, backup_image

       if t_sysname == s_sysname or t_sysname in s_sysname:
           #Localhost migration, no need to copy image
           return PASS, req_image, backup_image

       # Check if the image file with the same name already exist on the machine.
       # Back it up. Copy the required working image to the destination.
       cmd = "ls -l %s" % req_image
       rc, out = utils.run_remote(t_sysname, cmd)
       if rc == 0:
           backup_image = req_image + "." + str(random.randint(1, 100))
           cmd = 'mv %s %s' % (req_image, backup_image)
           rc, out = utils.run_remote(t_sysname, cmd)
           if rc != 0:
               backup_image = None
               logger.error("Failed to backup the image '%s' on '%s'", 
                            req_image, t_sysname)
               return FAIL, req_image, backup_image
       
       s, o = utils.copy_remote(t_sysname, req_image, remote=req_image)
       if s != 0:
           logger.error("Failed to copy the image file '%s' for migration"\
                        " to '%s'", req_image, t_sysname) 
           return FAIL, req_image, backup_image

    except Exception, details:
       logger.error("Exception in remote_copy_guest_image()")
       logger.error("Exception details %s", details)
       return FAIL, req_image, backup_image

    return PASS, req_image, backup_image

def check_possible_host_migration(service, cs_ref, ip, msd=None):
    res = None
    try:
        checkfn_name = 'service.CheckVirtualSystemIsMigratableToHost'
        if msd == None:
            res = eval(checkfn_name)(ComputerSystem=cs_ref, DestinationHost=ip)
        else:
            res = eval(checkfn_name)(ComputerSystem=cs_ref,
                                     DestinationHost=ip,
                                     MigrationSettingData=msd)
    except Exception, details:
        logger.error("Error invoke 'CheckVirtualSystemIsMigratableToHost'.")
        logger.error("%s", details)
        return FAIL 

    if res == None or res[1]['IsMigratable'] != True:
        logger.error("Migration check failed")
        return FAIL 

    return PASS 


def migrate_guest_to_host(service, cs_ref, dest_ip, msd=None):
    ret = []
    try:
        if msd == None:
            ret = service.MigrateVirtualSystemToHost(ComputerSystem=cs_ref,
                                                     DestinationHost=dest_ip)
        else:
            ret = service.MigrateVirtualSystemToHost(ComputerSystem=cs_ref,
                                                     DestinationHost=dest_ip,
                                                     MigrationSettingData=msd)
    except Exception, details:
        logger.error("Failed to invoke method 'MigrateVirtualSystemToHost'.")
        logger.error("Exception in fn migrate_guest_to_host() %s", details)
        return FAIL, ret

    if len(ret) == 0:
        logger.error("MigrateVirtualSystemToHost returns an empty list")
        return FAIL, ret

    return PASS, ret

def get_migration_job_instance(src_ip, virt, id):
    job = []
    curr_cim_rev, changeset = get_provider_version(virt, src_ip)
    if curr_cim_rev < libvirt_mig_changes:
        mig_job_cn   =  'Virt_MigrationJob'
    else:
        mig_job_cn   = get_typed_class(virt, 'MigrationJob')

    try:
        job = EnumInstances(src_ip, mig_job_cn)
        if len(job) < 1:
            logger.error("'%s' returned empty list", mig_job_cn)
            return FAIL, None

        for i in range(0, len(job)):
            if job[i].InstanceID == id:
                break
            elif i == len(job)-1 and job[i].InstanceID != id:
                logger.error("%s err: can't find expected job inst", mig_job_cn)
                return FAIL, None
    except Exception, details:
        logger.error(CIM_ERROR_ENUMERATE, mig_job_cn)
        logger.error("Exception in fn get_migration_job_instance() " \
                     "details: %s", details)
        return FAIL, None

    return PASS, job[i]

def verify_domain_list(virt, remote_migrate, test_dom, src_ip, target_ip):
    status = FAIL
    list_src = domain_list(src_ip, virt)
    if remote_migrate == 0:
        if test_dom in list_src:
            status = PASS
    elif remote_migrate == 1 :
        list_target = domain_list(target_ip, virt)
        if test_dom not in list_src and test_dom in list_target:
            status = PASS
    else:
        logger.error("Invalid migration option")

    if status != PASS:
        logger.error("Migration verification for '%s' failed", test_dom)
        return status 

    return status

def check_migration_job(src_ip, id, target_ip, test_dom, 
                        remote_migrate, virt='Xen', timeout=50):
    try:
        status, job_inst = get_migration_job_instance(src_ip, virt, id)
        if status != PASS:
            logger.error("Unable to get mig_job instance for '%s'", test_dom)
            return FAIL

        status = FAIL

        for i in range(0, timeout):
            if job_inst.JobState == CIM_JOBSTATE_COMPLETE:
                sleep(3)
                if job_inst.Status != "Completed":
                    logger.error("JobStatus for dom '%s' has '%s' instead of "\
                                 "'Completed'", test_dom, job_inst.Status)
                    return FAIL
                else:
                    status = verify_domain_list(virt, remote_migrate, test_dom, 
                                                src_ip, target_ip)
                    if status != FAIL:
                         logger.info("Migration for '%s' succeeded.", test_dom)
                         logger.info("Migration job status is : %s", 
                                      job_inst.Status)
                    return status
            elif job_inst.JobState == CIM_JOBSTATE_RUNNING and i < (timeout-1):
                sleep(3)
                status, job_inst = get_migration_job_instance(src_ip, virt, id)
                if status != PASS:
                    logger.error("Could not get mig_job instance for '%s'", 
                                  test_dom)
                    return status  
            else:
                logger.error("Migration timed out.... ")
                logger.error("Increase timeout > %s and try again..", timeout)
                return FAIL

    except Exception, details:
        logger.error("In check_migration_job() Exception details: %s", details)
        return  FAIL


def cleanup_image(backup_image, req_image, t_sysname, remote_migrate=1):
    # Make sure we do not remove the images on the local machine
    if remote_migrate == 1:
        # Cleanup the images that is copied on the remote machine
        cmd = "rm -rf %s" % req_image
        rc, out = utils.run_remote(t_sysname, cmd)
        if rc != 0:
            logger.info("Failed to remove the copied image '%s' from '%s'",
                         req_image, t_sysname)

        # Copy the backed up image if any on the remote machine
        if backup_image != None:
            cmd = 'mv  %s %s' % (backup_image, req_image)
            rc, out = utils.run_remote(t_sysname, cmd)
            if rc != 0:
                logger.info("Failed to restore the original backed up image" \
                            "'%s' on '%s'", backup_image, t_sysname)

# Desc:
# Fn Name : local_remote_migrate()
#
# Parameters:
# This fn executes local/remote migration depending on the 
# value of remote_migrate. 
# Parameters used:
# vsmservice = VSMigrationService Instance
# s_sysname = src host on which migration is initiated
# t_sysname = Target machine for migration
# virt = Xen, KVM
# remote_migrate = 1 [for remote migration, 0 for local]
# mtype = live/resume/offline/restart
# mpriority=0 by default
# guest_name = name of the guest to be migrated
# time_out = time for which migration is tried.
#
def local_remote_migrate(s_sysname, t_sysname, virt='KVM', 
                         remote_migrate=1, mtype='live', mpriority=0,
                         guest_name=None, time_out=40):

    if guest_name == None:
        logger.error("Guest to be migrated not specified.")
        return FAIL 

    try:
        if remote_migrate == 1:
            status, req_image, backup_image = remote_copy_guest_image(virt, 
                                                                      s_sysname, 
                                                                      t_sysname,
                                                                      guest_name)
            if status != PASS:
                raise Exception("Failure from remote_copy_guest_image()")

        # Get the guest ref
        guest_ref = get_guest_ref(guest_name, virt)
        if guest_ref == None or guest_ref['Name']  != guest_name:
            raise Exception ("Failed to get the guest refernce to be migrated")

        # Get MigrationSettingData information
        msd = get_msd(virt, mtype, mpriority)
        if msd == None:
            raise Exception("No MigrationSettingData details found")

        # Get VirtualSystemMigrationService object
        vsms_cn = get_vs_mig_setting_class(virt)
        vsmservice = vsms_cn(s_sysname, virt)

        # Verify if destination(t_sysname) can be used for migration
        status = check_possible_host_migration(vsmservice, guest_ref, 
                                               t_sysname, msd) 
        if status != PASS:
            raise Exception("Failed to verify Migration support on host '%s'" \
                             % t_sysname)

        logger.info("Migrating '%s'.. this will take some time.",  guest_name)

        # Migrate the guest to t_sysname
        status, ret = migrate_guest_to_host(vsmservice, guest_ref, t_sysname, msd)
        if status == FAIL:
            raise Exception("Failed to Migrate guest '%s' from '%s' to '%s'" \
                            % (guest_name, s_sysname, t_sysname))
        elif len(ret) == 2:
            id = ret[1]['Job'].keybindings['InstanceID']

        # Verify if migration status
        status =  check_migration_job(s_sysname, id, t_sysname, guest_name, 
                                      remote_migrate, virt, timeout=time_out)

    except Exception, details:
        logger.error("Exception in local_remote_migrate()")
        logger.error("Exception details %s", details)
        status = FAIL

    cleanup_image(backup_image, req_image, t_sysname, remote_migrate=1)
    return status
