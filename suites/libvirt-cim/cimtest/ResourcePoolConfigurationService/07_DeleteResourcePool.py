#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Deepti B. Kalakeri<dkalaker@in.ibm.com> 
#    
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
# This test case should test the  DeleteResourcePool service 
# supplied by the RPCS provider. 
# The DeleteResourcePool is used to delete a resource pool. 
# DeleteResourcePool() details:
# Input 
# -----
# IN -- Pool -- CIM_ResourcePool REF -- The resource pool to delete 
# 
# Output
# ------
# OUT -- Job -- CIM_ConcreteJob REF -- Returned job if started
# OUT -- Error-- String -- Encoded error instance if the operation 
#                          failed and did not return a job.
# REVISIT : 
# --------
# As of now the DeleteResourcePool() simply throws an Exception.
# We must improve this tc once the service is implemented. 
# 
#                                                  -Date: 20.02.2008


import sys
import pywbem 
from XenKvmLib import rpcs_service
from CimTest.Globals import logger
from CimTest.ReturnCodes import FAIL, PASS
from CimTest.Globals import do_main, platform_sup
from XenKvmLib.classes import get_typed_class

cim_errno  = pywbem.CIM_ERR_NOT_SUPPORTED
cim_desc   = "The requested operation is not supported"
cim_mname  = "DeleteResourcePool"

@do_main(platform_sup)
def main():
    options = main.options
    rpcs_conn = eval("rpcs_service." + get_typed_class(options.virt, \
                      "ResourcePoolConfigurationService"))(options.ip)
    try:
        rpcs_conn.DeleteResourcePool()
    except pywbem.CIMError, (err_no, desc):
        if err_no == cim_errno and desc.find(cim_desc) >= 0 :
            logger.info("Got expected exception for '%s' service", cim_mname)
            logger.info("Errno is '%s' ", err_no)
            logger.info("Error string is '%s'", desc)
            return PASS
        else:
            logger.error("Unexpected rc code %s and description %s\n" \
                                                       %(err_no, desc))
            return FAIL
     
    logger.error("The execution should not have reached here!!")
    return FAIL
if __name__ == "__main__":
    sys.exit(main())
    
