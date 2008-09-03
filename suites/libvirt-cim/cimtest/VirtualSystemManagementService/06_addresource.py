#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
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
import random
import pywbem
from pywbem.cim_obj import CIMInstanceName
from VirtLib import utils
from XenKvmLib import vsms
from XenKvmLib import vxml
from XenKvmLib.classes import get_typed_class
from CimTest.Globals import logger
from XenKvmLib.const import do_main
from CimTest.ReturnCodes import FAIL, PASS
from XenKvmLib import vsms_util
from XenKvmLib.const import default_network_name 

sup_types = ['Xen', 'KVM', 'XenFV']
default_dom = 'rstest_domain'
nmac = '99:aa:bb:cc:ee:ff'
ntype = 'network'
npool_name = default_network_name + str(random.randint(1, 100)) 

def cleanup_env(ip, virt, cxml):
    cxml.destroy(ip)
    cxml.undefine(ip)

@do_main(sup_types)
def main():
    options = main.options

    if options.virt == 'KVM':
        nddev = 'hdb'
    else:
        nddev = 'xvdb'

    service = vsms.get_vsms_class(options.virt)(options.ip)
    cxml = vxml.get_class(options.virt)(default_dom)
    classname = get_typed_class(options.virt, 'VirtualSystemSettingData')
    inst_id = '%s:%s' % (options.virt, default_dom)
    vssd_ref = CIMInstanceName(classname, keybindings = {
                               'InstanceID' : inst_id,
                               'CreationClassName' : classname})
    dasd = vsms.get_dasd_class(options.virt)(dev=nddev,
                                             source=cxml.secondary_disk_path,
                                             name=default_dom)
    disk_attr = { 'nddev' : nddev,
                  'src_path' : cxml.secondary_disk_path
                }

    nasd = vsms.get_nasd_class(options.virt)(type=ntype,
                                             mac=nmac,
                                             name=default_dom,
                                             virt_net=npool_name)

    net_attr = { 'ntype' : ntype,
                 'net_name' : npool_name,
                 'nmac' : nmac
               }

    status = FAIL

    if options.virt == "KVM": 
        test_cases = ["define"]
    else:
        test_cases = ["define", "start"]

    for case in test_cases:
        #Each time through, define guest using a default XML
        cxml.undefine(options.ip)
        cxml = vxml.get_class(options.virt)(default_dom)
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

        status = vsms_util.add_disk_res(options.ip, service, cxml, vssd_ref,
                                         dasd, disk_attr)
        if status != PASS:
            break

        status = vsms_util.add_net_res(options.ip, service, options.virt, cxml,
                                       vssd_ref, nasd, net_attr)
        if status != PASS:
            break

    cleanup_env(options.ip, options.virt, cxml)

    return status

if __name__ == "__main__":
    sys.exit(main())
    
