#!/usr/bin/python
#
# Copyright 2011 IBM Corp.
#
# Authors:
#    Sharad Mishra<snmishra@us.ibm.com> 
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
#                                                   -Date: 04.14.2011

import sys
import os
from pywbem import cim_types
from CimTest.Globals import logger
from XenKvmLib.xm_virt_util import virsh_version
from CimTest.ReturnCodes import FAIL, PASS, SKIP
from XenKvmLib.const import do_main, platform_sup
from XenKvmLib.classes import get_typed_class
from XenKvmLib.common_util import destroy_diskpool
from XenKvmLib.pool import create_pool, verify_pool, undefine_diskpool
from XenKvmLib.const import get_provider_version
from VirtLib import utils

disk_pool_autostart_support=1087
    
def verify_autostart(server, key):
    cmd = "virsh pool-info %s 2>/dev/null" % key
    s, disk_xml = utils.run_remote(server, cmd)
    if s != 0:
        logger.error("Encountered error running command : %s", cmd)
        return FAIL

    disk = disk_xml.translate(None, ' ')
    val = disk.find("Autostart:yes")
    if val == -1:
        logger.error("Pool is NOT set to Autostart");
        return FAIL

    return PASS

    
@do_main(platform_sup)
def main():
    options = main.options
    server = options.ip
    virt = options.virt

    dp_types =  { }

    libvirt_version = virsh_version(server, virt)
    if libvirt_version < "0.4.1":
        logger.info("Storage pool creation support is available in Libvirt "
                    "version >= 0.4.1 , hence skipping the test....")
        return SKIP
    
    curr_cim_rev, changeset = get_provider_version(virt, server)
    if curr_cim_rev < disk_pool_autostart_support:
        logger.info("DiskPool Autostart support available in libvirt-cim"
                    " version >= %s, hence skipping this test...",
                    disk_pool_autostart_support)
        return SKIP
    
    status = FAIL     
    pool_attr = None
    key = 'DISK_POOL_DIR'
    value = 1
    del_path = False
    try:
        logger.info("Verifying '%s'.....", key)
        test_pool = key
        pool_attr = { "Path" : "/var/lib/libvirt/images/autotest",
                      "Autostart" : cim_types.Uint16(1) }

        if not os.path.exists(pool_attr["Path"]):
                os.mkdir(pool_attr["Path"])
                del_path = True

        status = create_pool(server, virt, test_pool, pool_attr, 
                             mode_type=value, pool_type= "DiskPool")

        if status != PASS:
            raise Exception("Failed to create '%s' type diskpool '%s'" \
                             % (key, test_pool))

        status = verify_autostart(server, key)
        if status != PASS:
            destroy_diskpool(server, virt, test_pool)
            undefine_diskpool(server, virt, test_pool)
            raise Exception("Error in diskpool verification")

        status = destroy_diskpool(server, virt, test_pool)
        if status != PASS:
            raise Exception("Unable to destroy diskpool '%s'" \
                            % test_pool)

        status = undefine_diskpool(server, virt, test_pool)
        if status != PASS:
            raise Exception("Unable to undefine diskpool '%s'" \
                           % test_pool)

        status = PASS

    except Exception, details:
        status = FAIL
        logger.error("Exception details: %s", details)
 
    if del_path:
        os.rmdir(pool_attr["Path"])

    return status

if __name__ == "__main__":
    sys.exit(main())
