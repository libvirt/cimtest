#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Author:
#   Anoop V Chakkalakkal
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
# This tc is used to verify if appropriate exceptions are
# returned by ResourcePool providers on giving invalid inputs.
#
# Input:
# ------
# wbemcli gi 'http://localhost:5988/root/virt:KVM_DiskPool.InstanceID="Wrong"'
#
# Output:
# -------
# error code  : CIM_ERR_NOT_FOUND
# error desc  : "No such instance (Invalid_Keyvalue)"
#

import sys
from pywbem import CIM_ERR_NOT_FOUND, CIMError
from pywbem.cim_obj import CIMInstanceName
from CimTest.ReturnCodes import PASS, FAIL, SKIP
from CimTest.Globals import logger
from XenKvmLib.classes import get_typed_class
from XenKvmLib.const import do_main
from XenKvmLib.enumclass import GetInstance, CIM_CimtestClass
from XenKvmLib.pool import enum_pools

sup_types = ['Xen', 'KVM', 'XenFV', 'LXC']

def init_pool_list(virt, ip):
    pool_insts = {}

    pools, status = enum_pools(virt, ip)
    if status != PASS:
        return pool_insts, status

    for pool_cn, pool_list in pools.iteritems():
        if len(pool_list) < 1:
             logger.error("Got %d %s, exp at least 1", len(pool_list), pool_cn)
             return pool_insts, FAIL

    return pool_insts, PASS

@do_main(sup_types)
def main():
    options = main.options

    expr_values = {
                    'rc'   : CIM_ERR_NOT_FOUND,
                    'desc' : 'No such instance (Invalid_Keyvalue)'
                  }

    pools, status = init_pool_list(options.virt, options.ip)
    if status != PASS:
        logger.error("Unable to build pool instance list")
        return status
   
    keys = { 'InstanceID' : 'INVALID_Instid_KeyValue' }

    for cn, pool_list in pools.iteritems():
        status = FAIL

        ref = CIMInstanceName(cn, keybindings=keys)

        try:
            inst = CIM_CimtestClass(options.ip, ref)

        except CIMError, (err_no, err_desc):
            exp_rc    = expr_values['rc']
            exp_desc  = expr_values['desc']

            if err_no == exp_rc and err_desc.find(exp_desc) >= 0:
                logger.info("Got expected exception: %s %s", exp_desc, exp_rc)
                status = PASS
            else:
                logger.error("Unexpected errno %s, desc %s", err_no, err_desc)
                logger.error("Expected %s %s", exp_desc, exp_rc)

        if status != PASS:
            logger.error("------ FAILED: %s %s ------", cn, tc)
            break

    return status 

if __name__ == "__main__":
    sys.exit(main())
