#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Guolian Yun <yunguol@cn.ibm.com>
#    Kaitlin Rupert <karupert@us.ibm.com>
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

import sys
import pywbem
from pywbem.cim_obj import CIMInstanceName
from VirtLib import utils
from VirtLib.live import network_by_bridge
from XenKvmLib import vsms
from XenKvmLib import vxml
from CimTest.Globals import logger
from CimTest.Globals import do_main
from CimTest.ReturnCodes import PASS, FAIL
from XenKvmLib import vsms_util
from XenKvmLib.const import default_network_name

sup_types = ['Xen', 'KVM', 'XenFV']
default_dom = 'rstest_domain'
ntype = 'network'
cpu = 2
ncpu = 1
nmem = 256 

def cleanup_env(ip, virt, cxml):
    cxml.destroy(ip)
    cxml.undefine(ip)

@do_main(sup_types)
def main():
    options = main.options 

    service = vsms.get_vsms_class(options.virt)(options.ip)
    cxml = vxml.get_class(options.virt)(default_dom, vcpus=cpu)
    ndpath = cxml.secondary_disk_path
    dasd = vsms.get_dasd_class(options.virt)(dev=cxml.xml_get_disk_dev(),
                                             source=ndpath, 
                                             name=default_dom)
    
    nasd = vsms.get_nasd_class(options.virt)(type=ntype, 
                                             mac=cxml.xml_get_net_mac(),
                                             name=default_dom,
                                             virt_net=default_network_name)
    masd = vsms.get_masd_class(options.virt)(megabytes=nmem, name=default_dom)
    pasd = vsms.get_pasd_class(options.virt)(vcpu=ncpu, name=default_dom)

    status = FAIL
  
    if options.virt == "KVM":
        test_cases = ["define"]
    else:
        test_cases = ["define", "start"]

    for case in test_cases:
        #Each time through, define guest using a default XML
        cxml.undefine(options.ip)
        cxml = vxml.get_class(options.virt)(default_dom, vcpus=cpu)
        ret = cxml.define(options.ip)
        if not ret:
            logger.error("Failed to define the dom: %s", default_dom)
            cleanup_env(options.ip, options.virt, cxml)
            return FAIL
        if case == "start":
            ret = cxml.start(options.ip)
            if not ret:
                logger.error("Failed to start the dom: %s", default_dom)
                cleanup_env(options.ip, options.virt, cxml)
                return FAIL

        status = vsms_util.mod_vcpu_res(options.ip, service, cxml, pasd, ncpu,
                                        options.virt)
        if status != PASS:
            break

        status = vsms_util.mod_mem_res(options.ip, service, cxml, masd, nmem)
        if status != PASS:
            break

        #Unable to modify net and disk devices while guest is running
        if case == "start":
            break

        status = vsms_util.mod_disk_res(options.ip, service, cxml, dasd, ndpath)
        if status != PASS:
            break

        status = vsms_util.mod_net_res(options.ip, service, options.virt, cxml,
                                       nasd, ntype, default_network_name)
        if status != PASS:
            break

    cleanup_env(options.ip, options.virt, cxml)

    return status

if __name__ == "__main__":
    sys.exit(main())
 
