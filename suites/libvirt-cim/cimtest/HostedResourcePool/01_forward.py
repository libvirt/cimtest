#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Dan Smith <danms@us.ibm.com>
#    Guolian Yun <yunguol@cn.ibm.com>
#    Zhengang Li <lizg@cn.ibm.com>
#    Deepti B. Kalakeri <dkalaker@in.ibm.com>
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
from sets import Set
from XenKvmLib import assoc
from XenKvmLib import enumclass
from XenKvmLib.common_util import get_host_info
from XenKvmLib.const import default_network_name, get_provider_version
from CimTest import Globals
from CimTest.Globals import logger
from CimTest.ReturnCodes import PASS, FAIL
from XenKvmLib.const import do_main, default_pool_name
from XenKvmLib.classes import get_typed_class

input_graphics_pool_rev = 757
sup_types = ['Xen', 'KVM', 'XenFV', 'LXC']
@do_main(sup_types)
def main():
    options = main.options
    virt = options.virt
    keys = ['Name', 'CreationClassName']
    status, host_inst = get_host_info(options.ip, virt)
    if status != PASS:
        logger.error("Error in calling get_host_info function")
        return FAIL

    host_cn = host_inst.CreationClassName
    host_sys = host_inst.Name

    try:
        assoc_cn = get_typed_class(virt, "HostedResourcePool")
        pool = assoc.AssociatorNames(options.ip,
                                     assoc_cn,
                                     host_cn,
                                     Name = host_sys,
                                     CreationClassName = host_cn)
    except Exception, details:
        logger.error(Globals.CIM_ERROR_ASSOCIATORNAMES, assoc_cn)
        logger.error("Exception:",  details)
        return FAIL
   
    if pool == None:
        logger.error("System association failed")
        return FAIL
    elif len(pool) == 0:
        logger.error("No pool returned")
        return FAIL

    mpool =  get_typed_class(virt, 'MemoryPool')
    exp_pllist = { mpool   : ['MemoryPool/0'] }
    if virt != 'LXC':
        npool =  get_typed_class(virt, 'NetworkPool')
        dpool =  get_typed_class(virt, 'DiskPool')
        ppool =  get_typed_class(virt, 'ProcessorPool')
        exp_pllist[dpool] = ['DiskPool/%s' % default_pool_name]
        exp_pllist[npool] = ['NetworkPool/%s' %default_network_name]
        exp_pllist[ppool] = ['ProcessorPool/0']

        curr_cim_rev, changeset = get_provider_version(virt, options.ip)
        if curr_cim_rev >= input_graphics_pool_rev:
            ipool = get_typed_class(virt, 'InputPool')
            gpool = get_typed_class(virt, 'GraphicsPool')
            exp_pllist[ipool] = ['InputPool/0']
            exp_pllist[gpool] = ['GraphicsPool/0']
    
    try:
        res_pllist = {}
        for items in pool:
            # The dict has some elements
            if len(res_pllist) != 0:
                # If the dict already has the key we append the new value 
                if items.classname in res_pllist.keys(): 
                    list = []
                    list = res_pllist[items.classname]
                    list.append(items['InstanceID'])
                    res_pllist[items.classname] = list
                else:
                    # If the dict is not empty, but does not yet contain 
                    # items.classname, we create new item
                    res_pllist[items.classname] = [items['InstanceID']]
            else:
                # When the dict is empty
                res_pllist[items.classname] = [items['InstanceID']]

        #Verifying we get all the expected pool class info
        if len(Set(exp_pllist.keys()) - Set(res_pllist.keys())) != 0:
            logger.error("Pool Class mismatch")
            raise Exception("Expected Pool class list: %s \n \t  Got: %s"
                            % (sorted(exp_pllist.keys()), 
                               sorted(res_pllist.keys())))

        #Verifying that we get the atleast the expected instanceid 
        #for every pool class
        for key in exp_pllist.keys():
            if Set(exp_pllist[key]) - Set(res_pllist[key]):
                logger.error("InstanceID mismatch")
                raise Exception("Expected InstanceID: %s \n \t  Got: %s"
                                 % (sorted(exp_pllist[key]), 
                                    sorted(res_pllist[key])))
    except Exception, details:
         logger.error(details)
         return FAIL
        

    return PASS
if __name__ == "__main__":
    sys.exit(main())
