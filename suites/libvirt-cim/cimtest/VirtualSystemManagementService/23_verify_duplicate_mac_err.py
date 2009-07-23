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
# This testcase verifies definig network interface with conflicting MAC
#

from sys import exit
from random import randint
from pywbem import CIM_ERR_FAILED
from XenKvmLib.vsms_util import add_net_res
from XenKvmLib.vsms import get_vsms_class, get_nasd_class
from XenKvmLib.vxml import get_class
from CimTest.Globals import logger
from CimTest.ReturnCodes import FAIL, PASS
from XenKvmLib.const import default_network_name, do_main 
from XenKvmLib.common_util import create_netpool_conf, destroy_netpool
from XenKvmLib.classes import get_typed_class
from XenKvmLib.enumclass import GetInstance, EnumNames

sup_types = ['Xen', 'KVM', 'XenFV']
default_dom = 'net_domain1'
test_dom = 'brgtest_domain2'
nmac = '99:aa:bb:cc:ee:ff'
ntype = 'network'
npool_name = default_network_name + str(randint(1, 100)) 
exp_rc = CIM_ERR_FAILED 
exp_desc = "Conflicting MAC Addresses"


def cleanup_env(ip, virt, npool_name, cxml):
    cxml.cim_destroy(ip)
    cxml.undefine(ip)
    destroy_netpool(ip, virt, npool_name)

def start_dom(cxml,ip,dom):
    ret = cxml.cim_define(ip)
    if not ret:
        status = cxml.verify_error_msg(exp_rc, exp_desc)
        if status != PASS:
            raise Exception("Got unexpected rc code %s and description %s"
                            % (cxml.err_rc, cxml.err_desc))
        return FAIL
    ret = cxml.cim_start(ip)
    if ret:
        status = cxml.verify_error_msg(exp_rc, exp_desc)
        cxml.undefine(ip)
        if status != PASS:
            raise Exception("Got unexpected rc code %s and description %s"
                            % (cxml.err_rc, cxml.err_desc))
        return FAIL
    return PASS

@do_main(sup_types)
def main():
    options = main.options

    status, net_name = create_netpool_conf(options.ip, options.virt,
                                           use_existing=False,
                                           net_name=npool_name)
    if status != PASS:
        logger.error('Unable to create network pool')
        return FAIL
    cxml = get_class(options.virt)(default_dom, mac=nmac,
                                   ntype=ntype, net_name=npool_name)
    try:
        status = start_dom(cxml, options.ip, default_dom)
        if status == FAIL:
            raise Exception("Starting %s domain failed, got unexpeceted rc"
                            "code %s and description %s" % (default_dom,
                            cxml.err_rc, cxml.err_desc))

    except Exception, details:
        logger.error(details)
        destroy_netpool(options.ip, options.virt, net_name)
        return FAIL

    sxml = get_class(options.virt)(test_dom, mac=nmac,
                                   ntype=ntype, net_name=npool_name)
    try:
        status = start_dom(sxml, options.ip, test_dom)

        if status == PASS:
            sxml.cim_destroy(options.ip)
            sxml.undefine(options.ip)
            raise Exception("Was able to create two domains with"
                            "Conflicting MAC Addresses")

        service = get_vsms_class(options.virt)(options.ip)
        classname = get_typed_class(options.virt, 'VirtualSystemSettingData')
        netpool = EnumNames(options.ip, classname)
        inst_id = '%s:%s' % (options.virt, default_dom) 
        vssd_ref = None
        for i in range(0, len(netpool)):
            ret_pool = netpool[i].keybindings['InstanceID']
            if ret_pool == inst_id:
                vssd_ref = netpool[i]
                break
        if vssd_ref == None:
            raise Exception("Failed to get vssd_ref for '%s'"% default_dom)

        nasd = get_nasd_class(options.virt)(type=ntype, mac=nmac,
                                            name=default_dom,
                                            virt_net=npool_name)
        net_attr = { 'ntype'    : ntype,
                     'net_name' : npool_name,
                     'nmac'     : nmac
                   }

        ret = add_net_res(options.ip, service, options.virt, cxml,
                          vssd_ref, nasd, net_attr)
        if ret == PASS:
            raise Exception("AddRS should NOT return OK with duplicate MAC")
        else:
            status = PASS

    except Exception, details:
        logger.error(details)
        status = FAIL
    
    cleanup_env(options.ip, options.virt, npool_name, cxml)
    return status

if __name__ == "__main__":
    exit(main())
    
