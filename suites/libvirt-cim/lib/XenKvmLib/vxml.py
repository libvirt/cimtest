#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Zhengang Li <lizg@cn.ibm.com>
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
# this is a rewrite of the test_xml module. some hints to migrate the reference
# of test_xml to this module:
# Methods:
#    testxml ----------> XenXML/KVMXML
#    testxml_bl -------> XenXML(), XenXML.set_bootloader()
#    testxml_bridge ---> XenXML(), XenXML.set_bridge()
# The following parameters of testxml() remain not changed.
#    test_dom, mem, vcpus, mac, disk_file_path, disk
#
# The VirtXML should not be used directly, it only defines common XML nodes 
# shared by XenXML & KVMXML.
import os
import platform
import tempfile
from xml.dom import minidom, Node
from xml import xpath
from VirtLib import utils, live
from XenKvmLib.test_doms import set_uuid
from CimTest.Globals import logger, CIM_IP
from CimTest.ReturnCodes import SKIP
from XenKvmLib.classes import virt_types

class XMLClass:
    xml_string = ""
    xdoc = None

    def __init__(self):
        self.xdoc = minidom.Document()
        self.refresh()

    def __str__(self):
        return self.xml_string

    def refresh(self):
        self.xml_string = self.xdoc.toxml()

    def get_node(self, ixpath):
        node_list = xpath.Evaluate(ixpath, self.xdoc.documentElement)
        if len(node_list) != 1:
            raise LookupError('Zero or multiple nodes found for XPath' + ixpath)
        return node_list[0]
    def add_sub_node(self, parent, node_name, text_cdata=None, **attrs):
        if isinstance(parent, basestring):
            pnode = self.get_node(parent)
        else:
            pnode = parent

        node = self.xdoc.createElement(node_name)

        for key in attrs.keys():
            node.setAttribute(key, str(attrs[key]))

        if text_cdata is not None:
            node.appendChild(self.xdoc.createTextNode(str(text_cdata)))

        pnode.appendChild(node)
        self.refresh()

        return node

    def set_cdata(self, parent, text_cdata):
        if isinstance(parent, basestring):
            pnode = self.get_node(parent)
        else:
            pnode = parent
        
        for cnode in pnode.childNodes:
            pnode.removeChild(cnode)
            cnode.unlink()

        if text_cdata is not None:
            pnode.appendChild(self.xdoc.createTextNode(str(text_cdata)))

        self.refresh()

    def set_attributes(self, node, **attrs):
        if isinstance(node, basestring):
            pnode = self.get_node(node)
        else:
            pnode = node

        for key in attrs.keys():
            pnode.setAttribute(key, str(attrs[key]))

        self.refresh()

    def get_formatted_xml(self):
        '''Don't use this to define domain.
           Extra newline in the text node fails libvirt
        '''
        return self.xdoc.toprettyxml()

    def get_value_xpath(self, xpathStr):
        node = self.get_node(xpathStr)
        if node.nodeType == Node.ATTRIBUTE_NODE:
            return node.value
        if node.nodeType == Node.TEXT_NODE:
            return node.toxml()
        if node.nodeType == Node.ELEMENT_NODE:
            ret = ''
            for child in node.childNodes:
                ret = ret + child.toxml()
            return ret
    

class Virsh:
    vuri = ""

    def __init__(self, vir_type):
        if vir_type == 'xen':
            self.vuri = 'xen:///'
        elif vir_type == 'kvm':
            self.vuri = 'qemu:///system'

    def run(self, ip, vcmd, param):
        file_arg_cmds = ['define', 'create', 'net-create']
        if vcmd in file_arg_cmds:
            ntf = tempfile.NamedTemporaryFile('w')
            ntf.write(param)
            ntf.flush()
            name = ntf.name
        elif param is None:
            name = ""
        else:
            name = param

        cmd = 'virsh -c %s %s %s' % (self.vuri, vcmd, name)
        s, o = utils.run_remote(ip, cmd)
        if vcmd == 'define' or vcmd == 'create':
            # don't wait till gc does the ntf.close()
            ntf.close()

        return s == 0

class NetXML(Virsh, XMLClass):
    default_bridge_name = 'testbridge'
    default_network_name = 'default-net'

    vbr = ''
    net_name = ''
    server = ''

    def __init__(self, server, bridgename=default_bridge_name, 
                               networkname=default_network_name,
                               virt='xen'):

        def get_valid_bridge_name(server):
            bridge_list = live.available_bridges(server)
            if bridgename in bridge_list:
                import random
                vbr = bridgename + str(random.randint(1, 100))
                if vbr in bridge_list:
                    logger.error('Need to give different bridge name since it already exists')
                    return None
            else:
                vbr = bridgename
            return vbr

        self.vbr = get_valid_bridge_name(server)
        if self.vbr is None:
            sys.exit(SKIP)
        
        XMLClass.__init__(self)
        if virt == 'XenFV':
            virt = 'xen'
        Virsh.__init__(self, str(virt).lower())
        self.net_name = networkname
        self.server = server

        network = self.add_sub_node(self.xdoc, 'network')
        self.add_sub_node(network, 'name', self.net_name)
        self.add_sub_node(network, 'uuid', set_uuid())
        self.add_sub_node(network, 'forward')
        subnet = '192.168.122.'
        self.add_sub_node(network, 'bridge', name=self.vbr, stp='on',
                                             forwardDelay='0')
        ip = self.add_sub_node(network, 'ip', address=subnet+'1',
                                              netmask='255.255.255.0')
        dhcp = self.add_sub_node(ip, 'dhcp')
        self.add_sub_node(dhcp, 'range', start=subnet+'2',
                                         end=subnet+'254')

    def create_vnet(self):
        return self.run(self.server, 'net-create', self.xml_string)


class VirtXML(Virsh, XMLClass):
    """Base class for all XML generation & operation"""
    dname = ""                # domain name

    # default values
    default_domname = 'domU1'
    default_memory = 128
    default_vcpus = 1

    def __init__(self, domain_type, name, uuid, mem, vcpu):
        XMLClass.__init__(self)
        Virsh.__init__(self, domain_type)
        # domain root nodes
        domain = self.add_sub_node(self.xdoc, 'domain', type=domain_type)

        self.add_sub_node(domain, 'name', name)
        self.add_sub_node(domain, 'uuid', uuid)
        self.add_sub_node(domain, 'os')
        self.add_sub_node(domain, 'memory', mem * 1024)
        self.add_sub_node(domain, 'vcpu', vcpu)

        # TEMP: also required for KVM? if not, move these to XenXML
        self.add_sub_node(domain, 'on_poweroff', 'destroy')
        self.add_sub_node(domain, 'on_reboot', 'restart')
        self.add_sub_node(domain, 'on_crash', 'destroy')

        self.add_sub_node(domain, 'devices')
        
        # store the xml stream
        self.refresh()
        self.dname = name
    
    def _os(self):
        raise NotImplementedError('virtual method, implement your own')

    def _devices(self):
        raise NotImplementedError('virtual method, implement your own')
    
    def issubinstance(self):
        return isinstance(self, (XenXML, KVMXML, XenFVXML))

    def set_memory(self, mem):
        self.set_cdata('/domain/memory', mem * 1024)

    def set_uuid(self, uuid):
        self.set_cdata('/domain/uuid', uuid)

    def set_vcpu(self, vcpu):
        self.set_cdata('/domain/vcpu', vcpu)

    def set_mac(self, mac):
        self.set_attributes('/domain/devices/interface/mac', address=mac)

    def set_diskimg(self, diskimg):
        self.set_attributes('/domain/devices/disk/source', file=diskimg)

    def set_diskdev(self, diskdev):
        self.set_attributes('/domain/devices/disk/target', dev=diskdev)
    
    def define(self, ip):
        return self.run(ip, 'define', self.xml_string)

    def undefine(self, ip):
        return self.run(ip, 'undefine', self.dname)

    def start(self, ip):
        return self.run(ip, 'start', self.dname)

    def stop(self, ip):
        return self.run(ip, 'stop', self.dname)        

    def destroy(self, ip):
        return self.run(ip, 'destroy', self.dname)

    def create(self, ip):
        return self.run(ip, 'create', self.xml_string)

    def run_virsh_cmd(self, ip, vcmd):
        if vcmd == 'define' or vcmd == 'create':
            return self.run(ip, vcmd, self.xml_string)
        else:
            return self.run(ip, vcmd, self.dname)

    def _x2str(xstr):
        def func(f):
            def body(self):
                return self.get_value_xpath(xstr)
            return body
        return func

    @_x2str('/domain/name')
    def xml_get_dom_name(self):
        pass

    @_x2str('/domain/bootloader')
    def xml_get_dom_bootloader(self):
        pass

    @_x2str('/domain/bootloader_args')
    def xml_get_dom_bldr_args(self):
        pass

    @_x2str('/domain/on_crash')
    def xml_get_dom_oncrash(self):
        pass

    @_x2str('/domain/memory')
    def xml_get_mem(self):
        pass

    @_x2str('/domain/vcpu')
    def xml_get_vcpu(self):
        pass

    @_x2str('/domain/devices/disk/@type')
    def xml_get_disk_type(self):
        pass

    @_x2str('/domain/devices/disk/source/@file')
    def xml_get_disk_source(self):
        pass

    def xml_get_disk_dev(self):
        devStr = self.get_value_xpath('/domain/devices/disk/target/@dev')
        if devStr != None:
            return devStr.replace(':disk', '')

    @_x2str('/domain/devices/interface/@type')
    def xml_get_net_type(self):
        pass

    @_x2str('/domain/devices/interface/mac/@address')
    def xml_get_net_mac(self):
        pass
    
    def dumpxml(self, ip):
        cmd = 'virsh -c %s dumpxml %s' % (self.vuri, self.dname)
        s, o = utils.run_remote(ip, cmd)
        if s == 0:
            self.xml_string = o
            self.xdoc = minidom.parseString(self.xml_string)

    def _set_emulator(self, emu):
        self.add_sub_node('/domain/devices', 'emulator', emu)
    
    def _set_bridge(self, ip):
        br_list = live.available_virt_bridge(ip)
        if len(br_list) == 0:
            loggerr.error('No virtual bridges found')
            return None

        # pick the 1st virtual bridge
        br = br_list[0]
        interface = self.get_node('/domain/devices/interface')
        interface.setAttribute('type', 'bridge')
        self.add_sub_node(interface, 'source', bridge=br)
            
        return br

    def _set_vbridge(self, ip, virt_type):
        network_list = live.net_list(ip, virt=virt_type)
        if len(network_list) > 0:
            vbr = live.get_bridge_from_network_xml(network_list[0], ip,
                                                   virt = virt_type)
        else:
            logger.info('No virutal network found')
            logger.info('Trying to create one ......')
            netxml = NetXML(ip, virt=virt_type)
            ret = netxml.create_vnet()
            if not ret:
                logger.error('Failed to create the virtual network "%s"', netxml.net_name)
                sys.exit(SKIP)
            vbr = netxml.vbr

        interface = self.get_node('/domain/devices/interface')
        interface.setAttribute('type', 'bridge')
        self.add_sub_node(interface, 'source', bridge=vbr)

        return vbr


class XenXML(VirtXML):
    
    image_dir = "/tmp"
    kernel_path = os.path.join(image_dir, 'default-xen-kernel')
    init_path = os.path.join(image_dir, 'default-xen-initrd')
    disk_path = os.path.join(image_dir, 'default-xen-dimage')
    secondary_disk_path = os.path.join(image_dir, 'default-xen-dimage.2ND')
    default_disk_dev = 'xvda'
    default_mac = '11:22:33:aa:bb:cc'
    default_net_type = 'ethernet'
    
    def __init__(self, test_dom=VirtXML.default_domname, \
                       mem=VirtXML.default_memory, \
                       vcpus=VirtXML.default_vcpus, \
                       mac=default_mac, \
                       disk_file_path=disk_path, \
                       disk=default_disk_dev):
        if not (os.path.exists(self.kernel_path) and os.path.exists(self.init_path)):
            logger.error('ERROR: ' + \
                    'Either the kernel image or the init_path does not exist')
            sys.exit(1)
        VirtXML.__init__(self, 'xen', test_dom, set_uuid(), mem, vcpus)
        self._os(self.kernel_path, self.init_path)
        self._devices(disk_file_path, disk, self.default_net_type, mac)

    def _os(self, os_kernel, os_initrd):
        os = self.get_node('/domain/os')
        self.add_sub_node(os, 'type', 'linux')
        self.add_sub_node(os, 'kernel', os_kernel)
        self.add_sub_node(os, 'initrd', os_initrd)
        self.add_sub_node(os, 'cmdline', 'TERM=xterm')

    def _devices(self, disk_img, disk_dev, net_type, net_mac):
        devices = self.get_node('/domain/devices')
        
        disk = self.add_sub_node(devices, 'disk', type='file', device='disk')
        self.add_sub_node(disk, 'driver', name='file')
        self.add_sub_node(disk, 'source', file=disk_img)
        self.add_sub_node(disk, 'target', dev=disk_dev)
        
        interface = self.add_sub_node(devices, 'interface', type=net_type)
        self.add_sub_node(interface, 'mac', address=net_mac)

    def set_bootloader(self, ip, gtype=0):
        bldr = live.bootloader(ip, gtype)
        self.add_sub_node('/domain', 'bootloader', bldr)
        return bldr

    def set_bridge(self, ip):
        return self._set_bridge(ip)

    def set_vbridge(self, ip):
        return self._set_vbridge(ip, 'Xen')


class KVMXML(VirtXML):
    
    default_emulator = '/usr/bin/qemu'
    image_dir = '/tmp'
    disk_path = os.path.join(image_dir, 'default-kvm-dimage')
    secondary_disk_path = os.path.join(image_dir, 'default-kvm-dimage.2ND')
    default_disk_dev = 'hda'
    default_mac = '11:22:33:aa:bb:cc'

    def __init__(self, test_dom=VirtXML.default_domname, \
                       mem=VirtXML.default_memory, \
                       vcpus=VirtXML.default_vcpus, \
                       mac=default_mac, \
                       disk_file_path=disk_path, \
                       disk=default_disk_dev):
        if not os.path.exists(disk_file_path):
            logger.error('Error: Disk image does not exist')
            sys.exit(1)
        VirtXML.__init__(self, 'kvm', test_dom, set_uuid(), mem, vcpus)
        self._os()
        self._devices(self.default_emulator, disk_file_path, disk, mac)

    def _os(self):
        self.add_sub_node('/domain/os', 'type', 'hvm')

    def _devices(self, emu, disk_img, disk_dev, net_mac):
        devices = self.get_node('/domain/devices')

        self.add_sub_node(devices, 'emulator', emu)
        disk = self.add_sub_node(devices, 'disk', type='file', device='disk')
        self.add_sub_node(disk, 'source', file=disk_img)
        self.add_sub_node(disk, 'target', dev=disk_dev)

        interface = self.add_sub_node(devices, 'interface', type='user')
        self.add_sub_node(interface, 'mac', address=net_mac)

    def set_emulator(self, emu):
        return self._set_emulator(emu)
    
    def set_bridge(self, ip):
        return self._set_bridge(ip)

    def set_vbridge(self, ip):
        return self._set_vbridge(ip, 'KVM')


class XenFVXML(VirtXML):

    s, o = platform.architecture()
    if o == "32bit":
        arch = 'lib'
    else:
        arch = 'lib64'
    default_loader = '/usr/lib/xen/boot/hvmloader'
    default_emulator = '/usr/%s/xen/bin/qemu-dm' % arch
    image_dir = '/tmp'
    disk_path = os.path.join(image_dir, 'default-kvm-dimage')
    default_disk_dev = 'hda'
    default_mac = '00:16:3e:5d:c7:9e'
    default_net_type = 'bridge'

    def __init__(self, test_dom=VirtXML.default_domname, \
                       mem=VirtXML.default_memory, \
                       vcpus=VirtXML.default_vcpus, \
                       mac=default_mac, \
                       disk_file_path=disk_path, \
                       disk=default_disk_dev):
        if not os.path.exists(disk_file_path):
            logger.error('Error: Disk image does not exist')
            sys.exit(1)
        VirtXML.__init__(self, 'xen', test_dom, set_uuid(), mem, vcpus)
        self._os(self.default_loader)
        self._devices(self.default_emulator, self.default_net_type, mac, disk_file_path, disk)

    def _os(self, os_loader):
        os = self.get_node('/domain/os')
        self.add_sub_node(os, 'type', 'hvm')
        self.add_sub_node(os, 'loader', os_loader)
        self.add_sub_node(os, 'boot', dev='hd')

    def _devices(self, emu, net_type, net_mac, disk_img, disk_dev):
        devices = self.get_node('/domain/devices')

        self.add_sub_node(devices, 'emulator', emu)

        interface = self.add_sub_node(devices, 'interface', type=net_type)
        self.add_sub_node(interface, 'mac', address=net_mac)
        self.set_bridge(CIM_IP)

        disk = self.add_sub_node(devices, 'disk', type='file')
        self.add_sub_node(disk, 'source', file=disk_img)
        self.add_sub_node(disk, 'target', dev=disk_dev)

    def set_emulator(self, emu):
        return self._set_emulator(emu)

    def set_bridge(self, ip):
        return self._set_bridge(ip)

    def set_vbridge(self, ip):
        return self._set_vbridge(ip, 'XenFV')


def get_class(virt):
    if virt in virt_types:
        return eval(virt + 'XML')

