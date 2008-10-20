
# Copyright 2008 IBM Corp.
#
# Authors:
#    Guolian Yun <yunguol@cn.ibm.com>
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
import pywbem
import time
from CimTest.CimExt import CIMMethodClass, CIMClassMOF
from CimTest.Globals import logger, CIM_USER, CIM_PASS, CIM_NS
from CimTest.ReturnCodes import PASS, FAIL
from XenKvmLib.test_doms import destroy_and_undefine_domain
from CimTest.Globals import logger, CIM_ERROR_ENUMERATE
from XenKvmLib import enumclass
from XenKvmLib.classes import get_typed_class
from VirtLib.live import domain_list 

class CIM_VirtualSystemMigrationService(CIMMethodClass):
    conn = None
    inst = None

    def __init__(self, server, hyp):
        self.conn = pywbem.WBEMConnection('http://%s' % server,
                                          (CIM_USER, CIM_PASS), CIM_NS)

        self.inst = hyp + '_VirtualSystemMigrationService'


class Xen_VirtualSystemMigrationService(CIM_VirtualSystemMigrationService):
    def __init__(self, server):
        CIM_VirtualSystemMigrationService.__init__(self, server, 'Xen')

# classes to define VirtualSystemMigrationSettingData parameters
class CIM_VirtualSystemMigrationSettingData(CIMClassMOF):
    def __init__(self, type, priority):
        self.InstanceID = 'MigrationSettingData'
        self.CreationClassName = self.__class__.__name__
        self.MigrationType = type 
        self.Priority = priority 

class Xen_VirtualSystemMigrationSettingData(CIM_VirtualSystemMigrationSettingData):
    def __init__(self, type, priority):
        CIM_VirtualSystemMigrationSettingData.__init__(self, type, 
                                                       priority)

class KVM_VirtualSystemMigrationSettingData(CIM_VirtualSystemMigrationSettingData):
    def __init__(self, type, priority):
        CIM_VirtualSystemMigrationSettingData.__init__(self, type, 
                                                       priority)

def default_msd_str(mtype=3, mpriority=0):
    msd = Xen_VirtualSystemMigrationSettingData(type=mtype, 
                                                priority=mpriority)
   
    return msd.mof()

def check_possible_host_migration(service, cs_ref, ip):
    rc = None
    try:
        rc = service.CheckVirtualSystemIsMigratableToHost(ComputerSystem=cs_ref,
                                                          DestinationHost=ip)
    except Exception, details:
        logger.error("Error invoke 'CheckVirtualSystemIsMigratableToHost\'.")
        logger.error("%s" % details)
        return FAIL 

    if rc == None or rc[1]['IsMigratable'] != True:
        return FAIL 

    return PASS 

def migrate_guest_to_host(service, ref, ip, msd=None):
    ret = []
    try:
        if msd == None:
            ret = service.MigrateVirtualSystemToHost(ComputerSystem=ref,
                                                     DestinationHost=ip)
        else:
            ret = service.MigrateVirtualSystemToHost(ComputerSystem=ref,
                                                     DestinationHost=ip,
                                                     MigrationSettingData=msd)
    except Exception, details:
        logger.error("Error invoke method 'MigrateVirtualSystemToHost\'.")
        logger.error("%s", details)
        return FAIL, ret

    if len(ret) == 0:
        logger.error("MigrateVirtualSystemToHost returns an empty list")
        return FAIL, ret
    return PASS, ret

def get_migration_job_instance(ip, virt, id):
    job = []
    key_list = ["instanceid"]
    mig_job_cn   = get_typed_class(virt, 'MigrationJob')
    try:
        job = enumclass.EnumInstances(ip, mig_job_cn)
    except Exception, details:
        logger.error(CIM_ERROR_ENUMERATE, mig_job_cn)
        logger.error(details)
        return FAIL, None

    if len(job) < 1:
        return FAIL, None

    for i in range(0, len(job)):
        if job[i].InstanceID == id:
            break
        elif i == len(job)-1 and job[i].InstanceID != id:
            logger.error("%s err: can't find expected job inst", mig_job_cn)
            return FAIL, None

    return PASS, job[i]

def verify_domain_list(list, local_migrate, test_dom):
    status = PASS
    if local_migrate == 0 and test_dom not in list:
        status = FAIL
    if local_migrate == 1 and test_dom in list:
        status = FAIL

    if status != PASS:
        logger.error("%s migrate failed" % test_dom)
        return FAIL

    return PASS

def check_migration_job(ip, id, target_ip, test_dom, local_migrate, virt='Xen'):
    status, job_inst = get_migration_job_instance(ip, virt, id)
    if status != PASS:
        return FAIL

    for i in range(0, 50):
        if job_inst.JobState == 7:
            if job_inst.Status != "Completed":
                logger.error("%s migrate failed" % test_dom)
                return FAIL
            list_after = domain_list(ip)
            status = verify_domain_list(list_after, local_migrate, test_dom)
            break
        elif job_inst.JobState == 4 and i < 49:
            time.sleep(3)
            status, job_inst = get_migration_job_instance(ip, virt, id)
            if status != PASS:
                return FAIL
        else:
            logger.error("MigrateVirtualSystemToHost took too long")
            return FAIL

    return PASS

