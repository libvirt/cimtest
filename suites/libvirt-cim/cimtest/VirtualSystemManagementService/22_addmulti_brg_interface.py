#!/usr/bin/python
#
# Copyright 2009 IBM Corp.
#
# Authors:
#    Yogananth subramanian <anantyog@linux.vnet.ibm.com>
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
# The testcase verifies adding multiple bridge type interface to domain
#
import sys
from XenKvmLib.enumclass import GetInstance, EnumNames
from XenKvmLib.classes import get_typed_class, inst_to_mof
from XenKvmLib.vxml import XenXML, KVMXML, get_class
from CimTest.Globals import logger
from XenKvmLib.const import do_main, get_provider_version, sles11_changeset
from CimTest.ReturnCodes import PASS, FAIL, XFAIL_RC
from XenKvmLib.common_util import create_netpool_conf,destroy_netpool
from XenKvmLib.vsms import get_vsms_class, get_nasd_class
from XenKvmLib.vsms_util import add_net_res

sup_types = ['Xen', 'KVM', 'XenFV']
test_dom = "my_domain1"
default_net = "my_network0"
test_net = "my_network1"
test_mac = '88:aa:bb:cc:ee:ff'
default_mac = "00:11:33:33:44:55"
ntype = 'bridge'
default_brg = 'mybr0'
test_brg = 'mybr1'
bug_libvirt = "00015"

def cleanup_env(ip, virt, net_name, cxml):
    cxml.cim_destroy(ip)
    cxml.undefine(ip)
    destroy_netpool(ip, virt, net_name)

@do_main(sup_types)
def main():
    options = main.options

    status, net_name = create_netpool_conf(options.ip, options.virt,
                                           net_name=default_net,
                                           bridge_name=default_brg)
    if status != PASS:
        logger.error('Unable to create network pool %s',
                      default_net)
        return FAIL

    service = get_vsms_class(options.virt)(options.ip)
    classname = get_typed_class(options.virt, 'VirtualSystemSettingData')

    # Seems ACPI needs to be set for KVM in order for hotplug to work right
    if options.virt == "KVM":
        vsxml = get_class(options.virt)(test_dom, mac=default_mac, ntype=ntype,
                                        net_name=default_brg, acpi=True)
    else:
        vsxml = get_class(options.virt)(test_dom, mac=default_mac, ntype=ntype,
                                        net_name=default_brg)
    try:
        ret = vsxml.cim_define(options.ip)
        if not ret:
            raise Exception("Failed to define the dom: %s" % default_dom)

        ret = vsxml.cim_start(options.ip)
        if ret:
            raise Exception("Failed to define the dom: %s" % default_dom)

        if options.virt == "XenFV":
            prefix = "Xen"
        else:
            prefix = options.virt 

        inst_id = '%s:%s' % (prefix, test_dom)
        netpool = EnumNames(options.ip, classname)
        vssd_ref = None
        for i in range(0, len(netpool)):
            ret_pool = netpool[i].keybindings['InstanceID']
            if ret_pool == inst_id:
                vssd_ref = netpool[i]
                break

        if vssd_ref == None:
            raise Exception("Failed to get vssd_ref for '%s'"% test_dom)

        status, net_name = create_netpool_conf(options.ip, options.virt,
                                               net_name=test_net,
                                               bridge_name=test_brg)
        if status != PASS:
            raise Exception('Unable to create network pool %s'%
                            test_net)

        nasd = get_nasd_class(options.virt)(type=ntype, mac=test_mac,
                                            name=test_dom, virt_net=test_brg)

        net_attr = { 'ntype'    : ntype,
                     'net_name' : net_name,
                     'nmac'     : test_mac,
                     'virt_net' : test_brg
                   }

        status = add_net_res(options.ip, service, options.virt, vsxml,
                             vssd_ref, nasd, net_attr)
        destroy_netpool(options.ip, options.virt, net_name=test_net)

        if status != PASS:
            status = XFAIL_RC(bug_libvirt)

        destroy_netpool(options.ip, options.virt, net_name=test_net)

    except Exception, details:
        logger.error(details)
        status = FAIL

    cleanup_env(options.ip, options.virt, default_net, vsxml)
    return status

if __name__ == "__main__":
    sys.exit(main())
