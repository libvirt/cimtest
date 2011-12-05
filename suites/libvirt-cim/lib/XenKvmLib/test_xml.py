#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Dan Smith <danms@us.ibm.com>
#    Deepti B. Kalakeri <dkalaker@in.ibm.com>
#    Guolian Yun <yunguol@cn.ibm.com>
#    Kaitlin Rupert <karupert@us.ibm.com>
#    Veerendra Chandrappa <vechandr@in.ibm.com>
#    Zhengang Li <lizg@cn.ibm.com>
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
import sys 
import random
from VirtLib import utils
from lxml import etree
from CimTest.Globals import logger
from XenKvmLib.test_doms import set_uuid, create_vnet
from VirtLib.live import available_bridges
from XenKvmLib.xm_virt_util import net_list, get_bridge_from_network_xml, \
                                   bootloader, virt2uri
from CimTest.ReturnCodes import SKIP

image_dir   = "/tmp"
kernel_path = os.path.join(image_dir, 'default-xen-kernel')
init_path = os.path.join(image_dir, 'default-xen-initrd')
disk_path = os.path.join(image_dir, 'default-xen-dimage')

default_mac = '11:22:33:aa:bb:cc'

def testxml(test_dom="domU1", mem = 128, vcpus = 1, mac = default_mac,
            disk_file_path = disk_path, disk = "xvda"):
    if not (os.path.exists(kernel_path) and os.path.exists(init_path)) :
        logger.error("ERROR: Either the kernel image or the "
                     "init_path does not exist")
        sys.exit(SKIP)
    test_xml = """
    <domain type='xen' id='23'>
      <name>%s</name>
      <uuid>%s</uuid>
      <os>
        <type>linux</type>
        <kernel>%s</kernel>
        <initrd>%s</initrd>
        <cmdline>TERM=xterm </cmdline>
      </os>
      <memory>%d</memory>
      <vcpu>%d</vcpu>
      <on_poweroff>destroy</on_poweroff>
      <on_reboot>restart</on_reboot>
      <on_crash>destroy</on_crash>
      <devices>
        <interface type='ethernet'>
          <mac address='%s'/>
        </interface>
        <disk type='file' device='disk'>
          <driver name='file'/>
          <source file='%s'/>
          <target dev='%s'/>
        </disk>
      </devices>
    </domain>
    """ % ( test_dom, set_uuid(), kernel_path, init_path, mem*1024, vcpus,
            mac, disk_file_path, disk )
    return test_xml

def testxml_bl(test_dom="domU1", mem = 128, vcpus = 1, mac = default_mac,
               disk_file_path = disk_path, disk = "xvda", server = "",
               gtype = 0):
    if server == "":
        logger.error("ERROR: Server info cannot be empty "
                     "specify either localhost or remote machine ip/name ")
        sys.exit(SKIP)
    if not (os.path.exists(kernel_path) and os.path.exists(init_path)) :
        logger.error("ERROR: Either the kernel image or the "
                     "init_path does not exist")
        sys.exit(SKIP)
    test_xml = """
    <domain type='xen' id='23'>
      <name>%s</name>
      <uuid>%s</uuid>
      <bootloader>%s</bootloader>
      <os>
        <type>linux</type>
        <kernel>%s</kernel>
        <initrd>%s</initrd>
        <cmdline>TERM=xterm </cmdline>
      </os>
      <memory>%d</memory>
      <vcpu>%d</vcpu>
      <on_poweroff>destroy</on_poweroff>
      <on_reboot>restart</on_reboot>
      <on_crash>destroy</on_crash>
      <devices>
        <interface type='ethernet'>
          <mac address='%s'/>
        </interface>
        <disk type='file' device='disk'>
          <driver name='file'/>
          <source file='%s'/>
          <target dev='%s'/>
        </disk>
      </devices>
    </domain>
    """ % ( test_dom, set_uuid(), bootloader(server, gtype),
            kernel_path, init_path, mem*1024, vcpus, mac, disk_file_path, disk )
    return test_xml

def testxml_bridge(test_dom="domU1", mem = 128, vcpus = 1,
                   mac = default_mac, disk_file_path = disk_path,
                   disk = "xvda", server = ""): 
    if not (os.path.exists(kernel_path) and os.path.exists(init_path)) :
        logger.error("ERROR: Either the kernel image or the "
                     "init_path does not exist")
        sys.exit(SKIP)
    vir_network = net_list(server)
    if len(vir_network) > 0 :
        vnet = vir_network[0]
    # Try to find which bridge this network is associated with
        bridge = get_bridge_from_network_xml(vnet, server)
    else:
        logger.info("No virtual network found")
        logger.info("Trying to create one ......")
        bridgename  = 'testbridge'
        networkname = 'default-net'
        net_xml, bridge = netxml(server, bridgename, networkname)
        ret = create_vnet(server, net_xml)
        if not ret:
            logger.error("Failed to create the Virtual Network '%s'", 
                         networkname)
            sys.exit(SKIP)

    test_xml = """
    <domain type='xen' id='23'>
      <name>%s</name>
      <uuid>%s</uuid>
      <os>
        <type>linux</type>
        <kernel>%s</kernel>
        <initrd>%s</initrd>
        <cmdline>TERM=xterm </cmdline>
      </os>
      <memory>%d</memory>
      <vcpu>%d</vcpu>
      <on_poweroff>destroy</on_poweroff>
      <on_reboot>restart</on_reboot>
      <on_crash>destroy</on_crash>
      <devices>
        <interface type='bridge'>
          <source bridge='%s' />
          <mac address='%s'/>
        </interface>
        <disk type='file' device='disk'>
          <driver name='file'/>
          <source file='%s'/>
          <target dev='%s'/>
        </disk>
      </devices>
    </domain>
    """ % ( test_dom, set_uuid(), kernel_path, init_path, mem*1024, vcpus,
            bridge, mac, disk_file_path, disk )
    return test_xml, bridge

def netxml(server, bridgename, networkname):
    bridges = available_bridges(server)
    if bridgename in bridges:
        bridge_name = bridgename + str(random.randint(1, 100))
        if bridge_name in bridges:
            logger.error("Need to give different bridge name since "
                         "it alreay exists")
            sys.exit(SKIP)
    else:
        bridge_name = bridgename

    net_xml = """
    <network>
    <name>%s</name>
    <uuid>%s</uuid>
    <forward/>
    <bridge name='%s' stp='on' forwardDelay='0' />
    <ip address='192.168.122.1' netmask='255.255.255.0'>
      <dhcp>
        <range start='192.168.122.2' end='192.168.122.254' />
      </dhcp>
    </ip>
    </network>
    """ % (networkname, set_uuid(), bridge_name)
    return net_xml, bridge_name


def dumpxml(name, server, virt="Xen"):
    cmd = "virsh -c %s dumpxml %s" % (virt2uri(virt), name)
    s, o = utils.run_remote(server, cmd)
    if s == 0:
        return o

def get_value_xpath(xmlStr, xpathStr):
    xmldoc = etree.fromstring(xmlStr)
    nodes = xmldoc.xpath(xpathStr)

    if len(nodes) != 1:
        raise LookupError('Zero or multiple xpath results found!')

    node = nodes[0]
    ret = ''

    if etree.iselement(node):
        ret = node.text
        for child in node:
            ret = ret + child.text
    elif isinstance(node, str):
        ret = node

    if ret is None:
        ret = ''

    return ret

def xml_get_dom_name(xmlStr):
    return get_value_xpath(xmlStr,
                           '/domain/name')
def xml_get_dom_bootloader(xmlStr):                                                
    return get_value_xpath(xmlStr,                                                 
                           '/domain/bootloader')                                   
                                                                                   
def xml_get_dom_bldr_args(xmlStr):                                                 
    return get_value_xpath(xmlStr,                                                 
                           '/domain/bootloader_args')                              
                                                                                   
def xml_get_dom_oncrash(xmlStr):                                                   
    return get_value_xpath(xmlStr,                                                 
                           '/domain/on_crash')                                     
                                                                                   
def xml_get_mem(xmlStr):                                                           
    return get_value_xpath(xmlStr,                                                 
                           '/domain/memory')                                       
                                                                                   
def xml_get_vcpu(xmlStr):                                                          
    return get_value_xpath(xmlStr,                                                 
                           '/domain/vcpu')                                         
                                                                                   
def xml_get_disk_type(xmlStr):                                                     
    return get_value_xpath(xmlStr,                                                 
                           '/domain/devices/disk/@type')                           
                                                                                   
def xml_get_disk_source(xmlStr):                                                   
    return get_value_xpath(xmlStr,                                                 
                           '/domain/devices/disk/source/@file')                    
                                                                                   
def xml_get_disk_dev(xmlStr):                                                      
    devStr = get_value_xpath(xmlStr,                                               
                             '/domain/devices/disk/target/@dev')                   
    if devStr != None:                                                             
        return devStr.replace(':disk', '')                                         


def xml_get_net_type(xmlStr):
    return get_value_xpath(xmlStr,
                           '/domain/devices/interface/@type')

def xml_get_net_mac(xmlStr):
    return get_value_xpath(xmlStr,
                           '/domain/devices/interface/mac/@address')


