#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
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

import pywbem
from CimTest import Globals
from CimTest.ReturnCodes import FAIL, PASS
from CimTest.Globals import logger
from XenKvmLib.xm_virt_util import network_by_bridge, virsh_vcpuinfo, \
get_bridge_from_network_xml

def print_mod_err_msg(func_str, details):
        logger.error('Error invoking ModifyRS: %s', func_str)
        logger.error(details)

def call_modify_res(service, rasd):
    try:
        output = service.ModifyResourceSettings(ResourceSettings = [str(rasd)])
        if len(output) == 0:
            raise Exception("ModifyResourceSettings failed to return output")

        out_param = "ResultingResourceSettings"
        if output[1][out_param] is None:
            raise Exception("ModifyResourceSettings failed to return %s" % \
                            out_param)
    except Exception, details:
        logger.error(details)
        return FAIL, None

    return PASS, output[1][out_param] 

def mod_disk_res(server, service, cxml, dasd, ndpath):
    try:
        status, output = call_modify_res(service, dasd)
        if status != PASS:
            raise Exception("ModifyResourceSettings call failed")

        cxml.dumpxml(server)
        dpath = cxml.xml_get_disk_source()
        if dpath != ndpath:
            logger.error("Got %s, exp %s.", dpath, ndpath)
            raise Exception('Error changing rs for disk path')
        logger.info('good status for disk path')
    except Exception, details:
        print_mod_err_msg("mod_disk_res", details)
        return FAIL

    return PASS

def mod_net_res(server, service, virt, cxml, nasd, ntype, net_name):
    try:
        status, output = call_modify_res(service, nasd)
        if status != PASS:
            raise Exception("ModifyResourceSettings call failed")

        cxml.dumpxml(server)
        type = cxml.xml_get_net_type()

        if virt == "KVM":
            name = cxml.xml_get_net_network()
        else:
            if type == "bridge":
                type = "network"
            br_name = cxml.xml_get_net_bridge()
            name = network_by_bridge(br_name, server, virt)

        if type != ntype or name != net_name:
            logger.error('Got %s, exp %s. Got %s, exp %s',
                         type, ntype, name, net_name)
            raise Exception('Error changing rs for net mac')
        logger.info('good status for net mac')
    except Exception, details:
        print_mod_err_msg("mod_net_res", details)
        return FAIL

    return PASS

def mod_mem_res(server, service, cxml, masd, nmem):
    try:
        status, output = call_modify_res(service, masd)
        if status != PASS:
            raise Exception("ModifyResourceSettings call failed")

        cxml.dumpxml(server)
        mem = cxml.xml_get_mem()
        if int(mem) != int(nmem) * 1024:
            logger.error("Got %d, exp %d.", int(mem), (int(nmem) * 1024))
            raise Exception('Error changing rs for mem')
        logger.info('good status for mem')
    except Exception, details:
        print_mod_err_msg("mod_mem_res", details)
        return FAIL

    return PASS

def mod_vcpu_res(server, service, cxml, pasd, ncpu, virt):
    try:
        status, output = call_modify_res(service, pasd)
        if status != PASS:
            raise Exception("ModifyResourceSettings call failed")

        cxml.dumpxml(server)
        dom = cxml.xml_get_dom_name()
        cpu = virsh_vcpuinfo(server, dom, virt)
        if cpu is None:
            logger.info("Unable to get vcpuinfo from virsh, using XML values")
            cpu = cxml.xml_get_vcpu()
        if int(cpu) != int(ncpu):
            logger.error("Got %d, exp %d.", int(cpu), int(ncpu))
            raise Exception('Error changing rs for vcpu')
        logger.info('good status for vcpu')
    except Exception, details:
        print_mod_err_msg("mod_vcpu_res", details)
        return FAIL

    return PASS

def print_add_err_msg(func_str, details):
        logger.error('Error invoking AddRS: %s', func_str)
        logger.error(details)

def call_add_res(service, rasd, vssd_ref):
    try:
        output = service.AddResourceSettings(AffectedConfiguration=vssd_ref,
                                             ResourceSettings=[str(rasd)])
        if len(output) == 0:
            raise Exception("AddResourceSettings failed to return output")

        out_param = "ResultingResourceSettings"
        if output[1][out_param] is None:
            raise Exception("AddResourceSettings failed to return %s" % \
                            out_param)
    except Exception, details:
        logger.error(details)
        return FAIL

    return PASS

def add_disk_res(server, service, cxml, vssd_ref, dasd, attr):
    try:
        status = call_add_res(service, dasd, vssd_ref)
        if status != PASS:
            raise Exception("AddResourceSettings call failed")

        cxml.dumpxml(server)
        disk_dev = cxml.get_value_xpath(
                   '/domain/devices/disk/target/@dev[. = "%s"]' % attr['nddev'])
        dpath = cxml.get_value_xpath(
               '/domain/devices/disk/source/@file[. = "%s"]' % attr['src_path'])
        if disk_dev != attr['nddev'] or dpath != attr['src_path']:
            logger.error("Got %s, exp %s.  Got %s, exp %s", disk_dev, 
                         attr['nddev'], dpath, attr['src_path'])
            raise Exception('Error adding rs for disk_dev')
        logger.info('good status for disk path')
    except Exception, details:
        print_add_err_msg("add_disk_res", details)
        return FAIL

    return PASS

def add_net_res(server, service, virt, cxml, vssd_ref, nasd, attr):
    try:
        status = call_add_res(service, nasd, vssd_ref)
        if status != PASS:
            raise Exception("AddResourceSettings call failed")

        cxml.dumpxml(server)
    
        mac = cxml.get_value_xpath(
                              '/domain/devices/interface/mac/@address[. = "%s"]'
                              % attr['nmac'])

        if virt == "KVM":
            # For KVM bridge types, compare the source bridge
            if attr['ntype'] == 'bridge':
                name = cxml.get_value_xpath(
                           '/domain/devices/interface/source/@bridge[. = "%s"]'
                           % attr['virt_net'])
                attr_name = attr['virt_net']
            # For KVM network types, compare the network name
            else:
                name = cxml.get_value_xpath(
                           '/domain/devices/interface/source/@network[. = "%s"]'
                           % attr['net_name'])
                attr_name = attr['net_name']
            if mac != attr['nmac'] or name != attr_name:
                logger.error("MAC: Got %s, exp %s. NAME: Got %s, exp %s.",
                             mac, attr['nmac'], name, attr['virt_net'])
                raise Exception('Error adding rs for net mac')
            
        else:
            # For Xen, network interfaces are converted to bridge interfaces.
            br = get_bridge_from_network_xml(attr['net_name'], server, virt)
            name = cxml.get_value_xpath(
                           '/domain/devices/interface/source/@bridge[. = "%s"]'
                           % br)
            if name != None:
                name = attr['net_name']

            if mac != attr['nmac'] or name != attr['net_name']:
                logger.error("MAC: Got %s, exp %s. NAME: Got %s, exp %s. br %s",
                             mac, attr['nmac'], name, attr['net_name'], br)
                raise Exception('Error adding rs for net mac')

        logger.info('good status for net_mac')
    except Exception, details:
        print_add_err_msg("add_net_res", details)
        return FAIL

    return PASS

