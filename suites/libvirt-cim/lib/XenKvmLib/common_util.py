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
import os
import pywbem
import random
from time import sleep
from distutils.file_util import move_file
from XenKvmLib.test_xml import * 
from XenKvmLib.test_doms import * 
from XenKvmLib import vsms 
from XenKvmLib import computersystem 
from XenKvmLib import hostsystem 
from pywbem.cim_obj import CIMInstanceName
from XenKvmLib.devices import CIM_Instance
from XenKvmLib.classes import get_typed_class
from CimTest.Globals import logger, log_param, CIM_ERROR_ENUMERATE
from CimTest.ReturnCodes import PASS, FAIL, XFAIL_RC
from VirtLib.live import diskpool_list, virsh_version, net_list
from XenKvmLib.vxml import PoolXML, NetXML

test_dpath = "foo"
disk_file = '/etc/libvirt/diskpool.conf'

back_disk_file = disk_file + "." + "backup"

def print_field_error(fieldname, ret_value, exp_value):
    logger.error("%s Mismatch", fieldname)
    logger.error("Returned %s instead of %s", ret_value, exp_value)

def get_cs_instance(domain_name, ip, virt='Xen'):
    cs = None
    try:
        cs = computersystem.get_cs_class(virt)(ip, domain_name)

        if cs.Name != domain_name:
            logger.error("VS %s is not found" % domain_name)
            return (1, cs)

    except Exception, detail:
        logger.error(Globals.CIM_ERROR_GETINSTANCE, 
                     get_typed_class(virt, 'ComputerSystem'))
        logger.error("Exception: %s", detail)
        return (1, cs) 

    return (0, cs) 

def create_using_definesystem(domain_name, ip, 
                              params=None, exp_err=None, virt='Xen'):
    bug = "85673"
    try:
        class_vsms = eval('vsms.' + \
                get_typed_class(virt, 'VirtualSystemManagementService'))
        service = class_vsms(ip)

        if params == None or len(params) == 0:
            vssd, rasd = vsms.default_vssd_rasd_str(
                            dom_name=domain_name, virt=virt)
        else:
            vssd = params['vssd']
            rasd = params['rasd']

        if exp_err == None or len(exp_err) == 0:
            exp_rc = 0
            exp_desc = ''

        else:
            exp_rc = exp_err['exp_rc']
            exp_desc = exp_err['exp_desc'] 

        service.DefineSystem(SystemSettings=vssd,
                             ResourceSettings=rasd,
                             ReferenceConfiguration=' ')
    except pywbem.CIMError, (rc, desc):
        if rc == exp_rc and desc.find(exp_desc) >= 0:
            logger.info('Got expected rc code and error string.')
            if exp_err != None:
                return PASS
            return FAIL

        logger.error('Unexpected rc code %s and description:\n %s' % (rc, desc))
        return FAIL

    except Exception, details:
        logger.error('Error invoke method `DefineSystem\'.  %s' % details)
        return FAIL 

    if exp_err != None:    
        logger.error('DefineSystem should NOT return OK with invalid arg')
        undefine_test_domain(dname, options.ip, virt=virt)
        return XFAIL_RC(bug)

    set_uuid(viruuid(domain_name, ip, virt=virt))
    myxml = dumpxml(domain_name, ip, virt=virt)

    name = xml_get_dom_name(myxml)

    if name != domain_name:
        logger.error ("Name should be '%s' instead of '%s'",
                      domain_name, name)
        undefine_test_domain(name, ip, virt=virt)
        return FAIL

    return PASS 

def call_request_state_change(domain_name, ip, rs, time, virt='Xen'):
    rc, cs = get_cs_instance(domain_name, ip, virt)
    if rc != 0:
        return 1 

    try:
        cs.RequestStateChange(RequestedState=pywbem.cim_types.Uint16(rs),
                              TimeoutPeriod=pywbem.cim_types.CIMDateTime(time))

    except Exception, detail:
        logger.error("Exception: %s" % detail)
        return 1

    return 0 

def poll_for_state_change(server, virt, dom, exp_state, timeout=30):
    cs = computersystem.get_cs_class(virt)

    try:
        for i in range(1, (timeout + 1)):
            sleep(1)
            dom_cs = cs(server, name=dom)
            if dom_cs is None or dom_cs.Name != dom:
                logger.error("CS instance not returned for %s." % dom)
                return FAIL

            if dom_cs.EnabledState == exp_state:
                break

    except Exception, detail:
        logger.error("Exception: %s" % detail)
        return FAIL

    if dom_cs.EnabledState != exp_state:
        logger.error("EnabledState is %i instead of %i." % (dom_cs.EnabledState,
                     exp_state))
        logger.error("Try to increase the timeout and run the test again")
        return FAIL

    return PASS 

def get_host_info(server, virt="Xen"):
    status = PASS
    host_name = ''
    host_ccn  = ''
    try :
        host_sys = hostsystem.enumerate(server, virt)
        if host_sys[0].Name == "":
            logger.error("HostName seems to be empty")
            status = FAIL
        else:
        # Instance of the HostSystem
            host_sys = host_sys[0]
            host_ccn = host_sys.CreationClassName
            host_name = host_sys.Name
    except Exception, detail:
        logger.error(CIM_ERROR_ENUMERATE, 'HostSystem')
        logger.error("Exception: %s", detail)
        status = FAIL
    return status, host_name, host_ccn

def try_assoc(conn, classname, assoc_classname, keys, field_name, \
                                              expr_values, bug_no):
    assoc_info = []
    instanceref = CIMInstanceName(classname, keybindings=keys)
    logger.info ("Instanceref is '%s'", instanceref)
    try:
        assoc_info = conn.AssociatorNames(instanceref, \
                             AssocClass=assoc_classname)
    except pywbem.CIMError, (err_no, desc):
        exp_rc    = expr_values['rc']
        exp_desc  = expr_values['desc']
        if err_no == exp_rc and desc.find(exp_desc) >= 0:
            logger.info("Got expected exception where ")
            logger.info("Errno is '%s' ", exp_rc)
            logger.info("Error string is '%s'", exp_desc)
            return PASS
        else:
            logger.error("Unexpected rc code %s and description %s\n" \
                                                       %(err_no, desc))
            return FAIL
    logger.error("'%s' association failed to generate an exception and \
'%s' passed.", assoc_classname, field_name)
    return XFAIL_RC(bug_no)

def try_getinstance(conn, classname, keys, field_name, expr_values, bug_no):
    inst = None
    try:
        instanceref = CIMInstanceName(classname, keybindings=keys)
        logger.info ("Instanceref is '%s'", instanceref)
        inst = conn.GetInstance(instanceref)
    except pywbem.CIMError, (err_no, desc):
        exp_rc    = expr_values['rc']
        exp_desc  = expr_values['desc']
        if err_no == exp_rc and desc.find(exp_desc) >= 0:
            logger.info("Got expected exception where ")
            logger.info("Errno is '%s' ", exp_rc)
            logger.info("Error string is '%s'", exp_desc)
            return PASS
        else:
            logger.error("Unexpected rc code %s and description %s\n" \
                                                       %(err_no, desc))
            return FAIL
    logger.error("'%s' GetInstance failed to generate an exception and \
'%s' passed.", classname, field_name)
    return XFAIL_RC(bug_no)

def profile_init_list():
    sys_prof_info = {
                       "InstanceID"              : "CIM:DSP1042-SystemVirtualization-1.0.0", 
                       "RegisteredOrganization"  : 2, 
                       "RegisteredName"          : "System Virtualization", 
                       "RegisteredVersion"       : "1.0.0"
                    }
    vs_prof   =       {
                          "InstanceID"              : "CIM:DSP1057-VirtualSystem-1.0.0a",
                          "RegisteredOrganization"  : 2, 
                          "RegisteredName"          : "Virtual System Profile",
                          "RegisteredVersion"       : "1.0.0a"
                      }
    gen_dev_prof   =  {
                          "InstanceID"              : 
                              "CIM:DSP1059-GenericDeviceResourceVirtualization-1.0.0",
                          "RegisteredOrganization"  : 2, 
                          "RegisteredName"          : "Generic Device Resource Virtualization",
                          "RegisteredVersion"       : "1.0.0"
                      }
    mem_res_prof   =  {
                          "InstanceID"              : "CIM:DSP1045-MemoryResourceVirtualization-1.0.0",
                          "RegisteredOrganization"  : 2, 
                          "RegisteredName"          : "Memory Resource Virtualization",
                          "RegisteredVersion"       : "1.0.0"
                      }
    vs_mig_prof   =  {
                          "InstanceID"              : "CIM:DSP1081-VirtualSystemMigration-1.0",
                          "RegisteredOrganization"  : 2, 
                          "RegisteredName"          : "Virtual System Migration",
                          "RegisteredVersion"       : "1.0"
                     }
     
    profiles = {

                 'DSP1042'       : sys_prof_info,
                 'DSP1045'       : mem_res_prof,
                 'DSP1057'       : vs_prof,
                 'DSP1059'       : gen_dev_prof,
                 'DSP1081'       : vs_mig_prof
               } 
    
    return profiles 

def conf_file():
    """
       Creating diskpool.conf file.
    """
    status = PASS
    logger.info("Disk conf file : %s", disk_file)
    try:
        f = open(disk_file, 'w')
        f.write('%s %s' % (test_dpath, '/'))
        f.close()
    except Exception,detail:
        logger.error("Exception: %s", detail)
        status = SKIP
    if status != PASS:
        logger.error("Creation of Disk Conf file Failed")
    return status


def cleanup_restore(server, virt):
    """
        Restoring back the original diskpool.conf 
        file.
    """
    status = PASS
    libvirt_version = virsh_version(server, virt)
    # The conf file is not present on  the machine if 
    # libvirt_version >= 0.4.1
    # Hence Skipping the logic to delete the new conf file
    # and just returning PASS
    if libvirt_version >= '0.4.1':
        return status
    try:
        if os.path.exists(back_disk_file):
            os.remove(disk_file)
            move_file(back_disk_file, disk_file)
    except Exception, detail:
        logger.error("Exception: %s", detail)
        status = SKIP
    if status != PASS:
        logger.error("Failed to restore the original Disk Conf file")
    return status

def create_diskpool_file():
    # Taking care of already existing diskconf file
    # Creating diskpool.conf if it does not exist
    # Otherwise backing up the prev file and create new one.
    if (os.path.exists(back_disk_file)):
        os.unlink(back_disk_file)

    if (os.path.exists(disk_file)):
        move_file(disk_file, back_disk_file)
    
    return conf_file()

def create_diskpool(server, virt='KVM'):
    status = PASS
    dpoolname = None
    try:
        dpool_list = diskpool_list(server, virt='KVM')
        if len(dpool_list) > 0:
            dpoolname=dpool_list[0]
        else:
            diskxml = PoolXML(server, virt=virt)
            ret = diskxml.create_vpool()
            if not ret:
                logger.error('Failed to create the disk pool "%s"',
                         dpoolname)
                status = FAIL
            else:
                dpoolname=diskxml.xml_get_diskpool_name()
    except Exception, detail:
        logger.error("Exception: In fn create_diskpool(): %s", detail)
        status=FAIL
    return status, dpoolname

def create_diskpool_conf(server, virt):
    libvirt_version = virsh_version(server, virt)
    if libvirt_version >= '0.4.1':
        status, dpoolname = create_diskpool(server, virt=virt)
        diskid = "%s/%s" % ("DiskPool", dpoolname)
    else:
        status = create_diskpool_file()
        diskid = "%s/%s" % ("DiskPool", test_dpath)

    return status, diskid


def create_netpool_conf(server, virt, use_existing=True):
    status = PASS
    test_network = None
    try:
        if use_existing == True:
            vir_network = net_list(server, virt)
            if len(vir_network) > 0:
                test_network = vir_network[0]

        if test_network == None:
            net_name = "default-net" + str(random.randint(1, 100))
            netxml = NetXML(server, virt=virt, networkname=net_name)
            ret = netxml.create_vnet()
            if not ret:
                logger.error("Failed to create Virtual Network '%s'",
                              net_name)
                status = FAIL
            else:
                test_network = netxml.xml_get_netpool_name()
    except Exception, detail:
        logger.error("Exception: In fn create_netpool_conf(): %s", detail)
        status=FAIL
    return status, test_network

def destroy_netpool(server, virt, net_name):
    if net_name == None:
        return FAIL
  
    netxml = NetXML(server, virt=virt, networkname=net_name)
    ret = netxml.destroy_vnet()
    if not ret:
        logger.error("Failed to destroy Virtual Network '%s'",
                     net_name)
        return FAIL

    return PASS 

