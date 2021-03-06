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
# The testcase verifies if the expected error messages are received when
# invalid params are used to define a bridge or a network interface.
# If a network is defined with a None, the 'default' network pool is used
# so no exception is raised for tht condition in the test.
#

import sys
import random
from pywbem import CIM_ERR_FAILED
from XenKvmLib import vxml
from CimTest.Globals import logger
from CimTest.ReturnCodes import FAIL, PASS
from XenKvmLib.const import default_network_name, do_main, get_provider_version
from XenKvmLib.common_util import create_netpool_conf, destroy_netpool
from XenKvmLib.xm_virt_util import virsh_version, virsh_version_cmp

sup_types = ['Xen', 'KVM', 'XenFV']
default_dom = 'brgtest_domain'
nmac = '88:aa:bb:cc:ee:ff'
npool_name = default_network_name + str(random.randint(1, 100)) 
brg_name = "br" + str(random.randint(1, 100)) 

bridge_support_rev = 900

exp_rc = CIM_ERR_FAILED

def verify_error(exp_rc, exp_desc,cxml):
    status = cxml.verify_error_msg(exp_rc, exp_desc)
    return status

@do_main(sup_types)
def main():
    options = main.options

    nettypes = ['network']

    rev, changeset = get_provider_version(options.virt, options.ip)
    if rev >= bridge_support_rev: 
        nettypes.append('bridge')

    expected_values = {
       "invalid" : {'bridge'  : 'internal error Failed to add tap interface',
                    'network' : "internal error Network 'invalid'" },
       "empty"   : {'bridge'  : 'Bridge name is empty',
                    'network' : "internal error Network '' not found"},
       "none"    : {'bridge'  : 'No Network bridge name specified',
                    'network' : "Valid param "}
                      }

    libvirt_version = virsh_version(options.ip, options.virt)
    inv_empty_network = "Network not found"
    if options.virt == "Xen" or options.virt == "XenFV":
        if virsh_version_cmp(libvirt_version, "0.3.3") <= 0:
            inv_empty_network = "no network with matching name"

            inv_br_str = "POST operation failed: (xend.err 'Device 0 (vif) " + \
                         "could not be connected. Could not find bridge " + \
                         "device invalid')"

        else:
             
            inv_br_str = "POST operation failed: xend_post: error from xen " + \
                         "daemon: (xend.err 'Device 0 (vif) could not be " + \
                         "connected. Could not find bridge device invalid')"

        expected_values['invalid']['network'] = inv_empty_network 
        expected_values['empty']['network'] = inv_empty_network 

        expected_values['invalid']['bridge'] = inv_br_str
    else:
        if virsh_version_cmp(libvirt_version, "0.7.0") >= 0:
            expected_values['empty']['network'] = inv_empty_network
            expected_values['invalid']['network'] = inv_empty_network
            if virsh_version_cmp(libvirt_version, "0.9.8") >= 0:
                expected_values['invalid']['bridge'] = "Cannot get interface "\
                                                       "MTU on 'invalid'"
            else:
                expected_values['invalid']['bridge'] = " Failed to add tap "\
                                                       "interface to bridge"


    tc_scen = {
                'invalid' : 'invalid',
                'empty'   : '',
                'none'    : None
              }


    status, net_name = create_netpool_conf(options.ip, options.virt,
                                           use_existing=False,
                                           net_name=npool_name,
                                           bridge_name=brg_name)
    if status != PASS:
        logger.error('Unable to create network pool')
        return FAIL

    status = PASS
    for nettype in nettypes:
        for  tc, field in tc_scen.iteritems():
            logger.error("DEBUG nettype is %s, field is %s, tc is %s",
                         nettype, field, tc)
            cxml = vxml.get_class(options.virt)(default_dom, mac=nmac,
                                                ntype=nettype,
                                                net_name=field)
            exp_desc = expected_values[tc][nettype]
            try:
                ret = cxml.cim_define(options.ip)

                if not ret:
                    status = verify_error(exp_rc, exp_desc, cxml)
                    if status != PASS:
                        # There are few libvirt version between 0.7.0
                        # and 0.8.7 which give following error.
                        status = verify_error(exp_rc, 
                                            'No Network bridge name specified', 
                                            cxml)
                        if status != PASS:
                            raise Exception('Defining domain with invalid %s' 
                                            ' name %s gave unexpected rc code'
                                            ' %s and description:\n'
                                            ' %s'% (nettype, field,
                                            cxml.err_rc, cxml.err_desc))
                    continue
                ret = cxml.cim_start(options.ip)
                if ret:
                    status = verify_error(exp_rc, exp_desc, cxml)
                    cxml.undefine(options.ip) 
                    if status != PASS:
                        raise Exception('Starting domain with invalid %s name'
                                        ' %s gave unexpected rc code %s and '
                                        'description:\n %s'% (nettype, field,
                                        cxml.err_rc, cxml.err_desc))
                    continue

                cxml.cim_destroy(options.ip)
                cxml.undefine(options.ip) 
                if nettype != 'network' and field != None: 
                    raise  Exception('Was able to define a domain with invalid'
                                     ' %s name %s' % (nettype, field))

            except Exception,details:
                logger.error(details)
                destroy_netpool(options.ip, options.virt, net_name)
                return FAIL

    destroy_netpool(options.ip, options.virt, net_name)

    return status

if __name__ == "__main__":
    sys.exit(main())
    
