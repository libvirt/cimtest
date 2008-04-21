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
from pywbem.cim_obj import CIMInstanceName
from VirtLib import utils
from XenKvmLib import vsms
from XenKvmLib import vxml
from CimTest.Globals import logger
from CimTest.Globals import do_main
from CimTest.ReturnCodes import PASS, FAIL, XFAIL_RC

sup_types = ['Xen', 'KVM', 'XenFV']
default_dom = 'rstest_domain'
ntype = 'bridge'
ncpu = 3
nmem = 78

bug_cpu = '90079'
bug_net = '90853'

@do_main(sup_types)
def main():
    options = main.options 

    service = vsms.get_vsms_class(options.virt)(options.ip)
    cxml = vxml.get_class(options.virt)(default_dom)
    ndpath = cxml.secondary_disk_path
    dasd = vsms.get_dasd_class(options.virt)(dev=cxml.xml_get_disk_dev(),
                                             source=ndpath, 
                                             name=default_dom)
    nasd = vsms.get_nasd_class(options.virt)(type=ntype, 
                                             mac=cxml.xml_get_net_mac(),
                                             name=default_dom)
    masd = vsms.get_masd_class(options.virt)(megabytes=nmem, name=default_dom)
    pasd = vsms.get_pasd_class(options.virt)(vcpu=ncpu, name=default_dom)

    status = FAIL
    rc = 0
    try:
        cxml.define(options.ip)
        # Modify disk setting
        service.ModifyResourceSettings(ResourceSettings = [str(dasd)])
        cxml.dumpxml(options.ip)
        dpath = cxml.xml_get_disk_source()
        if dpath != ndpath:
            raise Exception('Error changing rs for disk path')
        logger.info('good status for disk path')
        # Modify net setting
        service.ModifyResourceSettings(ResourceSettings = [str(nasd)])
        cxml.dumpxml(options.ip)
        type = cxml.xml_get_net_type()
        if type != ntype:
            raise Exception('Error changing rs for net mac')
        logger.info('good status for net mac')
        # Modify memory resource setting
        service.ModifyResourceSettings(ResourceSettings=[str(masd)])
        cxml.dumpxml(options.ip)
        mem = cxml.xml_get_mem()
        if mem != '%i' % (nmem * 1024):
            raise Exception('Error changing rs for mem')
        logger.info('good status for mem')
        # Modify cpu setting
        service.ModifyResourceSettings(ResourceSettings = [str(pasd)])
        cxml.dumpxml(options.ip)
        cpu = cxml.xml_get_vcpu()
        if cpu != '%i' % ncpu:
            rc = -1
            raise Exception('Error changing rs for vcpu')
        logger.info('good status for vcpu')
        status = PASS
    except Exception, details:
        logger.error('Error invoking ModifyRS')
        logger.error(details)
        return XFAIL_RC(bug_net)

    cxml.undefine(options.ip)
    if rc == -1:
        return XFAIL_RC(bug_cpu)

    return status

if __name__ == "__main__":
    sys.exit(main())
 
