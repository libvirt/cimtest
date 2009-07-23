#!/usr/bin/python
#
# Copyright 2009 IBM Corp.
#
# Authors:
#    Deepti B. kalakeri <deeptik@linux.vnet.ibm.com>
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
# This test case verifies that libvirt-cim providers is able to define and
# start a block backed VM.
# 
# Usage:
#  python defineStart_blockbacked_VS.py -i localhost 
#  -b /dev/sda6 -v KVM  -N root/virt -u root -p <passwd> -l -c
# 
#                                                         Date: 23-07-2009
#

import sys
import os
from optparse import OptionParser
from commands  import getstatusoutput
sys.path.append('../../../lib')
from CimTest import Globals
from CimTest.Globals import logger, log_param
from CimTest.ReturnCodes import PASS, FAIL
sys.path.append('../lib')
from XenKvmLib.vxml import get_class 
from XenKvmLib.classes import get_typed_class
from XenKvmLib.xm_virt_util import active_domain_list
from XenKvmLib.const import default_network_name
from XenKvmLib.common_util import pre_check
from XenKvmLib.common_util import create_netpool_conf, destroy_netpool
from XenKvmLib.enumclass import EnumInstances

TEST_LOG="cimtest.log"
test_dom = "disk_backed_dom"

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

def verify_inputs(options, parser):
    try: 
        if options.ns == None:
            raise Exception("Please specify the NameSpace")

        if options.username == None:
            raise Exception("Please specify the Username")

        if options.password == None:
            raise Exception("Please specify the Password")

        if options.vm_disk_image == None:
            raise Exception("Please specify the diskimage for the VM")

    except Exception, details:
        logger.error("Input Verification failed ...")
        logger.error("\"%s\"\n", details)
        print parser.print_help()    
        return FAIL

    return PASS

def print_msg(msg1, field1, msg2, field2):
    logger.info("%s '%s' %s '%s' ", msg1, field1, msg2, field2)
    print msg1, "'", field1, "'",  msg2, "'", field2, "'"


def verify_guest_address_value(virt, sysname, vm_disk_image):
    rasd_list   = []
    classname = get_typed_class(virt, "DiskResourceAllocationSettingData")
    try:
        rasd_list = EnumInstances(sysname, classname, ret_cim_inst=True)
        if len(rasd_list) < 1:
            raise Exception("%s returned %i instances, excepted at least 1."\
                            % (classname, len(rasd_list)))

        for rasd in rasd_list:
            # Verify the Address for the domain is set to vm_disk_image
            if test_dom in rasd['InstanceID']:
                if rasd['Address'] != "" and rasd['Address'] == vm_disk_image:
                    print_msg("Address field of", test_dom, 
                             "is set to ", rasd['Address'])   
                    return PASS

    except Exception, detail:
        logger.error("Exception: %s", detail)
        return FAIL

    print_msg("Address field of", test_dom, "is not set to", vm_disk_image)
    return FAIL

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
    parser.add_option("-c", "--clean-log", action="store_true", dest="clean",
                      help="Will remove existing log files before test run")
    parser.add_option("-l", "--debug-output", action="store_true",
                      dest="debug", help="Duplicate the output to stderr")
    parser.add_option("-b", "--vm-image", dest="vm_disk_image", default=None,
                      help="Specify the partition on which the vm" \
                      " image is instantiated, Ex: /dev/sda6")

    print "\nPlease check cimtest.log in the curr dir for debug log msgs...\n"

    (options, args) = parser.parse_args()
        
    virt = options.virt

    if ":" in options.h_url:
        (sysname, port) = options.h_url.split(":")
    else:
        sysname = options.h_url

    log_param(file_name=TEST_LOG)

    # Verify if the CIMOM is running, clean cimtest.log and 
    # Set Debug option if requested
    status = env_setup(sysname, virt, options.clean, options.debug)
    if status != PASS:
       return status

    status = verify_inputs(options, parser)
    if status != PASS:
        return status

    os.environ['CIM_NS'] = Globals.CIM_NS = options.ns
    os.environ['CIM_USER'] = Globals.CIM_USER = options.username
    os.environ['CIM_PASS'] = Globals.CIM_PASS = options.password

    vm_disk_image = options.vm_disk_image 
    cxml = get_class(virt)(test_dom, disk_file_path=vm_disk_image)
    status = FAIL

    try:
        status, netpool = create_netpool_conf(sysname, virt, 
                                              net_name=default_network_name)
        if status != PASS:
            logger.error("\nUnable to create network pool %s",
                         default_network_name)
            return status

        ret = cxml.cim_define(sysname)
        if not ret:
            raise Exception("Unable to define %s" % test_dom)

        status = cxml.cim_start(sysname)
        if status != PASS:
            cxml.undefine(sysname)
            logger.error("Failed to Start the dom: %s", test_dom)
            raise Exception("Property values for '%s' not properly set" \
                            % test_dom) 

        active_doms = active_domain_list(sysname, virt)
        if test_dom in active_doms:
            status = verify_guest_address_value(virt, sysname, vm_disk_image)
            if status == PASS:
                print_msg("Domain", test_dom, "successfully created on", 
                           sysname)
        else:
            logger.error("'%s' not found on the '%s'", test_dom, sysname)
            status = FAIL
    
    except Exception, detail:
        logger.error("Exception: %s", detail)
        destroy_netpool(sysname, virt, default_network_name)
        return FAIL

    cxml.cim_destroy(sysname)
    cxml.undefine(sysname)
    destroy_netpool(sysname, virt, default_network_name)

    return status

if __name__ == "__main__":
    sys.exit(main())

