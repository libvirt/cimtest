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
import sys
import random
import platform
import tempfile
from time import sleep
import pywbem
from xml.dom import minidom, Node
from xml import xpath

try:
    from xml.etree import cElementTree as ElementTree
except:
    from xml.etree import ElementTree

from VirtLib import utils, live
from XenKvmLib.xm_virt_util import get_bridge_from_network_xml, bootloader, \
                                   net_list 
from XenKvmLib.test_doms import set_uuid, viruuid
from XenKvmLib import vsms
from XenKvmLib import const
from CimTest.Globals import logger, CIM_IP, CIM_PORT, CIM_NS, CIM_USER, CIM_PASS
from CimTest.ReturnCodes import SKIP, PASS, FAIL
from XenKvmLib.classes import virt_types, get_typed_class
from XenKvmLib.enumclass  import GetInstance
from XenKvmLib.const import get_provider_version

vsms_graphics_sup = 763
vsms_inputdev_sup = 771

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
        try:
            node = self.get_node(xpathStr)
        except Exception:
            logger.info('Zero or multiple node found')
            return None

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
        elif vir_type == 'lxc':
            self.vuri = 'lxc:///'

    def run(self, ip, vcmd, param):
        file_arg_cmds = ['define', 'create', 'net-create', 'pool-create']
        if vcmd in file_arg_cmds:
            ntf = tempfile.NamedTemporaryFile('w')
            ntf.write(param)
            ntf.flush()
            name = ntf.name
        elif param is None:
            name = ""
        else:
            name = param

        # We need to copy the xml files to remote machine for 
        # successful execution of the ssh remote commands like net-createa via virsh, 
        # otherwise the remote execution of the command fails when the 
        # file is not locally present on the remote machine.
        if vcmd == 'define' or vcmd == 'create' or vcmd == 'net-create' or \
           vcmd == 'pool-create':
            s, o = utils.copy_remote(ip, name, remote=name)
            if s != 0:
                logger.error("Failed to copy the tempxml file to execute '%s'"\
                             " cmd on '%s'", vcmd, ip) 
                return 0

        cmd = 'virsh -c %s %s %s 2>/dev/null' % (self.vuri, vcmd, name)
        s, o = utils.run_remote(ip, cmd)
        if vcmd == 'define' or vcmd == 'create' or vcmd == 'net-create' \
           or vcmd == 'pool-create':
            # don't wait till gc does the ntf.close()
            ntf.close()

            # Remove the tmp file copied to the remote machine
            cmd = 'rm -rf %s' % name
            utils.run_remote(ip, cmd)

        return s == 0

class NetXML(Virsh, XMLClass):
    vbr = ''
    net_name = ''
    server = ''

    def __init__(self, server, bridgename=const.default_bridge_name, 
                               networkname=const.default_network_name,
                               virt='xen',
                               is_new_net=True):

        def get_valid_bridge_name(server):
            bridge_list = live.available_bridges(server)
            if bridgename in bridge_list:
                vbr = bridgename + str(random.randint(1, 100))
                if vbr in bridge_list:
                    logger.error('Need to give different bridge name '
                                 'since it already exists')
                    return None
            else:
                vbr = bridgename
            return vbr
        # get_valid_bridge_name

        def _parse_net_dumpxml(_xml):
            try:
                root = ElementTree.fromstring(_xml)
                ip_element = root.find("ip")
                return ip_element.get("address")
            except:
                logger.error("Encounter error dump netxml")
            return None
        # _parse_net_dumpxml

        self.vbr = get_valid_bridge_name(server)
        if self.vbr is None:
            sys.exit(SKIP)
        
        XMLClass.__init__(self)
        if virt == 'XenFV':
            virt = 'xen'
        Virsh.__init__(self, str(virt).lower())
        self.net_name = networkname
        self.server = server

        if is_new_net is False:
            cmd = "virsh -c %s net-dumpxml %s 2>/dev/null" % (self.vuri, self.net_name)
            s, net_xml = utils.run_remote(server, cmd)
            if s != 0:
                logger.error("Encounter error dump netxml")
                return None
            else:
                self.xml_string = net_xml
                self.xdoc = minidom.parseString(self.xml_string)
                return 
    
        network = self.add_sub_node(self.xdoc, 'network')
        self.add_sub_node(network, 'name', self.net_name)
        self.add_sub_node(network, 'uuid', set_uuid())
        self.add_sub_node(network, 'forward')
        subnet = '192.168.%d.' % (random.randint(1, 100))
        self.add_sub_node(network, 'bridge', name=self.vbr, stp='on',
                                             forwardDelay='0')
        ip_base = random.randint(1, 100)
        addr = subnet+'%d' % ip_base

        n_list = net_list(server, virt)
        for _net_name in n_list:
            cmd = "virsh -c %s net-dumpxml %s 2>/dev/null" % (self.vuri, _net_name)
            s, xml = utils.run_remote(server, cmd)

            in_use_addr = _parse_net_dumpxml(xml)
            if in_use_addr is None:
                logger.error("Unable to find IP address")
                return None

            sub_net_in_use = in_use_addr
            sub_net_in_use = sub_net_in_use.rsplit('.', 1)[0].strip("'") + "."
            if subnet == sub_net_in_use:
                logger.error("Subnet address is in use by a different network")
                return None 

            in_use_addr = in_use_addr.strip("'")
            if in_use_addr == addr:
                logger.error("IP address is in use by a different network")
                return None 

        ip = self.add_sub_node(network, 'ip', address=addr,
                                              netmask='255.255.255.0')
        dhcp = self.add_sub_node(ip, 'dhcp')
        range_addr = subnet+'%d' % (ip_base + 1)
        self.add_sub_node(dhcp, 'range', start=range_addr,
                                         end=subnet+'254')

    def create_vnet(self):
        return self.run(self.server, 'net-create', self.xml_string)

    def destroy_vnet(self):
        return self.run(self.server, 'net-destroy', self.net_name)

    def xml_get_netpool_name(self):
        npoolname = self.get_value_xpath('/network/name')
        return npoolname

    def xml_get_netpool_mode(self):
        npoolmode = self.get_value_xpath('/network/forward/@mode')
        return npoolmode

    def xml_get_netpool_attr_list(self):
        pool_attr_list = []
        
        npooladdr = self.get_value_xpath('/network/ip/@address')
        npoolmask = self.get_value_xpath('/network/ip/@netmask')
        npoolstart = self.get_value_xpath('/network/ip/dhcp/range/@start')
        npoolend = self.get_value_xpath('/network/ip/dhcp/range/@end')

        pool_attr_list.append(npooladdr)
        pool_attr_list.append(npoolmask)
        pool_attr_list.append(npoolstart)
        pool_attr_list.append(npoolend)

        return pool_attr_list

class PoolXML(Virsh, XMLClass):

    def __init__(self, server, poolname=const.default_pool_name,
                 virt='xen', is_new_pool=True):

        XMLClass.__init__(self)
        if virt == 'XenFV':
            virt = 'xen'
        Virsh.__init__(self, str(virt).lower())
        self.pool_name = poolname
        self.server = server

        if is_new_pool is False:
            cmd = "virsh -c %s pool-dumpxml %s 2>/dev/null" % (self.vuri, self.pool_name)
            s, disk_xml = utils.run_remote(server, cmd)
            if s != 0:
                logger.error("Encounter error dump netxml")
                return None
            else:
                self.xml_string = disk_xml
                self.xdoc = minidom.parseString(self.xml_string)
                return

        pool = self.add_sub_node(self.xdoc, 'pool', type='dir')
        self.add_sub_node(pool, 'name', self.pool_name)
        target = self.add_sub_node(pool, 'target')
        self.add_sub_node(target, 'path', const._image_dir)

    def create_vpool(self):
        return self.run(self.server, 'pool-create', self.xml_string)

    def destroy_vpool(self):
        return self.run(self.server, 'pool-destroy', self.pool_name)

    def undefine_vpool(self):
        return self.run(self.server, 'pool-undefine', self.pool_name)

    def xml_get_diskpool_name(self):
        dpoolname = self.get_value_xpath('/pool/name')
        return dpoolname

    def xml_get_pool_attr_list(self, mode_type=1):
        pool_attr_list = []
        poolpath = self.get_value_xpath('/pool/target/path')
        pool_attr_list.append(poolpath)
        if mode_type == 3: #Netfs
           host = self.get_value_xpath('/pool/source/host/@name')
           pool_attr_list.append(host)
           src_dir = self.get_value_xpath('/pool/source/dir/@path')
           pool_attr_list.append(src_dir)

        return pool_attr_list

class VirtXML(Virsh, XMLClass):
    """Base class for all XML generation & operation"""
    dname = ""                # domain name

    def __init__(self, domain_type, name, uuid, mem, vcpu):
        is_XenFV = False
        if domain_type == "xenfv":
            is_XenFV = True
            domain_type = "xen"

        XMLClass.__init__(self)
        Virsh.__init__(self, domain_type)
        # domain root nodes
        domain = self.add_sub_node(self.xdoc, 'domain', type=domain_type)

        self.add_sub_node(domain, 'name', name)
        self.add_sub_node(domain, 'uuid', uuid)
        
        if is_XenFV is True:
            self.add_sub_node(domain, 'features')

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
        return isinstance(self, (XenXML, KVMXML, XenFVXML, LXCXML))

    def set_memory(self, mem):
        self.set_cdata('/domain/memory', mem * 1024)

    def set_uuid(self, uuid):
        self.set_cdata('/domain/uuid', uuid)

    def set_vcpu(self, vcpu):
        self.set_cdata('/domain/vcpu', vcpu)

    def set_mac(self, mac):
        self.set_attributes('/domain/devices/interface/mac', address=mac)

    def set_bridge_name(self, bridgename):
        self.set_attributes('/domain/devices/interface/source', 
                            bridge=bridgename)

    def set_nettype(self, nettype):
        self.set_attributes('/domain/devices/interface', 
                            type=nettype)

    def set_net_name(self, netname):
        self.set_attributes('/domain/devices/interface/source',
                            network=netname)

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

    @_x2str('/domain/features/pae')
    def xml_get_pae(self):
        pass

    @_x2str('/domain/features/acpi')
    def xml_get_acpi(self):
        pass

    @_x2str('/domain/features/apic')
    def xml_get_apic(self):
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
   
    def xml_get_net_bridge(self):
        bridgeStr = self.get_value_xpath(
                '/domain/devices/interface/source/@bridge')
        return bridgeStr

    def xml_get_net_network(self):
        networkStr = self.get_value_xpath(
                '/domain/devices/interface/source/@network')
        return networkStr

    def dumpxml(self, ip):
        cmd = 'virsh -c %s dumpxml %s 2>/dev/null' % (self.vuri, self.dname)
        s, o = utils.run_remote(ip, cmd)
        if s == 0:
            self.xml_string = o
            self.xdoc = minidom.parseString(self.xml_string)

    def _set_emulator(self, emu):
        self.add_sub_node('/domain/devices', 'emulator', emu)
    
    def _set_bridge(self, ip):
        br_list = live.available_virt_bridge(ip)
        if len(br_list) == 0:
            logger.error('No virtual bridges found')
            return None

        # pick the 1st virtual bridge
        br = br_list[0]
        interface = self.get_node('/domain/devices/interface')
        interface.setAttribute('type', 'bridge')
        self.add_sub_node(interface, 'source', bridge=br)
            
        return br

    def _set_vbridge(self, ip, virt_type, net_name):
        vbr = get_bridge_from_network_xml(net_name, ip, virt=virt_type)

        interface = self.get_node('/domain/devices/interface')
        interface.setAttribute('type', 'bridge')
        self.add_sub_node(interface, 'source', bridge=vbr)

        return vbr

    def set_interface_details(self, devices, net_mac, net_type, net_name, 
                              virt_type):
        interface = self.add_sub_node(devices, 'interface', type=net_type)
        self.add_sub_node(interface, 'mac', address=net_mac)
        if net_type == 'bridge':
            self._set_vbridge(CIM_IP, virt_type, net_name)
        elif net_type == 'network':
            self.add_sub_node(interface, 'source', network=net_name)
        elif net_type == 'ethernet':
            pass
        elif net_type == 'user':
            pass
        else:
            logger.error("%s is not a valid network type", net_type)
            sys.exit(1)


class VirtCIM:
    def __init__(self, virt, dom_name, uuid, pae, acpi, apic, disk_dev, 
                 disk_source, net_type, net_name, net_mac, vcpus, mem,
                 mem_allocunits, emu_type, grstype, ip,
                 is_ipv6_only, port_num, kmap, irstype, btype, vnc_passwd):
        self.virt = virt
        self.domain_name = dom_name
        self.err_rc = None
        self.err_desc = None
        self.vssd = vsms.get_vssd_mof(virt, dom_name, uuid=uuid, pae=pae, 
                                      acpi=acpi, apic=apic)
        self.nasd = vsms.get_nasd_class(virt)(type=net_type, 
                                              mac=net_mac,
                                              name=dom_name,
                                              virt_net=net_name)
        if virt == 'LXC':
            self.pasd = vsms.get_pasd_class(virt)(name=dom_name)
            self.dasd = vsms.get_dasd_class(virt)(disk_dev, disk_source,
                                                  dom_name)
            self.gasd = None 
        else:
            self.pasd = vsms.get_pasd_class(virt)(vcpu=vcpus, name=dom_name)
            self.dasd = vsms.get_dasd_class(virt)(disk_dev, disk_source,
                                                  dom_name, emu_type)
            self.gasd = vsms.get_gasd_class(virt)(name=dom_name, 
                                                  res_sub_type=grstype, ip=ip,
                                                  ipv6_flag=is_ipv6_only, 
                                                  lport=port_num, keymap=kmap, 
                                                  vnc_passwd=vnc_passwd)
        self.masd = vsms.get_masd_class(virt)(megabytes=mem, 
                                              mallocunits=mem_allocunits,
                                              name=dom_name)
        self.iasd = vsms.get_iasd_class(virt)(name=dom_name, 
                                              res_sub_type=irstype, 
                                              bus_type=btype)
        if virt == "KVM":
            dasd = vsms.get_dasd_class(virt)
            self.cdrom_dasd = dasd(dev=const.KVM_default_cdrom_dev,
                                   source="",
                                   name=dom_name,
                                   emu_type=1)
    def cim_define(self, ip, ref_conf=None):
        service = vsms.get_vsms_class(self.virt)(ip)
        sys_settings = str(self.vssd)

        res_settings = []
        if self.dasd is not None:
            res_settings.append(str(self.dasd))
        if self.pasd is not None:
            res_settings.append(str(self.pasd))
        if self.masd is not None:
            res_settings.append(str(self.masd))
        if self.nasd is not None:
            if self.virt == 'LXC' and const.LXC_netns_support is False:
                pass
            else:
                res_settings.append(str(self.nasd))

        # CDROM device
        if self.virt == "KVM":
            res_settings.append(str(self.cdrom_dasd))

        curr_cim_rev, changeset = get_provider_version(self.virt, ip)
        if curr_cim_rev >= vsms_graphics_sup:
            if self.gasd is not None:
                res_settings.append(str(self.gasd))

        if curr_cim_rev >= vsms_inputdev_sup:
            if self.iasd is not None:
                res_settings.append(str(self.iasd))

        if ref_conf is None:
             ref_conf = ' '

        try:
            service.DefineSystem(SystemSettings=sys_settings,
                                 ResourceSettings=res_settings,
                                 ReferenceConfiguration=ref_conf)
        except pywbem.CIMError, (rc, desc):
            logger.error('Got CIM error %s with return code %s', desc, rc)
            self.err_rc = rc 
            self.err_desc = desc 
            return False

        except Exception, details:
            logger.error('Got error %s with exception %s',
                         details, details.__class__.__name__)
            return False

        set_uuid(viruuid(self.domain_name, ip, self.virt))
        return True

    def cim_destroy(self, ip):
        service = vsms.get_vsms_class(self.virt)(ip)
        cs_cn = get_typed_class(self.virt, 'ComputerSystem')
        keys = { 'Name' : self.domain_name, 'CreationClassName' : cs_cn}
        target = pywbem.cim_obj.CIMInstanceName(cs_cn, keybindings = keys)
        try:
            ret = service.DestroySystem(AffectedSystem=target)
        except pywbem.CIMError, (rc, desc):
            logger.error('Got CIM error %s with return code %s', desc, rc)
            self.err_rc = rc 
            self.err_desc = desc 
            return False

        except Exception, details:
            logger.error('Error invoking DestroySystem')
            logger.error('Got error %s with exception %s',
                         details, details.__class__.__name__)
            return False
        return ret[0] == 0

    def check_guest_state(self, server, en_state, req_state=None):
        if req_state is None:
            req_state = en_state

        cs_class = get_typed_class(self.virt, 'ComputerSystem')
        keys = { 'Name' : self.domain_name, 'CreationClassName' : cs_class }

        try:
            cs = GetInstance(server, cs_class, keys)
            if cs is None or cs.Name != self.domain_name:
                raise Exception("Wrong guest instance")

            if cs.EnabledState != en_state:
                raise Exception("EnabledState is %i, expected %i." % \
                                (cs.EnabledState, en_state))

            if cs.RequestedState != req_state:
                raise Exception("RequestedState is %i, expected %i." % \
                                (cs.RequestedState, req_state))

        except Exception, detail:
            logger.error("Unable to check guest state")
            logger.error("Exception: %s", detail)
            return FAIL

        return PASS

    def cim_state_change(self, server, req_state, req_timeout, poll_time, 
                         en_state=None): 
        if en_state is None:
            en_state = req_state

        cs = None
        cs_class = get_typed_class(self.virt, 'ComputerSystem')
        keys = { 'Name' : self.domain_name, 'CreationClassName' : cs_class }
        cs = GetInstance(server, cs_class, keys)
        if cs is None or cs.Name != self.domain_name:
            return FAIL 

        try:
            req_state_change = pywbem.cim_types.Uint16(req_state)
            time_period = pywbem.cim_types.CIMDateTime(req_timeout)
            cs.RequestStateChange(RequestedState=req_state_change,
                                  TimeoutPeriod=time_period)

        except pywbem.CIMError, (rc, desc):
            logger.error('Got CIM error %s with return code %s', desc, rc)
            self.err_rc = rc 
            self.err_desc = desc 
            return FAIL 

        except Exception, detail:
            logger.error("In fn cim_state_change()")
            logger.error("Failed to change state of the domain '%s'", cs.Name)
            logger.error("Exception: %s", detail)
            return FAIL 

        for i in range(1, (poll_time + 1)):
            status = self.check_guest_state(server, en_state, req_state)
            if status == PASS:
                break

        return status

    def cim_start(self, server, req_time=const.TIME, poll_time=30): 
        return self.cim_state_change(server, const.CIM_ENABLE, 
                                     req_time, poll_time)

    def cim_disable(self, server, req_time=const.TIME, poll_time=30): 
        return self.cim_state_change(server, const.CIM_DISABLE, 
                                     req_time, poll_time)

    def cim_shutdown(self, server, req_time=const.TIME, poll_time=30): 
        return self.cim_state_change(server, const.CIM_SHUTDOWN, 
                                     req_time, poll_time)

    def cim_no_state_change(self, server, req_time=const.TIME, poll_time=30): 
        return self.cim_state_change(server, const.CIM_NOCHANGE, 
                                     req_time, poll_time) 

    def cim_suspend(self, server, req_time=const.TIME, poll_time=30): 
        return self.cim_state_change(server, const.CIM_SUSPEND, 
                                     req_time, poll_time) 

    def cim_pause(self, server, req_time=const.TIME, poll_time=30): 
        return self.cim_state_change(server, const.CIM_PAUSE, 
                                     req_time, poll_time)
        
    def cim_reboot(self, server, req_time=const.TIME, poll_time=30): 
        return self.cim_state_change(server, const.CIM_REBOOT, 
                                     req_time, poll_time, const.CIM_ENABLE) 

    def cim_reset(self, server, req_time=const.TIME, poll_time=30): 
        return self.cim_state_change(server, const.CIM_RESET, 
                                     req_time, poll_time, const.CIM_ENABLE)

    def set_sys_settings(self, vssd):
        self.vssd = vssd 

    def set_res_settings(self, rasd_list):
        for cn, rasd in rasd_list.iteritems():
            if cn.find("MemResourceAllocationSettingData") >= 0:
                self.masd = rasd
            elif cn.find("ProcResourceAllocationSettingData") >= 0:
                self.pasd = rasd
            elif cn.find("DiskResourceAllocationSettingData") >= 0:
                self.dasd = rasd
            elif cn.find("NetResourceAllocationSettingData") >= 0:
                self.nasd = rasd
            elif cn.find("GraphicsResourceAllocationSettingData") >= 0:
                self.gasd = rasd

    def verify_error_msg(self, exp_rc, exp_desc):
        try:
            rc = int(self.err_rc)

            if rc != exp_rc:
                raise Exception("Error code Mismatch, Got rc: %d, exp %d." \
                                % (rc, exp_rc))

            if not exp_desc in self.err_desc:
                raise Exception("Desc Mismatch, Got desc: '%s', exp '%s'" \
                               % (self.err_desc, exp_desc))

        except Exception, details:
            logger.error(details)
            return FAIL

        return PASS 

class XenXML(VirtXML, VirtCIM):

    secondary_disk_path = const.Xen_secondary_disk_path
    
    def __init__(self, test_dom=const.default_domname,
                       uuid=None,
                       pae=False,
                       acpi=False,
                       apic=False,
                       mem=const.default_memory,
                       mem_allocunits=const.default_mallocunits,
                       vcpus=const.default_vcpus,
                       mac=None,
                       disk_file_path=const.Xen_disk_path,
                       disk=const.Xen_default_disk_dev, 
                       ntype=const.default_net_type,
                       net_name=const.default_network_name,
                       emu_type=None, grstype="vnc", address=None,
                       is_ipv6_only=None,
                       port_num='-1', keymap="en-us", irstype="mouse", 
                       btype="xen", vnc_passwd=None): 
        if not (os.path.exists(const.Xen_kernel_path) \
                and os.path.exists(const.Xen_init_path)):
            logger.error('ERROR: Either the kernel image '
                         'or the init_path does not exist')
            sys.exit(1)
        VirtXML.__init__(self, 'xen', test_dom, set_uuid(), mem, vcpus)
        self._os(const.Xen_kernel_path, const.Xen_init_path)
        self._devices(disk_file_path, disk, ntype, mac, net_name)

        VirtCIM.__init__(self, 'Xen', test_dom, uuid, pae, acpi, apic, disk, 
                         disk_file_path, ntype, net_name, mac, vcpus, mem, 
                         mem_allocunits, emu_type, grstype, address, 
                         is_ipv6_only, port_num, keymap, irstype, btype, 
                         vnc_passwd)

    def _os(self, os_kernel, os_initrd):
        os = self.get_node('/domain/os')
        self.add_sub_node(os, 'type', 'linux')
        self.add_sub_node(os, 'kernel', os_kernel)
        self.add_sub_node(os, 'initrd', os_initrd)
        self.add_sub_node(os, 'cmdline', 'TERM=xterm')

    def _devices(self, disk_img, disk_dev, net_type, net_mac, net_name):
        devices = self.get_node('/domain/devices')
        
        disk = self.add_sub_node(devices, 'disk', type='file', device='disk')
        self.add_sub_node(disk, 'driver', name='file')
        self.add_sub_node(disk, 'source', file=disk_img)
        self.add_sub_node(disk, 'target', dev=disk_dev)
        self.set_interface_details(devices, net_mac, net_type, net_name, 'Xen')
        self.add_sub_node(devices, 'input', type='mouse', bus='xen')
        self.add_sub_node(devices, 'graphics', type='vnc', port='5900',
                          keymap='en-us')


    def set_bootloader(self, ip, gtype=0):
        bldr = bootloader(ip, gtype)
        self.add_sub_node('/domain', 'bootloader', bldr)
        self.vssd = vsms.get_vssd_mof(self.virt, self.domain_name, bldr=bldr)
        return bldr

    def set_bridge(self, ip):
        self.nasd.NetworkType = 'bridge'
        return self._set_bridge(ip)

    def set_vbridge(self, ip, net_name):
        self.nasd.NetworkType = 'bridge'
        return self._set_vbridge(ip, 'Xen', net_name)


class KVMXML(VirtXML, VirtCIM):

    secondary_disk_path = const.KVM_secondary_disk_path
    
    def __init__(self, test_dom=const.default_domname,
                       uuid=None,
                       pae=False,
                       acpi=False,
                       apic=False,
                       mem=const.default_memory,
                       mem_allocunits=const.default_mallocunits,
                       vcpus=const.default_vcpus,
                       mac=None,
                       disk_file_path=const.KVM_disk_path,
                       disk=const.KVM_default_disk_dev, 
                       ntype=const.default_net_type,
                       net_name=const.default_network_name,
                       emu_type=None, grstype="vnc", address=None,
                       is_ipv6_only=None,
                       port_num='-1', keymap="en-us", irstype="mouse", 
                       btype="ps2", vnc_passwd=None):
        if not os.path.exists(disk_file_path):
            logger.error('Error: Disk image does not exist')
            sys.exit(1)
        VirtXML.__init__(self, 'kvm', test_dom, set_uuid(), mem, vcpus)
        VirtCIM.__init__(self, 'KVM', test_dom, uuid, pae, acpi, apic, disk, 
                         disk_file_path, ntype, net_name, mac, vcpus, mem, 
                         mem_allocunits, emu_type, grstype, address, 
                         is_ipv6_only, port_num, keymap, irstype, btype, 
                         vnc_passwd)
        self._os()
        self._devices(const.KVM_default_emulator, ntype,
                      disk_file_path, disk, mac, net_name)


    def _os(self):
        self.add_sub_node('/domain/os', 'type', 'hvm')

    def _devices(self, emu, net_type, disk_img, disk_dev, net_mac, net_name):
        devices = self.get_node('/domain/devices')

        self.add_sub_node(devices, 'emulator', emu)
        disk = self.add_sub_node(devices, 'disk', type='file', device='disk')
        self.add_sub_node(disk, 'source', file=disk_img)
        self.add_sub_node(disk, 'target', dev=disk_dev)

        cdrom = self.add_sub_node(devices, 'disk', type='file', device='cdrom')
        self.add_sub_node(cdrom, 'source', file="")
        self.add_sub_node(cdrom, 'target', dev=const.KVM_default_cdrom_dev)

        self.add_sub_node(devices, 'input', type='mouse', bus='ps2')
        self.add_sub_node(devices, 'graphics', type='vnc', port='5900',
                          keymap='en-us')

        self.set_interface_details(devices, net_mac, net_type, net_name, 'KVM')

    def set_emulator(self, emu):
        return self._set_emulator(emu)
    
    def set_bridge(self, ip):
        return self._set_bridge(ip)

    def set_vbridge(self, ip, net_name):
        return self._set_vbridge(ip, 'KVM', net_name)


class XenFVXML(VirtXML, VirtCIM):

    secondary_disk_path = const.XenFV_secondary_disk_path

    def __init__(self, test_dom=const.default_domname,
                       uuid=None,              
                       pae=True,
                       acpi=True,
                       apic=True,
                       mem=const.default_memory,
                       mem_allocunits=const.default_mallocunits,
                       vcpus=const.default_vcpus,
                       mac=None,
                       disk_file_path=const.XenFV_disk_path,
                       disk=const.XenFV_default_disk_dev, 
                       ntype=const.default_net_type,
                       net_name=const.default_network_name,
                       emu_type=None, grstype="vnc", 
                       address=None, is_ipv6_only=None, port_num='-1', 
                       keymap="en-us",
                       irstype="mouse", btype="ps2", vnc_passwd=None):
        if not os.path.exists(disk_file_path):
            logger.error('Error: Disk image does not exist')
            sys.exit(1)
        VirtXML.__init__(self, 'xenfv', test_dom, set_uuid(), mem, vcpus)
        VirtCIM.__init__(self, 'XenFV', test_dom, uuid, pae, acpi, apic, disk,
                         disk_file_path, ntype, net_name, mac, vcpus, mem, 
                         mem_allocunits, emu_type, grstype, address, 
                         is_ipv6_only, port_num, 
                         keymap, irstype, btype, vnc_passwd)
        self._os(const.XenFV_default_loader)
        self._devices(const.XenFV_default_emulator,
                      ntype, mac, net_name, disk_file_path, disk) 

    def _os(self, os_loader):
        os = self.get_node('/domain/os')
        self.add_sub_node(os, 'type', 'hvm')
        self.add_sub_node(os, 'loader', os_loader)
        self.add_sub_node(os, 'boot', dev='hd')

    def _devices(self, emu, net_type, net_mac, net_name, disk_img, disk_dev):
        devices = self.get_node('/domain/devices')

        self.add_sub_node(devices, 'emulator', emu)
        self.add_sub_node(devices, 'graphics', type='vnc', port='5900',
                          keymap='en-us')
        self.add_sub_node(devices, 'input', type='mouse', bus='xen')
        disk = self.add_sub_node(devices, 'disk', type='file')
        self.add_sub_node(disk, 'source', file=disk_img)
        self.add_sub_node(disk, 'target', dev=disk_dev)
        self.set_interface_details(devices, net_mac, net_type, net_name, 'Xen')

    def set_emulator(self, emu):
        return self._set_emulator(emu)

    def set_bridge(self, ip):
        return self._set_bridge(ip)

    def set_vbridge(self, ip, net_name):
        return self._set_vbridge(ip, 'XenFV', net_name)

class LXCXML(VirtXML, VirtCIM):

    def __init__(self, test_dom=const.default_domname,
                       uuid=None,
                       mem=const.default_memory,
                       vcpus=const.default_vcpus,
                       mac=None,
                       ntype=const.default_net_type,
                       net_name=const.default_network_name,
                       tty=const.LXC_default_tty, grstype="vnc",
                       address=None, is_ipv6_only=None, port_num='-1', 
                       keymap="en-us",
                       irstype="mouse", btype="usb", vnc_passwd=None):
        VirtXML.__init__(self, 'lxc', test_dom, set_uuid(), mem, vcpus)
        # pae, acpi and apic parameters doesn't make sense here, so we
        # statically set them to False (a.k.a. ignore them)
        VirtCIM.__init__(self, 'LXC', test_dom, uuid, False, False, False, 
                         const.LXC_default_mp, const.LXC_default_source, 
                         ntype, net_name, mac, vcpus, mem, 
                         const.default_mallocunits, None, grstype, 
                         address, is_ipv6_only, port_num, keymap, irstype, 
                         btype, vnc_passwd)
        self._os(const.LXC_init_path)
        self._devices(const.LXC_default_emulator, mac, ntype, net_name, const.LXC_default_tty)
        self.create_lxc_file(CIM_IP, const.LXC_init_path)

    def _os(self, os_init):
        os = self.get_node('/domain/os')
        self.add_sub_node(os, 'init', os_init)
        self.add_sub_node(os, 'type', 'exe')

    def _devices(self, emu, net_mac, net_type, net_name, tty_set):
        devices = self.get_node('/domain/devices')
    
        self.add_sub_node(devices, 'emulator', emu) 
  
        if const.LXC_netns_support is True:
            self.set_interface_details(devices, net_mac, net_type, 
                                       net_name, 'LXC')

        self.add_sub_node(devices, 'console', tty = tty_set)

    def set_emulator(self, emu):
        return self._set_emulator(emu)

    def create_lxc_file(self, ip, lxc_file):
        try:
            f = open(lxc_file, 'w')
            f.write('%s' % 'exec /bin/sh')
            cmd = 'chmod +x %s' % lxc_file
            s, o = utils.run_remote(ip, cmd)
            f.close()
        except Exception:
            logger.error("Creation of LXC file Failed")
            return False


def get_class(virt):
    if virt in virt_types:
        return eval(virt + 'XML')

def set_default(server):
    dict = {}
    dict['default_sysname'] = live.full_hostname(server)
    dict['default_port'] = CIM_PORT
    dict['default_url'] = "%s:%s" % (dict['default_sysname'],
                                     dict['default_port'])
    dict['default_ns'] = CIM_NS
    dict['default_name'] = "Test"
    dict['default_dump'] = False
    dict['default_print_ind'] = False
    dict['default_username'] = CIM_USER
    dict['default_password'] = CIM_PASS
    dict['default_auth'] = (dict['default_username'], dict['default_password'])

    return dict
