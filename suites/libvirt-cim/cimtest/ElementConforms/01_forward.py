#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Kaitlin Rupert <karupert@us.ibm.com>
#    Veerendra Chandrappa <vechandr@in.ibm.com>
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

# This tc is used to verify the EnabledState, HealthState, EnabledDefault and
# the Classname are set appropriately for the results returned by the 
# Xen_ElementConformsToProfile association for the Xen_RegisteredProfile class
# and Xen_ManagedElement Class
# 
#   "CIM:DSP1042-SystemVirtualization-1.0.0" ,
#   "CIM:DSP1057-VirtualSystem-1.0.0a"
#
# Date : 04-12-2007

import sys
from VirtLib import utils, live
from XenKvmLib import assoc
from XenKvmLib.test_doms import destroy_and_undefine_all
from CimTest.Globals import log_param, logger, CIM_ERROR_ASSOCIATORS, do_main
from CimTest import Globals 
from CimTest.ReturnCodes import PASS, FAIL

sup_types = ['Xen']

def verify_cs(item, id):
    if item['EnabledState'] != 2 and  \
       item['EnabledDefault']  != 2 and  \
       item['RequestedState']  != 12     :
        logger.error("Values not set properly for VSP(ComputerSystem)")
        return FAIL

    else:
        logger.info("1. Property values for %s and domain %s is "  %  
                    (id, item['Name']))
        logger.info("EnabState = %d EnabDefault = %d ReqSt = %d" % 
                    (item['EnabledState'], item['EnabledDefault'], 
                    item['RequestedState'] ))

    return PASS 

def verify_host(item, id):
    if item['EnabledState'] != 5 and \
       item['EnabledDefault']  != 2 and \
       item['RequestedState']  != 12    :
        logger.error("Values not set properly for the the SVP (HostSystem)")
        return FAIL

    else:
        logger.info("2. Values for %s and host %s is" %
                    (id, item['Name']))
        logger.info("EnabState = %d EnabDefault = %d ReqSt = %d" %
                     (item['EnabledState'], item['EnabledDefault'], 
                     item['RequestedState'] ))

    return PASS 

@do_main(sup_types)
def main():
    options = main.options

    log_param()
    status = PASS
    destroy_and_undefine_all(options.ip)

    prev_namespace = Globals.CIM_NS
    Globals.CIM_NS = 'root/interop'
    host = live.hostname(options.ip)

    inst_lst = {
              "InstID1"  : "CIM:DSP1042-SystemVirtualization-1.0.0" ,
              "InstID2"  : "CIM:DSP1057-VirtualSystem-1.0.0a"
             }
    devlist = [  
              "Xen_HostSystem" , \
              "Xen_ComputerSystem"
             ]

    for args, devid in inst_lst.items() :
        try:
            assoc_info = assoc.Associators(options.ip, \
                                               "Xen_ElementConformsToProfile",
                                               "Xen_RegisteredProfile",
                                               InstanceID = devid)  
            if len(assoc_info) < 1:
                status = FAIL
                logger.error("Xen_ElementConformsToProfile returned %i\
 Xen_RegisteredProfile objects" % len(assoc_info))
                break

            count = 0
            for info in assoc_info:
                if info['CreationClassName'] == "Xen_ComputerSystem" :

                    if info['Name'] == 'Domain-0' :
                        count = count + 1
                        verify_cs(info, devid)

                elif info['CreationClassName'] == "Xen_HostSystem" and \
                     info['Name'] == host:
                        count = count + 1
                        verify_host(info, devid)

                else:
                    status = FAIL
                    logger.error("CreationClassName Mismatch")
                    logger.error("Returned %s instead of %s or %s" % \
                           (item['CreationClassName'],  devlist[0], devlist[1]))

            exp_count = 1
            if count != exp_count:
                status = FAIL
                logger.error("Expected to verify %d instances, not %d." % 
                             exp_count, count)


        except BaseException, detail:
            logger.error(CIM_ERROR_ASSOCIATORS, 'Xen_ElementConformsToProfile')
            logger.error("Exception: %s" % detail)
            status = FAIL

    Globals.CIM_NS = prev_namespace
    return status

if __name__ == "__main__":
    sys.exit(main())

