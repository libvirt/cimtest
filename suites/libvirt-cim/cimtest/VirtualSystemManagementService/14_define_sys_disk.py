#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Kaitlin Rupert <karupert@us.ibm.com>
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
import os 
from VirtLib.utils import run_remote
from CimTest.Globals import logger
from CimTest.ReturnCodes import FAIL, PASS
from XenKvmLib.const import do_main, _image_dir
from XenKvmLib.common_util import create_using_definesystem
from XenKvmLib.test_doms import destroy_and_undefine_domain
from XenKvmLib.classes import get_typed_class, inst_to_mof
from XenKvmLib.rasd import get_default_rasds
from XenKvmLib.vsms import get_vssd_mof

sup_types = ['Xen', 'XenFV', 'KVM', 'LXC']
test_dom = 'rstest_disk_domain'

def make_long_disk_path(ip):
    path = os.path.join(_image_dir, 'cimtest_large_image')

    cmd = "dd if=/dev/zero of=%s bs=1M count=1 seek=8192" % path

    rc, out = run_remote(ip, cmd)
    if rc != 0:
        logger.error("Unable to create large disk image")
        logger.error(out)
        return None

    return path

def get_vssd_rasd(ip, virt, addr):
    vssd = get_vssd_mof(virt, test_dom)

    rasds = get_default_rasds(ip, virt)

    for i in range(0, len(rasds)):
        if rasds[i]['PoolID'].find('DiskPool') >= 0:
            rasds[i]['Address'] = addr
        rasds[i] = inst_to_mof(rasds[i])

    params = { 'vssd' : vssd,
               'rasd' : rasds
             }

    return params 

@do_main(sup_types)
def main():
    options = main.options

    try:
        addr = make_long_disk_path(options.ip)
        if addr is None:
            raise Exception("Unable to create large disk image")

        define_params = get_vssd_rasd(options.ip, options.virt, addr)
        if len(define_params) != 2:
            raise Exception("Unable to get VSSD and RASDs for %s" %  test_dom)

        status = create_using_definesystem(test_dom, options.ip, 
                                           params=define_params, ref_config="",
                                           virt=options.virt)
        if status != PASS:
            raise Exception("Unable to define %s" % test_dom)

    except Exception, details:
        logger.error(details)
        status = FAIL

    if os.path.exists(addr):
        os.remove(addr)

    destroy_and_undefine_domain(test_dom, options.ip, options.virt)

    return status 

if __name__ == "__main__":
    sys.exit(main())
    
