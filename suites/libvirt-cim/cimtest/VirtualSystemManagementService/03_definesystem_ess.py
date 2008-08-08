#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Guolian Yun <yunguol@cn.ibm.com>
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
import pywbem
from VirtLib import utils
from XenKvmLib import vsms
from XenKvmLib.test_doms import undefine_test_domain
from XenKvmLib.common_util import create_using_definesystem
from CimTest.Globals import logger
from CimTest.Globals import do_main
from CimTest.ReturnCodes import PASS, FAIL

sup_types = ['Xen', 'KVM', 'XenFV', 'LXC']
exp_rc = 1 #CMPI_RC_ERR_FAILED
exp_desc = 'Unable to parse embedded object'

@do_main(sup_types)
def main():
    options = main.options

    dname = 'test_domain'

    vssd, rasd = vsms.default_vssd_rasd_str(dom_name=dname, virt=options.virt)

    params = {'vssd' : 'wrong',
              'rasd' : rasd
             }

    exp_err = {'exp_rc' : exp_rc,
               'exp_desc' : exp_desc
              }

    rc = create_using_definesystem(dname, options.ip, params, ref_config=' ',
                                   exp_err=exp_err, virt=options.virt)

    if rc != PASS:
        logger.error('DefineSystem should NOT return OK with a wrong ss input')

    undefine_test_domain(dname, options.ip, virt=options.virt)

    return rc 

if __name__ == "__main__":
    sys.exit(main())
    
