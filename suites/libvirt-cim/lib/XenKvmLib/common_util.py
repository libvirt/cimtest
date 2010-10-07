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
from tempfile import mkdtemp
from commands import getstatusoutput
from socket import gethostbyaddr
from distutils.file_util import move_file
from XenKvmLib.test_xml import * 
from XenKvmLib.test_doms import * 
from XenKvmLib import vsms
from CimTest import Globals 
from XenKvmLib import enumclass 
from pywbem.cim_obj import CIMInstanceName
from XenKvmLib.classes import get_typed_class
from CimTest.Globals import logger, CIM_ERROR_ENUMERATE, \
                            CIM_ERROR_GETINSTANCE
from CimTest.ReturnCodes import PASS, FAIL, XFAIL_RC, SKIP
from XenKvmLib.xm_virt_util import diskpool_list, virsh_version, net_list,\
                                   domain_list, virt2uri, net_destroy
from XenKvmLib.vxml import PoolXML, NetXML
from VirtLib import utils 
from XenKvmLib.const import default_pool_name, default_network_name,\
                            default_bridge_name

disk_file = '/etc/libvirt/diskpool.conf'
exports_file = '/etc/exports'
back_disk_file = disk_file + "." + "backup"
back_exports_file = exports_file + "." + "backup"

def print_field_error(fieldname, ret_value, exp_value):
    logger.error("%s Mismatch", fieldname)
    logger.error("Returned %s instead of %s", ret_value, exp_value)

def get_cs_instance(domain_name, ip, virt='Xen'):
    cs = None
    cs_class = get_typed_class(virt, 'ComputerSystem')
    try:
        keys = {
                'Name' : domain_name,
                'CreationClassName' : cs_class
               }
        cs = enumclass.GetInstance(ip, cs_class, keys)

        if cs.Name != domain_name:
            logger.error("VS %s is not found", domain_name)
            return (1, cs)

    except Exception, detail:
        logger.error(CIM_ERROR_GETINSTANCE, 
                     get_typed_class(virt, 'ComputerSystem'))
        logger.error("Exception: %s", detail)
        return (1, cs) 

    return (0, cs) 

def verify_err_desc(exp_rc, exp_desc, err_no, err_desc):
    if err_no == exp_rc and err_desc.find(exp_desc) >= 0:
        logger.info("Got expected exception where ")
        logger.info("Errno is '%s' ", exp_rc)
        logger.info("Error string is '%s'", exp_desc)
        return PASS
    else:
        logger.error("Unexpected rc code %s and description %s\n", 
                     err_no, err_desc)
        return FAIL

def call_request_state_change(domain_name, ip, rs, time, virt='Xen'):
    rc, cs = get_cs_instance(domain_name, ip, virt)
    if rc != 0:
        return FAIL 

    try:
        cs.RequestStateChange(RequestedState=pywbem.cim_types.Uint16(rs),
                              TimeoutPeriod=pywbem.cim_types.CIMDateTime(time))

    except Exception, detail:
        logger.error("Exception: %s", detail)
        return FAIL 

    return PASS 

def try_request_state_change(domain_name, ip, rs, time, exp_rc, 
                             exp_desc, virt='Xen'):
    rc, cs = get_cs_instance(domain_name, ip, virt)
    if rc != 0:
        return FAIL 

    try:
        cs.RequestStateChange(RequestedState=pywbem.cim_types.Uint16(rs),
                              TimeoutPeriod=pywbem.cim_types.CIMDateTime(time))

    except Exception, (err_no, err_desc) :
        return verify_err_desc(exp_rc, exp_desc, err_no, err_desc)
    logger.error("RequestStateChange failed to generate an exception")
    return FAIL 

def poll_for_state_change(server, virt, dom, exp_state, timeout=30):
    dom_cs = None
    cs_class = get_typed_class(virt, 'ComputerSystem')
    keys = {
            'Name' : dom,
            'CreationClassName' : cs_class
           }

    try:
        for i in range(1, (timeout + 1)):
            dom_cs = enumclass.GetInstance(server, cs_class, keys)
            if dom_cs is None or dom_cs.Name != dom:
                continue

            sleep(1)
            if dom_cs.EnabledState == exp_state:
                break

    except Exception, detail:
        logger.error("Exception: %s", detail)
        return FAIL, dom_cs

    if dom_cs is None or dom_cs.Name != dom:
        logger.error("CS instance not returned for %s.", dom)
        return FAIL, dom_cs

    if dom_cs.EnabledState != exp_state:
        logger.error("EnabledState is %i instead of %i.", dom_cs.EnabledState,
                     exp_state)
        logger.error("Try to increase the timeout and run the test again")
        return FAIL, dom_cs

    return PASS, dom_cs 

def get_host_info(server, virt):
    try:
    # Commenting out sblim check as libvirt-cim is not supporting it anymore.
    # Leaving them commented, in case we add support for sblim at later time.

    #    status, linux_cs = check_sblim(server)
    #    if status == PASS:
    #        return status, linux_cs

        hs_class = get_typed_class(virt, 'HostSystem')
        host_info = enumclass.EnumInstances(server, hs_class)
        if len(host_info) == 1:
            return PASS, host_info[0]
        else:
            logger.error("Error in getting HostSystem instance")
            return FAIL, None 

    except Exception,detail:
        logger.error("Exception: %s", detail)

    return FAIL, None 

def try_assoc(conn, classname, assoc_classname, keys, field_name, \
                                              expr_values, bug_no):
    assoc_info = []
    instanceref = CIMInstanceName(classname, keybindings=keys)
    logger.info ("Instanceref is '%s'", instanceref)
    try:
        assoc_info = conn.AssociatorNames(instanceref, \
                             AssocClass=assoc_classname)
    except pywbem.CIMError, (err_no, err_desc):
        exp_rc    = expr_values['rc']
        exp_desc  = expr_values['desc']
        return verify_err_desc(exp_rc, exp_desc, err_no, err_desc)
    logger.error("'%s' association failed to generate an exception and" 
                  " '%s' passed.", assoc_classname, field_name)
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
                          "InstanceID"              : "CIM:DSP1081-VirtualSystemMigration-0.8.1",
                          "RegisteredOrganization"  : 2, 
                          "RegisteredName"          : "Virtual System Migration",
                          "RegisteredVersion"       : "0.8.1"
                     }
     
    profiles = {

                 'DSP1042'       : sys_prof_info,
                 'DSP1045'       : mem_res_prof,
                 'DSP1057'       : vs_prof,
                 'DSP1081'       : vs_mig_prof
               } 
    gdrv_list = ['DSP1059-GenericDeviceResourceVirtualization-1.0.0_d', 
                 'DSP1059-GenericDeviceResourceVirtualization-1.0.0_n',
                 'DSP1059-GenericDeviceResourceVirtualization-1.0.0_p' ]
    for key in gdrv_list:
        profiles[key] = gen_dev_prof.copy()
        profiles[key]['InstanceID'] = 'CIM:' + key
    return profiles 

def check_cimom(ip):
    cmd = "ps -ef | grep -v grep | grep cimserver"
    rc, out = utils.run_remote(ip, cmd)
    if rc != 0:
        cmd = "ps -ef | grep -v grep | grep sfcbd"
        rc, out = utils.run_remote(ip, cmd)

    if rc == 0 :
        cmd = "%s | awk '{ print \$8 }' | uniq" % cmd
        rc, out = utils.run_remote(ip, cmd)

    return rc, out

def pre_check(ip, virt):
    cmd = "virsh -c %s list --all 2>/dev/null" % virt2uri(virt)
    ret, out = utils.run_remote(ip, cmd)
    if ret != 0:
        return "This libvirt install does not support %s"  % virt

    cmd = "virsh -c %s version 2>/dev/null" % virt2uri(virt)
    ret, out = utils.run_remote(ip, cmd)
    if ret != 0:
        # The above version cmd does not work for F10.
        # Hence, this is a workaround to verify if qemu and qemu-kvm 
        # are installed in case the above version cmd fails.
        cmd = "qemu -help"
        ret, out = utils.run_remote(ip, cmd)
        if ret != 0: 
            cmd = "qemu-kvm -help"
            ret, out = utils.run_remote(ip, cmd)
            if ret != 0: 
                return "Encountered an error querying for qemu-kvm and qemu " 

    rc, out = check_cimom(ip)
    if rc != 0:
        return "A supported CIMOM is not running" 

    cmd = "ps -ef | grep -v grep | grep libvirtd"
    rc, out = utils.run_remote(ip, cmd)
    if rc != 0:
        return "libvirtd is not running" 

    return None

def conf_file():
    """
       Creating diskpool.conf file.
    """
    status = PASS
    logger.info("Disk conf file : %s", disk_file)
    try:
        f = open(disk_file, 'w')
        f.write('%s %s' % (default_pool_name, '/'))
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

def create_diskpool(server, virt='KVM', dpool=default_pool_name,
                    useExisting=False):
    status = PASS
    dpoolname = None
    try:
        if useExisting == True:
            dpool_list = diskpool_list(server, virt='KVM')
            if len(dpool_list) > 0:
                dpoolname=dpool_list[0]

        if dpoolname == None:
            cmd = "virsh -c %s pool-info %s 2>/dev/null" % \
                  (virt2uri(virt), dpool)
            ret, out = utils.run_remote(server, cmd)
            if ret == 0:
                logger.error("Disk pool with name '%s' already exists", dpool)
                return FAIL, "Unknown"

            diskxml = PoolXML(server, virt=virt, poolname=dpool)
            ret = diskxml.create_vpool()
            if not ret:
                logger.error('Failed to create the disk pool "%s"', dpool)
                status = FAIL
            else:
                dpoolname=diskxml.xml_get_diskpool_name()
    except Exception, detail:
        logger.error("Exception: In fn create_diskpool(): %s", detail)
        status=FAIL
    return status, dpoolname

def create_diskpool_conf(server, virt, dpool=default_pool_name):
    libvirt_version = virsh_version(server, virt)
    if libvirt_version >= '0.4.1':
        status, dpoolname = create_diskpool(server, virt, dpool)
        diskid = "%s/%s" % ("DiskPool", dpoolname)
    else:
        status = create_diskpool_file()
        diskid = "DiskPool/%s" % default_pool_name

    return status, diskid

def destroy_diskpool(server, virt, dpool):
    libvirt_version = virsh_version(server, virt)
    if libvirt_version >= '0.4.1':
        if dpool == None:
            logger.error("No disk pool specified")
            return FAIL

        pool_xml = PoolXML(server, virt=virt, poolname=dpool)
        ret = pool_xml.destroy_vpool()
        if not ret:
            logger.error("Failed to destroy disk pool '%s'", dpool)
            return FAIL

    else:
        status = cleanup_restore(server, virt)
        if status != PASS:
            logger.error("Failed to restore original disk pool file")
            return status 

    return PASS

def create_netpool_conf(server, virt, use_existing=False,
                        net_name=default_network_name,
                        bridge_name=default_bridge_name):
    status = PASS
    test_network = None
    try:
        if use_existing == True:
            vir_network = net_list(server, virt)
            if len(vir_network) > 0:
                test_network = vir_network[0]

        if test_network == None:
            cmd = "virsh -c %s net-list --all 2>/dev/null | grep -w %s" % \
                  (virt2uri(virt), net_name)
            ret, out = utils.run_remote(server, cmd)
            # If success, network pool with name net_name already exists
            if ret == 0:
                logger.error("Network pool with name '%s' already exists",
                              net_name)
                return FAIL, "Unknown" 
                
            netxml = NetXML(server, virt=virt, networkname=net_name,
                            bridgename=bridge_name)
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
  
    ret = net_destroy(net_name, server, virt)
    if ret != 0:
        logger.error("Failed to destroy Virtual Network '%s'", net_name)
        return FAIL

    return PASS 

def libvirt_cached_data_poll(ip, virt, dom_name):
    cs = None

    dom_list = domain_list(ip, virt)
    if dom_name in dom_list:
        timeout = 10 

        for i in range(0, timeout):
            rc, cs = get_cs_instance(dom_name, ip, virt)
            if rc == 0:
                return cs 

            sleep(1)
            
    return cs

def check_sblim(server, virt='Xen'):
    status = FAIL
    prev_namespace = Globals.CIM_NS
    Globals.CIM_NS = 'root/cimv2'
    keys = ['Name', 'CreationClassName']
    linux_cs = None
    cs = 'Linux_ComputerSystem'
    try:
        linux = enumclass.EnumInstances(server, cs)
        if len(linux) == 1:
            status = PASS
            linux_cs = linux[0]
        else:
            logger.info("Enumerate of Linux_ComputerSystem return NULL")
    except Exception, detail:
        logger.error(CIM_ERROR_ENUMERATE, 'Linux_ComputerSystem')
        logger.error("Exception: %s", detail)

    Globals.CIM_NS = prev_namespace 
    return status, linux_cs 

def parse_instance_id(instid):
    str_arr = instid.split("/")
    if len(str_arr) < 2:
        return None, None, FAIL

    guest_name = str_arr[0] 

    devid = instid.lstrip("%s/" % guest_name)

    return guest_name, devid, PASS


def get_nfs_bin(server):
    cmd = "cat /etc/issue | grep -v ^$ | egrep 'Red Hat|Fedora'"
    rc, out = utils.run_remote(server, cmd)
    if rc != 0:
        #SLES
        nfs_server_bin =  "/etc/init.d/nfsserver"
    else:
        nfs_server_bin =  "/etc/init.d/nfs"

    return nfs_server_bin

def nfs_config(server, nfs_server_bin):
    cmd = "ps aux | grep -v -e nfsiod -e grep | grep nfsd"
    rc, out = utils.run_remote(server, cmd)
    # if NFS services is not found on the machine, start it.. 
    if rc != PASS :
        # Check if NFS server is installed ...
        if not os.path.exists(nfs_server_bin):
            logger.error("NFS server '%s' does not seem to be installed "\
                         "on '%s'", nfs_server_bin, server)
            return SKIP

        # Start the nfs server ...
        nfs_server_cmd = "%s start" % nfs_server_bin
        rc, out = utils.run_remote(server, nfs_server_cmd)
        if rc != PASS:
            logger.error("Could not start the nfsserver on '%s'", server)
            logger.error("NFS server seems to have problem on '%s'", server)
            return FAIL 

    return PASS

def check_existing_nfs():
    host_addr = src_dir = None
    s, o = getstatusoutput("mount")
    lines  = o.splitlines()
    for line in lines:
        if "nfs" == line.split()[-2]:
            addr, src_dir = line.split()[0].split(":")
            host_addr  = gethostbyaddr(addr)[0] 

    return host_addr, src_dir

def clean_temp_files(server, src_dir_for_mnt, dest_dir_to_mnt, cmd):
    rc, out = utils.run_remote(server, cmd) 
    if rc != PASS:
        logger.error("Please delete %s %s if present on %s", 
                      src_dir_for_mnt, dest_dir_to_mnt, server)

def check_haddr_is_localhost(server, host_addr):
    # This function is required to determine if setup a new nfs
    # setup or using an old one.
    new_nfs_server_setup = False
    local_addr = gethostbyaddr(server)
    if host_addr in local_addr:
        new_nfs_server_setup = True

    return new_nfs_server_setup

def netfs_cleanup(server, pool_attr):
    src_dir = pool_attr['SourceDirectory']
    dst_dir = pool_attr['Path']
    host_addr = pool_attr['Host']

    # Determine if we are using existing nfs setup or configured a new one
    new_nfs_server_setup = check_haddr_is_localhost(server, host_addr)
    if new_nfs_server_setup == False:
        cmd =  "rm -rf %s " % (dst_dir)
    else:
        cmd =  "rm -rf %s %s" % (src_dir, dst_dir)

    # Remove the temp dir created .
    clean_temp_files(server, src_dir, dst_dir, cmd)

    if new_nfs_server_setup == False:
        return 
 
    # Restore the original exports file.
    if os.path.exists(back_exports_file):
        os.remove(exports_file)
        move_file(back_exports_file, exports_file)

    # restart the nfs server
    nfs_server_bin = get_nfs_bin(server)
    nfs_server_cmd = "%s restart" % nfs_server_bin
    rc, out = utils.run_remote(server, nfs_server_cmd)
    if rc != PASS:
        logger.error("Could not restart NFS server on '%s'" % server)

def netfs_config(server, nfs_server_bin, dest_dir_to_mnt):
    src_dir_for_mnt = mkdtemp()
    
    try:
        # Backup the original exports file.
        if (os.path.exists(exports_file)):
            if os.path.exists(back_exports_file):
                os.remove(back_exports_file)
            move_file(exports_file, back_exports_file)
        fd = open(exports_file, "w")
        line = "\n %s %s(rw)" %(src_dir_for_mnt, server)
        fd.write(line)
        fd.close()

        # Need to give suitable perm, otherwise netfs pool-create fails
        cmd = "chmod go+rx %s %s" % (src_dir_for_mnt, dest_dir_to_mnt)
        rc, out = utils.run_remote(server, cmd)
        if rc != 0:
            raise Exception("Failed to chmod on %s %s" \
                            % (src_dir_for_mnt, dest_dir_to_mnt))

        # Restart the nfs server....
        nfs_server_cmd = "%s restart" % nfs_server_bin
        rc, out = utils.run_remote(server, nfs_server_cmd)
        if rc != PASS:
            raise Exception("Could not restart NFS server on '%s'" % server)

    except Exception, detail:
        logger.error("Exception details : %s", detail)
        cmd = "rm -rf %s %s " % (src_dir_for_mnt,dest_dir_to_mnt)
        clean_temp_files(server, src_dir_for_mnt, dest_dir_to_mnt, cmd)
        return SKIP, None

    return PASS, src_dir_for_mnt

def nfs_netfs_setup(server):
    nfs_server_bin = get_nfs_bin(server)
   
    dest_dir = mkdtemp()

    # Before going ahead verify that nfs server is available on machine..
    ret = nfs_config(server, nfs_server_bin)
    if ret != PASS:
        logger.error("Failed to configure NFS on '%s'", server)
        logger.info("Trying to look for nfs mounted dir on '%s'...", server)
        server, src_dir = check_existing_nfs()
        if server == None or src_dir == None:
            logger.error("No nfs mount information on '%s' ", server)
            return SKIP, None, None, None
        else:
            return PASS, server, src_dir, dest_dir
    else:
        ret, src_dir = netfs_config(server, nfs_server_bin, dest_dir)
        if ret != PASS:
            logger.error("Failed to configure netfs on '%s'", server)
            return ret, None, None, None
    
    return PASS, server, src_dir, dest_dir
